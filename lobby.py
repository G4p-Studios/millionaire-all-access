# lobby.py

import hashlib
import os

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
        self.lobby_name = "Lobby"

        self.studio_zones = STUDIO_ZONES
        self.zone_index = 0
        self.current_zone = self.studio_zones[self.zone_index]

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
            "Setup Preset",
            "Apply Setup Preset",
            "Back To Show Controls",
            "Close Panel",
        ]

        self.setup_presets = ["Classic Live", "Fast Practice", "FFF Warmup"]
        self.setup_index = 0
        self.call_up_index = 0

        self.asset_sync_ready = self.is_host
        self.synced_asset_revision = 0 if self.is_host else -1
        self.next_asset_sync_retry_at = 0
        self.last_start_block_reason = ""
        self.last_sync_skipped_count = 0
        self.last_sync_manifest_count = 0
        self.last_sync_source = ""

        if self.is_host:
            accessibility.speak(
                "Lobby created. Waiting for other players to join. Press Enter to start the game. "
                "Use left and right arrow keys to move around the set."
            )
        else:
            accessibility.speak(
                "Joined lobby. Waiting for the host to start the game. "
                "Use left and right arrow keys to move around the set."
            )

        self.game.network.send({"action": "move_zone", "zone": self.current_zone})
        self.game.network.send({"action": "set_seated", "seated": False})

        if self.is_host:
            self._host_publish_session_assets()

    def _announce_zone(self):
        self.game.sounds.play_ui("ui_arrive", "ui_select")
        accessibility.speak(f"You are at {self.current_zone}.")

        if self._can_open_host_panel():
            self.game.sounds.play_ui("ui_panel", "ui_select")
            accessibility.speak("Host control panel. Press Enter or Space to interact with controls.")

    def _move_zone(self, direction):
        if self.is_seated:
            self._set_seated(False, announce=True)

        self.game.sounds.play_ui("ui_leave", "ui_step")
        self.game.sounds.play_ui("ui_step", "ui_move")
        self.zone_index = (self.zone_index + direction) % len(self.studio_zones)
        self.current_zone = self.studio_zones[self.zone_index]
        self.game.network.send({"action": "move_zone", "zone": self.current_zone})
        self._announce_zone()

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
            "Lobby controls. Left and right move between studio areas. "
            "S sits or stands when a seat is available. "
            "Enter starts the game if you are host. Escape leaves the lobby."
        )

    def _can_open_host_panel(self):
        return self.is_host and not self.is_seated and self.current_zone == "Host Control Panel"

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
        elif item == "Setup Preset":
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

        if preset == "Classic Live":
            self.light_index = 0
            self.music_index = 0
        elif preset == "Fast Practice":
            self.light_index = 1
            self.music_index = 2
        else:
            self.light_index = 2
            self.music_index = 0

        self._apply_music_preset()
        accessibility.speak(f"Applied preset {preset}.")

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
                accessibility.speak(f"Lights set to {self.light_presets[self.light_index]}.")
            elif item == "Music Bed":
                self.music_index = (self.music_index + 1) % len(self.music_presets)
                self._apply_music_preset()
                accessibility.speak(f"Music bed set to {self.music_presets[self.music_index]}.")
            elif item == "Play Sting":
                self.game.sounds.play("lifeline")
                accessibility.speak("Played sting.")
            elif item == "Refresh Session Assets":
                accessibility.speak("Refreshing session assets.")
                self._host_publish_session_assets()
            elif item == "Sync Status":
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
                    accessibility.speak(f"Call-up target set to {contestants[self.call_up_index]}.")
            elif item == "Call Next Contestant":
                target = self._get_current_call_target()
                if target == "No contestants":
                    self.game.sounds.play_ui("ui_error")
                    accessibility.speak("No contestants are available.")
                else:
                    accessibility.speak(f"Calling {target} to the hot seat.")
            elif item == "Move Target To Hot Seat":
                target = self._get_current_call_target()
                if target == "No contestants":
                    self.game.sounds.play_ui("ui_error")
                    accessibility.speak("No contestants are available.")
                else:
                    self.game.network.send({"action": "move_target_hot_seat", "target_name": target})
                    accessibility.speak(f"Moved {target} to the hot seat.")
            elif item == "Setup Preset":
                self.setup_index = (self.setup_index + 1) % len(self.setup_presets)
                accessibility.speak(f"Setup preset selected: {self.setup_presets[self.setup_index]}.")
            elif item == "Apply Setup Preset":
                self._apply_setup_preset()
            elif item == "Back To Show Controls":
                self._switch_panel_page(0)
            elif item == "Close Panel":
                self._close_host_panel()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.host_panel_open:
                if not self.is_host:
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
                self._move_zone(-1)
            elif event.key == pygame.K_RIGHT:
                self._move_zone(1)
            elif event.key == pygame.K_TAB:
                self._move_zone(1)
            elif event.key == pygame.K_h:
                self._announce_controls()
            elif event.key == pygame.K_s:
                self._toggle_seat()
            elif (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and self._can_open_host_panel():
                self._open_host_panel()
            elif event.key == pygame.K_RETURN and self.is_host:
                print("Host is starting the game...")
                self._try_start_game()
            elif event.key == pygame.K_ESCAPE:
                self.game.sounds.play_ui("ui_back")
                self.game.end_session()

    def update(self):
        game_state = self.game.network.send("get")
        if game_state:
            self.lobby_name = game_state.get("lobby_name", "Lobby")
            previous_zone = self.current_zone

            if len(self.players) != len(game_state["players"]):
                self.players = game_state["players"]
                player_names = ", ".join([
                    f"{p.name} {('seated' if getattr(p, 'seated', False) else 'standing')} "
                    f"{('ready' if getattr(p, 'asset_ready', False) else 'syncing')} "
                    f"at {getattr(p, 'zone', 'Contestant Area')}"
                    for p in self.players
                ])
                accessibility.speak(f"Players in {self.lobby_name}: {player_names}")
            else:
                self.players = game_state["players"]

            revision = int(game_state.get("asset_revision", 0))
            if not self.is_host and revision != self.synced_asset_revision:
                self.asset_sync_ready = False
                now = pygame.time.get_ticks()
                if now >= self.next_asset_sync_retry_at:
                    if self._attempt_client_asset_sync(expected_revision=revision):
                        self.next_asset_sync_retry_at = 0
                    else:
                        self.next_asset_sync_retry_at = now + 3000

            reason = game_state.get("start_block_reason", "")
            if self.is_host and reason and reason != self.last_start_block_reason:
                self.last_start_block_reason = reason
                accessibility.speak(reason)
            elif self.is_host and not reason:
                self.last_start_block_reason = ""

            for player in self.players:
                if player.id == self.game.player_id:
                    self.current_zone = getattr(player, "zone", self.current_zone)
                    self.is_seated = getattr(player, "seated", self.is_seated)
                    if self.current_zone in self.studio_zones:
                        self.zone_index = self.studio_zones.index(self.current_zone)
                    break

            if previous_zone != self.current_zone:
                self._announce_zone()

            if game_state["game_started"]:
                self.game.start_game()
        else:
            self.game.sounds.play_ui("ui_error")
            accessibility.speak("Lost connection to the server. Returning to menu.")
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

        if self.is_host:
            inst_text = font_main.render("Press Enter to Start", True, colors["highlight"])
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
            self.screen.blit(inst_text, inst_rect)
        else:
            inst_text = font_small.render("Waiting for host...", True, colors["dim"])
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
            self.screen.blit(inst_text, inst_rect)

        nav_text = font_small.render("Left/Right: Move   S: Sit or Stand   H: Controls", True, colors["dim"])
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
