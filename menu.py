# menu.py

import pygame
import subprocess
import sys
from settings import *
import accessible_output as accessibility

class Menu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.menu_items = ["Host Game", "Join Game", "Settings", "Quit"]
        self.selected_index = 0
        self.font = pygame.font.Font(None, 60)
        self.title_font = pygame.font.Font(None, 90)
        self.announce_current_selection()

    def announce_current_selection(self):
        selected_item = self.menu_items[self.selected_index]
        accessibility.speak(f"{selected_item}, button")

    def navigate(self, direction):
        self.selected_index = (self.selected_index + direction) % len(self.menu_items)
        self.announce_current_selection()

    def select(self):
        selected_item = self.menu_items[self.selected_index]
        accessibility.speak(f"Selected {selected_item}")

        if selected_item == "Host Game":
            self.host_game()
        elif selected_item == "Join Game":
            self.game.connect_to_server("127.0.0.1")
        elif selected_item == "Settings":
            print("Action: Settings selected")
        elif selected_item == "Quit":
            self.game.running = False
    
    def host_game(self):
        """Launches the server and connects to it."""
        try:
            port_to_use = str(SERVER_PORT)
            command = [sys.executable, "server.py", port_to_use]
            
            self.game.server_process = subprocess.Popen(command)
            accessibility.speak("Starting server...")
            pygame.time.wait(1000)
            
            self.game.connect_to_server("127.0.0.1")
        except FileNotFoundError:
            print("Error: server.py not found.")
            accessibility.speak("Error, server script not found.")
        except Exception as e:
            print(f"Failed to start server: {e}")
            accessibility.speak("Failed to start server.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.navigate(-1)
            elif event.key == pygame.K_DOWN: self.navigate(1)
            elif event.key == pygame.K_RETURN: self.select()

    def draw(self):
        title_text = self.title_font.render(SCREEN_TITLE, True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
        self.screen.blit(title_text, title_rect)

        for index, item in enumerate(self.menu_items):
            color = (255, 255, 0) if index == self.selected_index else WHITE
            text_surface = self.font.render(item, True, color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + index * 70))
            self.screen.blit(text_surface, text_rect)