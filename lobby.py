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

        if self.is_host:
            accessibility.speak("Lobby created. Waiting for other players to join. Press Enter to start the game. Use left and right arrow keys to move around the set.")
        else:
            accessibility.speak("Joined lobby. Waiting for the host to start the game. Use left and right arrow keys to move around the set.")

        self.game.network.send({"action": "move_zone", "zone": self.current_zone})

    def _announce_zone(self):
        self.game.sounds.play_ui("ui_arrive", "ui_select")
        accessibility.speak(f"You are at {self.current_zone}.")

    def _move_zone(self, direction):
        self.game.sounds.play_ui("ui_step", "ui_move")
        self.zone_index = (self.zone_index + direction) % len(self.studio_zones)
        self.current_zone = self.studio_zones[self.zone_index]
        self.game.network.send({"action": "move_zone", "zone": self.current_zone})
        self._announce_zone()

    def _announce_controls(self):
        accessibility.speak("Lobby controls. Left and right move between studio areas. Enter starts the game if you are host. Escape leaves the lobby.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._move_zone(-1)
            elif event.key == pygame.K_RIGHT:
                self._move_zone(1)
            elif event.key == pygame.K_TAB:
                self._move_zone(1)
            elif event.key == pygame.K_h:
                self._announce_controls()
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
                player_names = ", ".join([f"{p.name} at {getattr(p, 'zone', 'Contestant Area')}" for p in self.players])
                accessibility.speak(f"Players in {self.lobby_name}: {player_names}")
            else:
                 self.players = game_state["players"]

            for player in self.players:
                if player.id == self.game.player_id:
                    self.current_zone = getattr(player, "zone", self.current_zone)
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
            player_text = f"{player.name} - {zone}"
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

        nav_text = font_small.render("Left/Right: Move set areas   H: Controls", True, colors["dim"])
        self.screen.blit(nav_text, (40, SCREEN_HEIGHT - 50))