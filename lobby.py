# lobby.py

import hashlib
import json
import os
try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None

import pygame

import accessible_output as accessibility
from settings import *


class Lobby:
    def __init__(self, game):
        # Prevent Enter from menu triggering an instant lobby action.
        pygame.event.clear()

        self.game = game
        self.screen = game.screen
        self.players = []
        self.is_host = self.game.player_id == 0
        self.active_host_id = self.game.player_id
        self.last_host_handoff_notice = ""
        self.lobby_name = "Lobby"

        self.studio_graph = {
            "Entrance": {"right": "Audience Riser"},
            "Audience Riser": {
                "left": "Entrance",
                "right": "Contestant Area",
                "up": "Camera Walkway",
            },
            "Contestant Area": {
                "left": "Audience Riser",
                "right": "Hot Seat",
                "down": "Sound Booth",
            },
            "Hot Seat": {
                "left": "Contestant Area",
                "right": "Host Control Panel",
                "up": "Camera Walkway",
            },
            "Host Control Panel": {
                "left": "Hot Seat",
                "down": "Sound Booth",
            },
            "Camera Walkway": {
                "down": "Audience Riser",
                "right": "Hot Seat",
            },
            "Sound Booth": {
                "up": "Contestant Area",
                "right": "Host Control Panel",
            },
        }
        self.studio_landmarks = {
            "Entrance": "main doors and floor lights",
            "Audience Riser": "audience seating and applause wall",
            "Contestant Area": "contestant podium row",
            "Hot Seat": "single hot seat spotlight",
            "Host Control Panel": "master console with cue buttons",
            "Camera Walkway": "overhead camera rail and crane",
            "Sound Booth": "audio desk and monitor speakers",
        }
        self.studio_zones = list(self.studio_graph.keys())
        self.current_zone = "Entrance"

        self.seat_zones = {"Contestant Area", "Hot Seat", "Host Control Panel"}
        self.seat_labels = {
            "Contestant Area": "contestant seat",
            "Hot Seat": "hot seat",
            "Host Control Panel": "host chair",
        }
        self.is_seated = False

        self.host_panel_open = False
        self.host_panel_page = 0
        self.host_panel_index = 0

        self.light_presets = ["Studio Blue", "Warm Spotlight", "Fastest Finger"]
        self.light_index = 0
        self.music_presets = ["Lobby Theme", "Question Bed", "Silence"]
        self.music_index = 0

        self.host_show_items = [
            "Lights",
            "Music Bed",
            "Play Sting",
            "Refresh Session Assets",
            "Sync Status",
            "Go To Flow Page",
            "Start Game",
            "Close Panel",
        ]
        self.host_flow_items = [
            "Call-Up Target",
            "Call Next Contestant",
            "Move Target To Hot Seat",
            "Quick Switch Preset",
            "Setup Preset",
            "Apply Setup Preset",
            "Save Current As Preset",
            "Import Preset Pack",
            "Delete Selected Preset",
            "Back To Show Controls",
            "Close Panel",
        ]

        self.builtin_setup_preset_states = {
            "Classic Live": {
                "lights": "Studio Blue",
                "music": "Lobby Theme",
                "zone": "Host Control Panel",
                "seated": False,
                "call_up_mode": "reset",
            },
            "Fast Practice": {
                "lights": "Warm Spotlight",
                "music": "Silence",
                "zone": "Host Control Panel",
                "seated": False,
                "call_up_mode": "keep",
            },
            "FFF Warmup": {
                "lights": "Fastest Finger",
                "music": "Question Bed",
                "zone": "Contestant Area",
                "seated": True,
                "call_up_mode": "reset",
            },
        }
        self.custom_setup_presets = self._load_custom_setup_presets()
        self.file_setup_presets = self._load_setup_preset_packs()
        self.setup_presets = []
        self.setup_preset_states = {}
        self.setup_preset_meta = {}
        self._rebuild_setup_presets()
        self.setup_index = 0
        self.call_up_index = 0

        self.asset_sync_ready = self.is_host
        self.synced_asset_revision = 0 if self.is_host else -1
        self.next_asset_sync_retry_at = 0
        self.last_start_block_reason = ""
        self.last_sync_skipped_count = 0
        self.last_sync_manifest_count = 0
        self.last_sync_source = ""
        self.connection_retry_started_at = 0
        self.connection_retry_announced = False

        if self._local_is_host():
            accessibility.speak(
                "Lobby created. Waiting for other players to join. Press Enter to start the game. "
                "Use arrow keys to navigate the set."
            )
        else:
            accessibility.speak(
                "Joined lobby. Waiting for the host to start the game. "
                "Use arrow keys to navigate the set."
            )

        self.game.network.send({"action": "move_zone", "zone": self.current_zone})
        self.game.network.send({"action": "set_seated", "seated": False})

        if self._local_is_host():
            self._host_publish_session_assets()

    def _local_is_host(self):
        return self.game.player_id == self.active_host_id

    def _announce_zone(self):
        self.game.sounds.play_ui_panned("ui_arrive", 0.0, "ui_select")

        landmark = self.studio_landmarks.get(self.current_zone, "set corridor")
        exits = self._get_exit_summary(self.current_zone)
        proximity = self._get_proximity_summary(self.current_zone)

        parts = [
            f"You are at {self.current_zone}.",
            f"Landmark: {landmark}.",
            exits,
        ]
        if proximity:
            parts.append(proximity)

        if self.current_zone in self.seat_zones:
            parts.append("Press S to sit or stand.")

        accessibility.speak(" ".join(parts))

        if self._can_open_host_panel():
            self.game.sounds.play_ui_panned("ui_panel", self._panel_proximity_pan(), "ui_select")
            accessibility.speak("Host control panel. Press Enter or Space to interact with controls.")

    def _get_exit_summary(self, zone):
        neighbors = self.studio_graph.get(zone, {})
        if not neighbors:
            return "No exits available from this location."

        ordered = []
        for key in ("left", "right", "up", "down"):
            if key in neighbors:
                ordered.append(f"{key} to {neighbors[key]}")
        return f"Exits: {', '.join(ordered)}."

    def _shortest_path_directions(self, start_zone, target_zone):
        if start_zone == target_zone:
            return []

        frontier = [(start_zone, [])]
        visited = {start_zone}

        while frontier:
            zone, path = frontier.pop(0)
            for direction, next_zone in self.studio_graph.get(zone, {}).items():
                if next_zone in visited:
                    continue

                next_path = path + [direction]
                if next_zone == target_zone:
                    return next_path

                visited.add(next_zone)
                frontier.append((next_zone, next_path))

        return None

    def _get_proximity_summary(self, zone):
        target_labels = [
            ("Hot Seat", "hot seat"),
            ("Host Control Panel", "control panel"),
            ("Entrance", "entrance"),
        ]

        cues = []
        for target_zone, label in target_labels:
            if target_zone == zone:
                continue

            path = self._shortest_path_directions(zone, target_zone)
            if path is None:
                continue

            steps = len(path)
            lead = path[0]
            if steps == 1:
                cues.append((steps, f"{label} is 1 move {lead}"))
            else:
                cues.append((steps, f"{label} is {steps} moves, starting {lead}"))

        if not cues:
            return ""

        cues.sort(key=lambda item: item[0])
        spoken = "; ".join(text for _, text in cues[:2])
        return f"Proximity: {spoken}."

    def _direction_to_pan(self, direction):
        pan_map = {
            "left": -0.8,
            "right": 0.8,
            "up": 0.0,
            "down": 0.0,
        }
        return pan_map.get(direction, 0.0)

    def _panel_proximity_pan(self):
        path = self._shortest_path_directions(self.current_zone, "Host Control Panel")
        if not path:
            return 0.0
        return self._direction_to_pan(path[0])

    def _move_direction(self, direction):
        neighbors = self.studio_graph.get(self.current_zone, {})
        next_zone = neighbors.get(direction)
        if not next_zone:
            self.game.sounds.play_ui("ui_error")
            accessibility.speak(f"No path {direction} from {self.current_zone}.")
            return

        pan = self._direction_to_pan(direction)

        if self.is_seated:
            self._set_seated(False, announce=True)

        self.game.sounds.play_ui_panned("ui_leave", pan, "ui_step")
        self.game.sounds.play_ui_panned("ui_step", pan, "ui_move")
        self.current_zone = next_zone
        self.game.network.send({"action": "move_zone", "zone": self.current_zone})
        self._announce_zone()

    def _move_tab_forward(self):
        for direction in ("right", "down", "left", "up"):
            if direction in self.studio_graph.get(self.current_zone, {}):
                self._move_direction(direction)
                return

        self.game.sounds.play_ui("ui_error")
        accessibility.speak("No available route from this location.")

    def _set_seated(self, seated, announce=True):
        self.is_seated = seated
        self.game.network.send({"action": "set_seated", "seated": seated})

        seat_name = self.seat_labels.get(self.current_zone, "seat")
        if seated:
            self.game.sounds.play_ui("ui_sit", "ui_select")
            if announce:
                accessibility.speak(f"Sitting in the {seat_name}.")
        else:
            self.game.sounds.play_ui("ui_stand", "ui_leave")
            if announce:
                accessibility.speak(f"Standing from the {seat_name}.")

    def _toggle_seat(self):
        if self.current_zone not in self.seat_zones:
            accessibility.speak("No seat at this location.")
            self.game.sounds.play_ui("ui_error")
            return

        self._set_seated(not self.is_seated)

    def _announce_controls(self):
        accessibility.speak(
            "Lobby controls. Arrow keys move through connected studio areas. "
            "Each arrival announces landmarks, exits, and nearby targets. "
            "S sits or stands when a seat is available. "
            "Enter starts the game if you are host. Escape leaves the lobby."
        )

    def _can_open_host_panel(self):
        return self._local_is_host() and not self.is_seated and self.current_zone == "Host Control Panel"

    def _open_host_panel(self):
        if not self._can_open_host_panel():
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("You must be standing at the host control panel to use these controls.")
            return

        self.host_panel_open = True
        self.host_panel_page = 0
        self.host_panel_index = 0
        self.game.sounds.play_ui("ui_panel", "ui_select")
        self._announce_host_panel_selection()

    def _close_host_panel(self):
        self.host_panel_open = False
        self.game.sounds.play_ui("ui_back")
        accessibility.speak("Closed host control panel.")

    def _announce_host_panel_selection(self):
        item = self._get_current_panel_items()[self.host_panel_index]
        detail = ""
        if item == "Lights":
            detail = self.light_presets[self.light_index]
        elif item == "Music Bed":
            detail = self.music_presets[self.music_index]
        elif item == "Call-Up Target":
            detail = self._get_current_call_target()
        elif item == "Quick Switch Preset":
            detail = self.setup_presets[self.setup_index]
        elif item == "Setup Preset":
            detail = self.setup_presets[self.setup_index]
        elif item == "Delete Selected Preset":
            detail = self.setup_presets[self.setup_index]
        elif item == "Sync Status":
            detail = "Press Enter"

        announcement = item if not detail else f"{item}: {detail}"
        accessibility.speak(announcement)

    def _navigate_host_panel(self, direction):
        items = self._get_current_panel_items()
        self.host_panel_index = (self.host_panel_index + direction) % len(items)
        self.game.sounds.play_ui("ui_move")
        self._announce_host_panel_selection()

    def _get_current_panel_items(self):
        return self.host_show_items if self.host_panel_page == 0 else self.host_flow_items

    def _switch_panel_page(self, page):
        self.host_panel_page = page
        self.host_panel_index = 0
        self.game.sounds.play_ui("ui_move")
        accessibility.speak("Show Controls" if page == 0 else "Flow And Presets")
        self._announce_host_panel_selection()

    def _get_contestant_names(self):
        return [p.name for p in self.players if getattr(p, "id", -1) != 0]

    def _get_current_call_target(self):
        contestants = self._get_contestant_names()
        if not contestants:
            return "No contestants"
        self.call_up_index %= len(contestants)
        return contestants[self.call_up_index]

    def _safe_lobby_slug(self):
        allowed = []
        for c in self.lobby_name:
            if c.isalnum() or c in ("-", "_"):
                allowed.append(c)
            elif c.isspace():
                allowed.append("_")
        slug = "".join(allowed).strip("_")
        return slug if slug else "session"

    def _sha256_file(self, path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                block = f.read(65536)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()

    def _send_with_retry(self, payload):
        for attempt in range(SESSION_SYNC_NETWORK_RETRIES):
            reply = self.game.network.send(payload)
            if reply is not None:
                return reply
            if attempt < SESSION_SYNC_NETWORK_RETRIES - 1:
                pygame.time.wait(SESSION_SYNC_RETRY_BACKOFF_MS * (attempt + 1))
        return None

    def _progress_bucket(self, offset, total):
        if total <= 0:
            return 100
        percent = int((offset * 100) / total)
        step = max(1, int(SESSION_SYNC_PROGRESS_STEP_PERCENT))
        bucket = (percent // step) * step
        return min(100, bucket)

    def _load_custom_setup_presets(self):
        raw = self.game.config.data.get("custom_setup_presets", [])
        if not isinstance(raw, list):
            return []

        custom = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            state = item.get("state")
            if not isinstance(name, str) or not name.strip() or not isinstance(state, dict):
                continue
            custom.append({"name": name.strip(), "state": state})

        return custom

    def _preset_pack_dir(self):
        path = os.path.expandvars(os.path.expanduser(STUDIO_PRESET_PACKS_DIR))
        os.makedirs(path, exist_ok=True)
        return path

    def _safe_preset_filename(self, name):
        cleaned = []
        for ch in name:
            if ch.isalnum() or ch in ("-", "_"):
                cleaned.append(ch)
            elif ch.isspace():
                cleaned.append("_")
        slug = "".join(cleaned).strip("_")
        return slug if slug else "preset"

    def _load_setup_preset_packs(self):
        presets = []
        pack_dir = self._preset_pack_dir()

        try:
            names = sorted(os.listdir(pack_dir))
        except Exception:
            return presets

        for filename in names:
            if not filename.lower().endswith(STUDIO_PRESET_PACK_EXTENSION):
                continue

            full_path = os.path.join(pack_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception:
                continue

            if not isinstance(payload, dict):
                continue

            name = payload.get("name")
            state = payload.get("state")
            if not isinstance(name, str) or not name.strip() or not isinstance(state, dict):
                continue

            presets.append({
                "name": f"Pack: {name.strip()}",
                "state": state,
                "path": full_path,
            })

        return presets

    def _save_setup_preset_pack(self, name, state):
        pack_dir = self._preset_pack_dir()
        slug = self._safe_preset_filename(name)
        path = os.path.join(pack_dir, f"{slug}{STUDIO_PRESET_PACK_EXTENSION}")

        payload = {
            "name": name,
            "state": state,
            "format": 1,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _rebuild_setup_presets(self):
        self.setup_preset_states = {}
        self.setup_presets = []
        self.setup_preset_meta = {}

        for name, state in self.builtin_setup_preset_states.items():
            self.setup_preset_states[name] = state
            self.setup_preset_meta[name] = {"source": "builtin"}
            self.setup_presets.append(name)

        for item in self.file_setup_presets:
            name = item["name"]
            state = item["state"]
            if name in self.setup_presets:
                self.setup_presets.remove(name)
            self.setup_preset_states[name] = state
            self.setup_preset_meta[name] = {
                "source": "pack",
                "path": item.get("path", ""),
            }
            self.setup_presets.append(name)

        for item in self.custom_setup_presets:
            name = item["name"]
            state = item["state"]
            if name in self.setup_presets:
                self.setup_presets.remove(name)
            self.setup_preset_states[name] = state
            self.setup_preset_meta[name] = {"source": "custom"}
            self.setup_presets.append(name)

    def _persist_custom_setup_presets(self):
        self.game.config.data["custom_setup_presets"] = list(self.custom_setup_presets)
        self.game.config.save()

    def _snapshot_current_preset_state(self):
        return {
            "lights": self.light_presets[self.light_index],
            "music": self.music_presets[self.music_index],
            "zone": self.current_zone,
            "seated": bool(self.is_seated),
            "call_up_mode": "set",
            "call_up_index": int(self.call_up_index),
        }

    def _save_current_as_preset(self):
        base_name = "Custom Preset"
        existing = set(self.setup_presets)
        index = 1
        while f"{base_name} {index}" in existing:
            index += 1

        name = f"{base_name} {index}"
        state = self._snapshot_current_preset_state()
        self.custom_setup_presets.append({"name": name, "state": state})

        if len(self.custom_setup_presets) > 30:
            self.custom_setup_presets = self.custom_setup_presets[-30:]

        try:
            self._save_setup_preset_pack(name, state)
        except Exception:
            accessibility.speak("Preset saved in session, but writing preset pack file failed.")

        self.file_setup_presets = self._load_setup_preset_packs()
        self._rebuild_setup_presets()
        self._persist_custom_setup_presets()
        self.setup_index = self.setup_presets.index(name)
        accessibility.speak(f"Saved current studio setup as {name}.")

    def _import_setup_preset_pack(self):
        if tk is None or filedialog is None:
            accessibility.speak("Preset import is unavailable on this system.")
            self.game.sounds.play_ui("ui_error")
            return

        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            selected = filedialog.askopenfilename(
                title="Select Preset Pack",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
        except Exception:
            selected = ""
        finally:
            if root is not None:
                root.destroy()

        if not selected:
            accessibility.speak("Preset pack import cancelled.")
            return

        try:
            with open(selected, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("Preset pack file could not be read.")
            return

        if not isinstance(payload, dict):
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("Preset pack format is invalid.")
            return

        name = payload.get("name")
        state = payload.get("state")
        if not isinstance(name, str) or not name.strip() or not isinstance(state, dict):
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("Preset pack is missing a valid name or state.")
            return

        base_name = self._safe_preset_filename(name)
        pack_dir = self._preset_pack_dir()
        suffix = 0
        while True:
            filename = (
                f"{base_name}{STUDIO_PRESET_PACK_EXTENSION}"
                if suffix == 0
                else f"{base_name}_{suffix}{STUDIO_PRESET_PACK_EXTENSION}"
            )
            out_path = os.path.join(pack_dir, filename)
            if not os.path.exists(out_path):
                break
            suffix += 1

        out_payload = {
            "name": name.strip(),
            "state": state,
            "format": 1,
        }
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out_payload, f, indent=2)
        except Exception:
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("Preset pack import failed while writing the file.")
            return

        imported_name = f"Pack: {name.strip()}"
        self.file_setup_presets = self._load_setup_preset_packs()
        self._rebuild_setup_presets()
        if imported_name in self.setup_presets:
            self.setup_index = self.setup_presets.index(imported_name)
        accessibility.speak(f"Imported preset pack {name.strip()}.")

    def _delete_selected_preset(self):
        preset = self.setup_presets[self.setup_index]
        meta = self.setup_preset_meta.get(preset, {"source": "builtin"})
        source = meta.get("source", "builtin")
        deleted_label = "preset"

        if source == "builtin":
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("Built-in presets cannot be deleted.")
            return

        if source == "pack":
            deleted_label = "imported pack preset"
            path = meta.get("path", "")
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
            except Exception:
                self.game.sounds.play_ui("ui_error")
                accessibility.speak("Preset pack file could not be deleted.")
                return
        elif source == "custom":
            deleted_label = "custom preset"
            self.custom_setup_presets = [p for p in self.custom_setup_presets if p.get("name") != preset]
            self._persist_custom_setup_presets()

            # Custom presets are also exported to preset packs using a slugged filename.
            custom_path = os.path.join(
                self._preset_pack_dir(),
                f"{self._safe_preset_filename(preset)}{STUDIO_PRESET_PACK_EXTENSION}",
            )
            try:
                if os.path.isfile(custom_path):
                    os.remove(custom_path)
            except Exception:
                pass

        self.file_setup_presets = self._load_setup_preset_packs()
        self._rebuild_setup_presets()
        if self.setup_index >= len(self.setup_presets):
            self.setup_index = max(0, len(self.setup_presets) - 1)
        accessibility.speak(f"Deleted {deleted_label} {preset}.")

    def _get_host_asset_source_dir(self):
        configured = self.game.config.data.get("session_assets_dir", SESSION_SYNC_SOURCE_DIR)
        if not isinstance(configured, str):
            configured = SESSION_SYNC_SOURCE_DIR
        source = configured.strip() or SESSION_SYNC_SOURCE_DIR
        source = os.path.expandvars(os.path.expanduser(source))
        return os.path.normpath(source)

    def _collect_session_assets(self):
        source = self._get_host_asset_source_dir()
        manifest = []
        files = {}
        skipped_too_large = []

        if not os.path.isdir(source):
            return source, False, manifest, files, skipped_too_large

        for root, _, names in os.walk(source):
            for name in names:
                ext = os.path.splitext(name)[1].lower()
                if ext not in SESSION_SYNC_ALLOWED_EXTS:
                    continue

                abs_path = os.path.join(root, name)
                rel_path = os.path.relpath(abs_path, source).replace("\\", "/")

                with open(abs_path, "rb") as f:
                    data = f.read()
                if len(data) > SESSION_SYNC_MAX_FILE_SIZE:
                    skipped_too_large.append((rel_path, len(data)))
                    continue
                digest = hashlib.sha256(data).hexdigest()

                files[rel_path] = data
                manifest.append({
                    "name": rel_path,
                    "sha256": digest,
                    "size": len(data),
                })

        manifest.sort(key=lambda x: x["name"])
        return source, True, manifest, files, skipped_too_large

    def _announce_sync_status(self):
        revision = self.synced_asset_revision
        source = self.last_sync_source if self.last_sync_source else self._get_host_asset_source_dir()
        skipped = self.last_sync_skipped_count
        published = self.last_sync_manifest_count

        if self.players:
            states = []
            for p in self.players:
                state = "ready" if getattr(p, "asset_ready", False) else "syncing"
                states.append(f"{p.name} {state}")
            player_state_text = ", ".join(states)
        else:
            player_state_text = "No players connected"

        accessibility.speak(
            f"Sync status. Revision {revision}. Published {published} files. "
            f"Skipped {skipped} oversized files. Source folder {source}. "
            f"Player states: {player_state_text}."
        )

    def _host_publish_session_assets(self):
        source, source_exists, manifest, files, skipped_too_large = self._collect_session_assets()
        self.last_sync_source = source
        self.last_sync_skipped_count = len(skipped_too_large)
        self.last_sync_manifest_count = len(manifest)
        reply = self._send_with_retry({"action": "asset_upload_manifest", "manifest": manifest})
        if not reply or not reply.get("ok"):
            accessibility.speak("Could not publish session assets.")
            return

        revision = int(reply.get("asset_revision", 0))

        if not manifest:
            ready_reply = self._send_with_retry({
                "action": "asset_client_ready",
                "ready": True,
                "revision": revision,
            })
            if not ready_reply or not ready_reply.get("ok"):
                accessibility.speak("Could not confirm host asset sync readiness.")
                return

            self.game.sounds.set_session_asset_root(None)
            self.asset_sync_ready = True
            self.synced_asset_revision = revision
            if source_exists:
                accessibility.speak(f"No custom session assets found in {source}.")
            else:
                accessibility.speak(f"Session asset folder not found: {source}.")
            if skipped_too_large:
                accessibility.speak(
                    f"Skipped {len(skipped_too_large)} files over "
                    f"{SESSION_SYNC_MAX_FILE_SIZE // (1024 * 1024)} megabytes."
                )
            return

        for index, entry in enumerate(manifest):
            name = entry["name"]
            data = files[name]

            accessibility.speak(f"Uploading asset {index + 1} of {len(manifest)}: {name}.")

            begin_reply = self._send_with_retry({
                "action": "asset_upload_begin",
                "name": name,
                "size": len(data),
                "sha256": entry.get("sha256", ""),
            })
            if not begin_reply or not begin_reply.get("ok"):
                if begin_reply and begin_reply.get("error") == "file_too_large":
                    accessibility.speak(
                        f"Server rejected {name} because it exceeds the max size limit."
                    )
                    continue
                accessibility.speak(f"Failed to start upload for {name}.")
                return

            offset = int(begin_reply.get("offset", 0))
            if offset < 0 or offset > len(data):
                accessibility.speak(f"Upload offset error for {name}.")
                return

            last_bucket = -1
            bucket = self._progress_bucket(offset, len(data))
            if bucket > last_bucket:
                last_bucket = bucket
                accessibility.speak(f"{name} upload {bucket} percent.")

            while offset < len(data):
                chunk = data[offset:offset + SESSION_SYNC_CHUNK_SIZE]
                upload_reply = self._send_with_retry({
                    "action": "asset_upload_chunk",
                    "name": name,
                    "offset": offset,
                    "data": chunk,
                })
                if not upload_reply:
                    accessibility.speak(f"Upload interrupted for {name}.")
                    return
                if not upload_reply.get("ok"):
                    if upload_reply.get("error") == "offset_mismatch":
                        expected = int(upload_reply.get("expected_offset", offset))
                        if expected < 0 or expected > len(data):
                            accessibility.speak(f"Upload offset mismatch for {name}.")
                            return
                        offset = expected
                        continue
                    accessibility.speak(f"Failed to upload session asset {name}.")
                    return

                next_offset = int(upload_reply.get("next_offset", offset + len(chunk)))
                if next_offset <= offset:
                    accessibility.speak(f"Upload stalled for {name}.")
                    return
                offset = next_offset

                bucket = self._progress_bucket(offset, len(data))
                if bucket > last_bucket:
                    last_bucket = bucket
                    accessibility.speak(f"{name} upload {bucket} percent.")

        ready_reply = self._send_with_retry({
            "action": "asset_client_ready",
            "ready": True,
            "revision": revision,
        })
        if not ready_reply or not ready_reply.get("ok"):
            accessibility.speak("Could not confirm host asset sync readiness.")
            return

        self.game.sounds.set_session_asset_root(source)
        self.asset_sync_ready = True
        self.synced_asset_revision = revision
        if skipped_too_large:
            accessibility.speak(
                f"Skipped {len(skipped_too_large)} files over "
                f"{SESSION_SYNC_MAX_FILE_SIZE // (1024 * 1024)} megabytes."
            )
        accessibility.speak(f"Published {len(manifest)} session assets from {source}.")

    def _attempt_client_asset_sync(self, expected_revision=None):
        manifest_reply = self._send_with_retry({"action": "asset_get_manifest"})
        if not manifest_reply or manifest_reply.get("type") != "asset_manifest":
            return False

        revision = int(manifest_reply.get("revision", 0))
        server_chunk_size = int(manifest_reply.get("chunk_size", SESSION_SYNC_CHUNK_SIZE))
        server_chunk_size = max(1024, min(server_chunk_size, SESSION_SYNC_CHUNK_SIZE))
        if expected_revision is not None and revision != expected_revision:
            return False

        manifest = manifest_reply.get("manifest", [])
        if not manifest:
            ready_reply = self._send_with_retry({
                "action": "asset_client_ready",
                "ready": True,
                "revision": revision,
            })
            if not ready_reply or not ready_reply.get("ok"):
                return False

            self.game.sounds.set_session_asset_root(None)
            self.asset_sync_ready = True
            self.synced_asset_revision = revision
            return True

        session_dir = os.path.join(SESSION_CACHE_DIR, self._safe_lobby_slug())
        os.makedirs(session_dir, exist_ok=True)

        for entry in manifest:
            rel_name = entry.get("name", "")
            expected_hash = entry.get("sha256", "")
            expected_size = int(entry.get("size", 0))
            if not rel_name:
                continue

            target_path = os.path.normpath(os.path.join(session_dir, rel_name))
            target_root = os.path.normpath(session_dir)
            if os.path.commonpath([target_root, target_path]) != target_root:
                self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                accessibility.speak("Session asset path was invalid.")
                return False

            if os.path.exists(target_path):
                try:
                    if not expected_hash or self._sha256_file(target_path) == expected_hash:
                        continue
                except Exception:
                    pass

            part_path = target_path + ".part"
            if os.path.exists(part_path):
                try:
                    if os.path.getsize(part_path) > expected_size:
                        os.remove(part_path)
                except Exception:
                    try:
                        os.remove(part_path)
                    except Exception:
                        pass

            offset = 0
            if os.path.exists(part_path):
                try:
                    offset = os.path.getsize(part_path)
                except Exception:
                    offset = 0

            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            if expected_size == 0 and not os.path.exists(part_path):
                with open(part_path, "wb"):
                    pass

            last_bucket = -1
            bucket = self._progress_bucket(offset, expected_size)
            if bucket > last_bucket:
                last_bucket = bucket
                accessibility.speak(f"Downloading {rel_name}: {bucket} percent.")

            while offset < expected_size:
                req_len = min(server_chunk_size, expected_size - offset)
                file_reply = self._send_with_retry({
                    "action": "asset_get_file_chunk",
                    "name": rel_name,
                    "offset": offset,
                    "length": req_len,
                })

                if not file_reply or file_reply.get("type") != "asset_file_chunk":
                    self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                    accessibility.speak(f"Could not download required asset {rel_name}.")
                    return False

                if not file_reply.get("ok"):
                    if file_reply.get("error") == "offset_mismatch":
                        expected_offset = int(file_reply.get("expected_offset", 0))
                        expected_offset = max(0, min(expected_offset, expected_size))
                        try:
                            with open(part_path, "r+b") as f:
                                f.truncate(expected_offset)
                        except FileNotFoundError:
                            with open(part_path, "wb"):
                                pass
                        offset = expected_offset
                        continue

                    self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                    accessibility.speak(f"Could not download required asset {rel_name}.")
                    return False

                chunk_data = file_reply.get("data", b"")
                if not isinstance(chunk_data, (bytes, bytearray)) or not chunk_data:
                    self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                    accessibility.speak(f"Download stalled for {rel_name}.")
                    return False

                try:
                    with open(part_path, "ab") as f:
                        f.write(bytes(chunk_data))
                except Exception:
                    self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                    accessibility.speak(f"Could not write asset file {rel_name}.")
                    return False

                offset = int(file_reply.get("next_offset", offset + len(chunk_data)))

                bucket = self._progress_bucket(offset, expected_size)
                if bucket > last_bucket:
                    last_bucket = bucket
                    accessibility.speak(f"Downloading {rel_name}: {bucket} percent.")

            try:
                os.replace(part_path, target_path)
            except Exception:
                self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                accessibility.speak(f"Could not finalize asset file {rel_name}.")
                return False

            if expected_hash and self._sha256_file(target_path) != expected_hash:
                self.game.network.send({"action": "asset_client_ready", "ready": False, "revision": revision})
                accessibility.speak(f"Downloaded asset did not match expected hash: {rel_name}.")
                return False

        ready_reply = self._send_with_retry({
            "action": "asset_client_ready",
            "ready": True,
            "revision": revision,
        })
        if not ready_reply or not ready_reply.get("ok") or not ready_reply.get("accepted", True):
            return False

        self.game.sounds.set_session_asset_root(session_dir)
        self.asset_sync_ready = True
        self.synced_asset_revision = revision
        accessibility.speak("Session assets synced and ready.")
        return True

    def _try_start_game(self):
        self.game.sounds.play_ui("ui_select")
        accessibility.speak("Starting game.")
        reply = self.game.network.send("start")
        if isinstance(reply, dict):
            reason = reply.get("start_block_reason", "")
            if reason:
                self.game.sounds.play_ui("ui_error")
                accessibility.speak(reason)

    def _apply_setup_preset(self):
        preset = self.setup_presets[self.setup_index]

        state = self.setup_preset_states.get(preset, {})

        target_light = state.get("lights")
        if target_light in self.light_presets:
            self.light_index = self.light_presets.index(target_light)

        target_music = state.get("music")
        if target_music in self.music_presets:
            self.music_index = self.music_presets.index(target_music)

        target_zone = state.get("zone")
        if target_zone in self.studio_zones:
            self.current_zone = target_zone
            self.game.network.send({"action": "move_zone", "zone": target_zone})

        target_seated = bool(state.get("seated", False))
        if self.current_zone not in self.seat_zones:
            target_seated = False
        self._set_seated(target_seated, announce=False)

        call_up_mode = state.get("call_up_mode", "keep")
        if call_up_mode == "reset":
            self.call_up_index = 0
        elif call_up_mode == "next":
            self.call_up_index += 1
        elif call_up_mode == "set":
            self.call_up_index = int(state.get("call_up_index", self.call_up_index))

        self._apply_music_preset()
        posture = "seated" if self.is_seated else "standing"
        accessibility.speak(
            f"Applied preset {preset}. "
            f"Lights {self.light_presets[self.light_index]}. "
            f"Music {self.music_presets[self.music_index]}. "
            f"Host at {self.current_zone}, {posture}."
        )

    def _apply_music_preset(self):
        preset = self.music_presets[self.music_index]
        if preset == "Lobby Theme":
            self.game.sounds.play_music("theme")
        elif preset == "Question Bed":
            self.game.sounds.play_music("q_bed_1_5")
        else:
            self.game.sounds.stop_music()

    def _activate_host_panel_item(self):
        item = self._get_current_panel_items()[self.host_panel_index]
        self.game.sounds.play_ui("ui_select")

        if self.host_panel_page == 0:
            if item == "Lights":
                self.light_index = (self.light_index + 1) % len(self.light_presets)
                accessibility.speak(f"Confirmed. Lights set to {self.light_presets[self.light_index]}.")
            elif item == "Music Bed":
                self.music_index = (self.music_index + 1) % len(self.music_presets)
                self._apply_music_preset()
                accessibility.speak(f"Confirmed. Music bed set to {self.music_presets[self.music_index]}.")
            elif item == "Play Sting":
                self.game.sounds.play("lifeline")
                accessibility.speak("Confirmed. Sting played.")
            elif item == "Refresh Session Assets":
                accessibility.speak("Confirmed. Refreshing session assets.")
                self._host_publish_session_assets()
            elif item == "Sync Status":
                accessibility.speak("Confirmed. Reporting sync status.")
                self._announce_sync_status()
            elif item == "Go To Flow Page":
                self._switch_panel_page(1)
            elif item == "Start Game":
                self._try_start_game()
            elif item == "Close Panel":
                self._close_host_panel()
        else:
            if item == "Call-Up Target":
                contestants = self._get_contestant_names()
                if not contestants:
                    accessibility.speak("No contestants are available.")
                    self.game.sounds.play_ui("ui_error")
                else:
                    self.call_up_index = (self.call_up_index + 1) % len(contestants)
                    accessibility.speak(f"Confirmed. Call-up target set to {contestants[self.call_up_index]}.")
            elif item == "Call Next Contestant":
                target = self._get_current_call_target()
                if target == "No contestants":
                    self.game.sounds.play_ui("ui_error")
                    accessibility.speak("No contestants are available.")
                else:
                    accessibility.speak(f"Confirmed. Calling {target} to the hot seat.")
            elif item == "Move Target To Hot Seat":
                target = self._get_current_call_target()
                if target == "No contestants":
                    self.game.sounds.play_ui("ui_error")
                    accessibility.speak("No contestants are available.")
                else:
                    self.game.network.send({"action": "move_target_hot_seat", "target_name": target})
                    accessibility.speak(f"Confirmed. Moved {target} to the hot seat.")
            elif item == "Quick Switch Preset":
                self.setup_index = (self.setup_index + 1) % len(self.setup_presets)
                self._apply_setup_preset()
            elif item == "Setup Preset":
                self.setup_index = (self.setup_index + 1) % len(self.setup_presets)
                accessibility.speak(f"Confirmed. Setup preset selected: {self.setup_presets[self.setup_index]}.")
            elif item == "Apply Setup Preset":
                self._apply_setup_preset()
            elif item == "Save Current As Preset":
                self._save_current_as_preset()
            elif item == "Import Preset Pack":
                self._import_setup_preset_pack()
            elif item == "Delete Selected Preset":
                self._delete_selected_preset()
            elif item == "Back To Show Controls":
                self._switch_panel_page(0)
            elif item == "Close Panel":
                self._close_host_panel()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.host_panel_open:
                if not self._local_is_host():
                    self._close_host_panel()
                    self.game.sounds.play_ui("ui_error")
                    accessibility.speak("Only the host can use the control panel.")
                    return

                if event.key == pygame.K_UP:
                    self._navigate_host_panel(-1)
                elif event.key == pygame.K_DOWN:
                    self._navigate_host_panel(1)
                elif event.key == pygame.K_LEFT:
                    self._switch_panel_page(0)
                elif event.key == pygame.K_RIGHT:
                    self._switch_panel_page(1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._activate_host_panel_item()
                elif event.key == pygame.K_ESCAPE:
                    self._close_host_panel()
                return

            if event.key == pygame.K_LEFT:
                self._move_direction("left")
            elif event.key == pygame.K_RIGHT:
                self._move_direction("right")
            elif event.key == pygame.K_UP:
                self._move_direction("up")
            elif event.key == pygame.K_DOWN:
                self._move_direction("down")
            elif event.key == pygame.K_TAB:
                self._move_tab_forward()
            elif event.key == pygame.K_h:
                self._announce_controls()
            elif event.key == pygame.K_s:
                self._toggle_seat()
            elif (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and self._can_open_host_panel():
                self._open_host_panel()
            elif event.key == pygame.K_RETURN and self._local_is_host():
                print("Host is starting the game...")
                self._try_start_game()
            elif event.key == pygame.K_ESCAPE:
                self.game.sounds.play_ui("ui_back")
                self.game.end_session()

    def update(self):
        game_state = self.game.network.send("get")
        if game_state:
            self.connection_retry_started_at = 0
            self.connection_retry_announced = False

            self.lobby_name = game_state.get("lobby_name", "Lobby")
            previous_zone = self.current_zone

            previous_host_id = self.active_host_id
            self.active_host_id = int(game_state.get("host_player_id", self.active_host_id))

            if len(self.players) != len(game_state["players"]):
                self.players = game_state["players"]
                player_names = ", ".join([
                    f"{p.name} {('seated' if getattr(p, 'seated', False) else 'standing')} "
                    f"{('connected' if getattr(p, 'connected', True) else 'reconnecting')} "
                    f"{('ready' if getattr(p, 'asset_ready', False) else 'syncing')} "
                    f"at {getattr(p, 'zone', 'Contestant Area')}"
                    for p in self.players
                ])
                accessibility.speak(f"Players in {self.lobby_name}: {player_names}")
            else:
                self.players = game_state["players"]

            if previous_host_id != self.active_host_id:
                active_name = "Unknown"
                for p in self.players:
                    if p.id == self.active_host_id:
                        active_name = p.name
                        break

                if self._local_is_host():
                    accessibility.speak("Host handoff complete. You are now the active host.")
                else:
                    accessibility.speak(f"Host handoff complete. Active host is {active_name}.")

            host_notice = game_state.get("host_handoff_notice", "")
            if host_notice and host_notice != self.last_host_handoff_notice:
                self.last_host_handoff_notice = host_notice
                if "handoff" in host_notice.lower() or "reconnected" in host_notice.lower():
                    accessibility.speak(host_notice)

            revision = int(game_state.get("asset_revision", 0))
            if not self._local_is_host() and revision != self.synced_asset_revision:
                self.asset_sync_ready = False
                now = pygame.time.get_ticks()
                if now >= self.next_asset_sync_retry_at:
                    if self._attempt_client_asset_sync(expected_revision=revision):
                        self.next_asset_sync_retry_at = 0
                    else:
                        self.next_asset_sync_retry_at = now + 3000

            reason = game_state.get("start_block_reason", "")
            if self._local_is_host() and reason and reason != self.last_start_block_reason:
                self.last_start_block_reason = reason
                accessibility.speak(reason)
            elif self._local_is_host() and not reason:
                self.last_start_block_reason = ""

            for player in self.players:
                if player.id == self.game.player_id:
                    incoming_zone = getattr(player, "zone", self.current_zone)
                    if incoming_zone in self.studio_graph:
                        self.current_zone = incoming_zone
                    self.is_seated = getattr(player, "seated", self.is_seated)
                    break

            if previous_zone != self.current_zone:
                self._announce_zone()

            if game_state["game_started"]:
                self.game.start_game()
        else:
            now = pygame.time.get_ticks()
            if self.connection_retry_started_at == 0:
                self.connection_retry_started_at = now

            if not self.connection_retry_announced:
                self.connection_retry_announced = True
                self.game.sounds.play_ui("ui_error")
                accessibility.speak("Connection interrupted. Attempting to recover.")

            if now - self.connection_retry_started_at > 7000:
                self.game.sounds.play_ui("ui_error")
                accessibility.speak("Could not recover connection. Returning to menu.")
                self.game.end_session()

    def draw(self):
        colors = self.game.config.colors
        font_title = self.game.config.fonts["title"]
        font_main = self.game.config.fonts["main"]
        font_small = self.game.config.fonts["small"]

        title_text = font_title.render(self.lobby_name, True, colors["text"])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5))
        self.screen.blit(title_text, title_rect)

        for index, player in enumerate(self.players):
            zone = getattr(player, "zone", "Contestant Area")
            posture = "Seated" if getattr(player, "seated", False) else "Standing"
            sync_state = "Ready" if getattr(player, "asset_ready", False) else "Syncing"
            player_text = f"{player.name} - {sync_state} - {posture} - {zone}"
            player_surface = font_main.render(player_text, True, colors["text"])
            player_rect = player_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + index * 55))
            self.screen.blit(player_surface, player_rect)

        zone_title = font_small.render("Studio Areas", True, colors["highlight"])
        self.screen.blit(zone_title, (40, SCREEN_HEIGHT / 3))
        for idx, zone in enumerate(self.studio_zones):
            zone_color = colors["highlight"] if zone == self.current_zone else colors["text"]
            zone_surface = font_small.render(zone, True, zone_color)
            self.screen.blit(zone_surface, (40, SCREEN_HEIGHT / 3 + 40 + idx * 36))

        if self._local_is_host():
            inst_text = font_main.render("Press Enter to Start", True, colors["highlight"])
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
            self.screen.blit(inst_text, inst_rect)
        else:
            inst_text = font_small.render("Waiting for host...", True, colors["dim"])
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
            self.screen.blit(inst_text, inst_rect)

        nav_text = font_small.render("Arrows: Move   S: Sit or Stand   H: Controls", True, colors["dim"])
        self.screen.blit(nav_text, (40, SCREEN_HEIGHT - 50))

        if self.host_panel_open:
            panel_rect = pygame.Rect(SCREEN_WIDTH - 380, 120, 340, 430)
            pygame.draw.rect(self.screen, colors["bg"], panel_rect, border_radius=12)
            pygame.draw.rect(self.screen, colors["highlight"], panel_rect, width=2, border_radius=12)

            page_name = "Show Controls" if self.host_panel_page == 0 else "Flow And Presets"
            panel_title = font_small.render(f"Host Control Panel - {page_name}", True, colors["highlight"])
            self.screen.blit(panel_title, (panel_rect.x + 16, panel_rect.y + 14))

            y = panel_rect.y + 70
            current_items = self._get_current_panel_items()
            for idx, item in enumerate(current_items):
                text = item
                if item == "Lights":
                    text = f"Lights: {self.light_presets[self.light_index]}"
                elif item == "Music Bed":
                    text = f"Music Bed: {self.music_presets[self.music_index]}"
                elif item == "Call-Up Target":
                    text = f"Call-Up Target: {self._get_current_call_target()}"
                elif item == "Setup Preset":
                    text = f"Setup Preset: {self.setup_presets[self.setup_index]}"

                color = colors["highlight"] if idx == self.host_panel_index else colors["text"]
                line = font_small.render(text, True, color)
                self.screen.blit(line, (panel_rect.x + 16, y))
                y += font_small.get_height() + 12

            hint = font_small.render("Left/Right: Switch Page", True, colors["dim"])
            self.screen.blit(hint, (panel_rect.x + 16, panel_rect.bottom - 36))
