# main.py

import pygame
import sys
from settings import *
import accessible_output as accessibility
from menu import Menu
from lobby import Lobby # --- NEW ---
from gameplay import Gameplay
from network import Network

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = 'menu'

        # Network and Player Info
        self.network = None
        self.server_process = None
        self.player_id = -1 # Keep track of our own player ID

        # State objects
        self.menu = Menu(self)
        self.lobby = None
        self.gameplay = None

        accessibility.speak(f"Welcome to {SCREEN_TITLE}. Main menu.", interrupt=True)
    
    def connect_to_server(self, ip_address):
        self.network = Network(ip_address, SERVER_PORT)
        player_data = self.network.connect()
        if player_data:
            self.player_id = player_data.id
            accessibility.speak(f"Successfully connected as Player {self.player_id}.")
            self.start_lobby() # --- CHANGED: Go to lobby, not game ---
        else:
            self.end_session() # Clean up if connection failed
            accessibility.speak("Connection failed. Returning to menu.")
    
    def start_lobby(self):
        self.game_state = 'lobby'
        self.lobby = Lobby(self)

    def start_game(self):
        self.game_state = 'gameplay'
        self.gameplay = Gameplay(self)

    def end_session(self):
        """--- NEW: Central cleanup function ---"""
        self.game_state = 'menu'
        if self.network:
            self.network = None
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            print("Server process terminated.")
        # Reset player state
        self.player_id = -1
        self.lobby = None
        self.gameplay = None


    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state in ['lobby', 'gameplay']:
                        accessibility.speak("Leaving session. Returning to main menu.")
                        self.end_session() # Use the cleanup function
                    else:
                        self.running = False

            if self.game_state == 'menu': self.menu.handle_event(event)
            elif self.game_state == 'lobby' and self.lobby: self.lobby.handle_event(event)
            elif self.game_state == 'gameplay' and self.gameplay: self.gameplay.handle_event(event)

    def update(self):
        """Handle periodic updates for lobby and gameplay."""
        if self.game_state == 'lobby' and self.lobby:
            self.lobby.update()
        # We can add a similar update for gameplay later to sync state

    def draw(self):
        self.screen.fill(BLUE)
        if self.game_state == 'menu': self.menu.draw()
        elif self.game_state == 'lobby' and self.lobby: self.lobby.draw()
        elif self.game_state == 'gameplay' and self.gameplay: self.gameplay.draw()
        pygame.display.flip()

    def quit(self):
        accessibility.speak("Exiting the game. Goodbye!")
        self.end_session() # Ensure server is terminated on quit
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = Game()
    try:
        game.run()
    finally:
        game.quit()