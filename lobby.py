# lobby.py

import pygame
from settings import *
import accessible_output as accessibility

class Lobby:
    def __init__(self, game):
        # FIX: Ensure no lingering inputs (like Enter from menu) trigger actions
        pygame.event.clear()
        
        self.game = game
        self.screen = game.screen
        self.players = []
        self.is_host = (self.game.player_id == 0) 
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
            "Go To Flow Page",
            "Start Game",
            "Close Panel",
        ]
        self.host_flow_items = [
            "Call-Up Target",
            "Call Next Contestant",
            "Setup Preset",
            "Apply Setup Preset",
            "Back To Show Controls",
            "Close Panel",
        ]
        self.setup_presets = ["Classic Live", "Fast Practice", "FFF Warmup"]
        self.setup_index = 0
        self.call_up_index = 0

        if self.is_host:
            accessibility.speak("Lobby created. Waiting for other players to join. Press Enter to start the game. Use left and right arrow keys to move around the set.")
        else:
            accessibility.speak("Joined lobby. Waiting for the host to start the game. Use left and right arrow keys to move around the set.")

        self.game.network.send({"action": "move_zone", "zone": self.current_zone})
        self.game.network.send({"action": "set_seated", "seated": False})

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
        accessibility.speak("Lobby controls. Left and right move between studio areas. S sits or stands when a seat is available. Enter starts the game if you are host. Escape leaves the lobby.")

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
        title = "Show Controls" if page == 0 else "Flow And Presets"
        accessibility.speak(title)
        self._announce_host_panel_selection()

    def _get_contestant_names(self):
        names = [p.name for p in self.players if getattr(p, "id", -1) != 0]
        return names

    def _get_current_call_target(self):
        contestants = self._get_contestant_names()
        if not contestants:
            return "No contestants"
        self.call_up_index %= len(contestants)
        return contestants[self.call_up_index]

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
            elif item == "Go To Flow Page":
                self._switch_panel_page(1)
            elif item == "Start Game":
                accessibility.speak("Starting game.")
                self.game.network.send("start")
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
                self.game.sounds.play_ui("ui_select")
                accessibility.speak("Starting game.")
                self.game.network.send("start")
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
                    f"{p.name} {('seated' if getattr(p, 'seated', False) else 'standing')} at {getattr(p, 'zone', 'Contestant Area')}"
                    for p in self.players
                ])
                accessibility.speak(f"Players in {self.lobby_name}: {player_names}")
            else:
                 self.players = game_state["players"]

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

        # Draw title
        title_text = font_title.render(self.lobby_name, True, colors["text"])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5))
        self.screen.blit(title_text, title_rect)
        
        # Draw player list
        for index, player in enumerate(self.players):
            zone = getattr(player, "zone", "Contestant Area")
            posture = "Seated" if getattr(player, "seated", False) else "Standing"
            player_text = f"{player.name} - {posture} - {zone}"
            player_surface = font_main.render(player_text, True, colors["text"])
            player_rect = player_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + index * 55))
            self.screen.blit(player_surface, player_rect)

        zone_title = font_small.render("Studio Areas", True, colors["highlight"])
        self.screen.blit(zone_title, (40, SCREEN_HEIGHT / 3))
        for idx, zone in enumerate(self.studio_zones):
            zone_color = colors["highlight"] if zone == self.current_zone else colors["text"]
            zone_surface = font_small.render(zone, True, zone_color)
            self.screen.blit(zone_surface, (40, SCREEN_HEIGHT / 3 + 40 + idx * 36))
        
        # Draw instruction
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