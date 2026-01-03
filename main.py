# main.py

import pygame
import sys
from settings import *
import accessible_output as accessibility
from menu import Menu
from lobby import Lobby
from gameplay import Gameplay
from network import Network
from config import Config
from sound_manager import SoundManager

class Game:
    def __init__(self):
        pygame.init()
        # Ensure repeat is off by default
        pygame.key.set_repeat(0)
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.config = Config()
        if self.config.data["fullscreen"]:
            self.set_fullscreen(True)

        self.sounds = SoundManager()
        
        self.game_state = 'menu'
        self.network = None
        self.server_process = None
        self.player_id = -1 

        self.menu = Menu(self)
        self.lobby = None
        self.gameplay = None

        accessibility.speak(f"Welcome to {SCREEN_TITLE}. Main menu.", interrupt=True)
    
    def set_fullscreen(self, full):
        flags = pygame.FULLSCREEN if full else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)

    def connect_to_server(self, ip_address, port=SERVER_PORT):
        self.network = Network(ip_address, port)
        my_name = self.config.data["player_name"]
        
        player_data = self.network.connect(my_name)
        if player_data:
            self.player_id = player_data.id
            role = "Host" if self.player_id == 0 else "Player"
            accessibility.speak(f"Connected as {role} (ID {self.player_id}).")
            self.start_lobby() 
        else:
            accessibility.speak("Connection failed. Returning to menu.")
            if self.game_state != 'menu':
                self.end_session()
    
    def start_lobby(self):
        self.game_state = 'lobby'
        self.lobby = Lobby(self)

    def start_game(self):
        self.game_state = 'gameplay'
        self.gameplay = Gameplay(self)

    def end_session(self):
        self.game_state = 'menu'
        self.sounds.stop_all()
        self.sounds.play_music("theme")
        
        if self.network:
            self.network = None
        if self.server_process:
            try: self.server_process.terminate()
            except Exception: pass
            self.server_process = None
            print("Server process terminated.")
        self.player_id = -1
        self.lobby = None
        self.gameplay = None
        self.menu = Menu(self)
        pygame.key.set_repeat(0)
        accessibility.speak("Returned to Main Menu.")

    def run(self):
        self.sounds.play_music("theme")
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.quit()
            
            if event.type == pygame.KEYDOWN:
                # --- GLOBAL SHORTCUTS ---
                if event.key == pygame.K_F1:
                    accessibility.speak("Help: Arrow keys to navigate, Enter to select, Escape to go back.")
                elif event.key == pygame.K_F11:
                    self.config.toggle_fullscreen()
                    self.set_fullscreen(self.config.data["fullscreen"])
                    state = "Fullscreen" if self.config.data["fullscreen"] else "Windowed"
                    accessibility.speak(state)
                
                # --- ESCAPE LOGIC ---
                elif event.key == pygame.K_ESCAPE:
                    # 1. LOBBY: Allow leaving
                    if self.game_state == 'lobby':
                        accessibility.speak("Leaving session.")
                        self.end_session()
                        continue 
                    
                    # 2. GAMEPLAY: BLOCK Escape (User must use W)
                    elif self.game_state == 'gameplay':
                        accessibility.speak("Press W to walk away.")
                        continue

                    # 3. MENU: Handle Quit vs Back
                    elif self.game_state == 'menu':
                        # If at top level menu, Quit. 
                        if self.menu.state == "MAIN":
                            self.quit()
                        # If in submenu, pass to menu handler (handled in menu.py via change_state)

            # Pass events to state handlers
            if self.game_state == 'menu': self.menu.handle_event(event)
            elif self.game_state == 'lobby' and self.lobby: self.lobby.handle_event(event)
            elif self.game_state == 'gameplay' and self.gameplay: self.gameplay.handle_event(event)

    def update(self):
        if self.game_state == 'lobby' and self.lobby:
            self.lobby.update()

    def draw(self):
        self.screen.fill(self.config.colors["bg"])
        if self.game_state == 'menu': self.menu.draw()
        elif self.game_state == 'lobby' and self.lobby: self.lobby.draw()
        elif self.game_state == 'gameplay' and self.gameplay: self.gameplay.draw()
        pygame.display.flip()

    def quit(self):
        accessibility.speak("Exiting the game. Goodbye!")
        self.end_session() 
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = Game()
    try: game.run()
    finally: pass