# lobby.py

import pygame
from settings import *
import accessible_output as accessibility

class Lobby:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.players = []
        self.font = pygame.font.Font(None, 60)
        self.title_font = pygame.font.Font(None, 90)
        self.small_font = pygame.font.Font(None, 40)
        self.is_host = (self.game.player_id == 0) 
        
        self.lobby_name = "Lobby" 

        if self.is_host:
            accessibility.speak("Lobby created. Waiting for other players to join. Press Enter to start the game.")
        else:
            accessibility.speak("Joined lobby. Waiting for the host to start the game.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.is_host:
                print("Host is starting the game...")
                accessibility.speak("Starting game.")
                self.game.network.send("start")
            elif event.key == pygame.K_ESCAPE:
                self.game.end_session()

    def update(self):
        game_state = self.game.network.send("get")
        if game_state:
            self.lobby_name = game_state.get("lobby_name", "Lobby")
            if len(self.players) != len(game_state["players"]):
                self.players = game_state["players"]
                player_names = ", ".join([p.name for p in self.players])
                accessibility.speak(f"Players in {self.lobby_name}: {player_names}")
            else:
                 self.players = game_state["players"]

            if game_state["game_started"]:
                self.game.start_game()
        else:
            accessibility.speak("Lost connection to the server. Returning to menu.")
            self.game.end_session()

    def draw(self):
        colors = self.game.config.colors

        # Draw title
        title_text = self.title_font.render(self.lobby_name, True, colors["text"])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5))
        self.screen.blit(title_text, title_rect)
        
        # Draw player list
        for index, player in enumerate(self.players):
            player_text = f"{player.name}"
            player_surface = self.font.render(player_text, True, colors["text"])
            player_rect = player_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + index * 70))
            self.screen.blit(player_surface, player_rect)
        
        # Draw instruction
        if self.is_host:
            inst_text = self.font.render("Press Enter to Start", True, colors["highlight"])
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
            self.screen.blit(inst_text, inst_rect)
        else:
            inst_text = self.small_font.render("Waiting for host...", True, colors["dim"])
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100))
            self.screen.blit(inst_text, inst_rect)