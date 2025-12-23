# menu.py

import pygame
import subprocess
import sys
import urllib.request
import json
from settings import *
import accessible_output as accessibility

class Menu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.state = "MAIN"
        
        self.host_config = {
            "Lobby Name": "My Game",
            "Port": str(SERVER_PORT),
            "Host Name": self.game.config.data["player_name"],
            "Public": False
        }
        
        self.join_private_config = {
            "Player Name": self.game.config.data["player_name"],
            "IP Address": "127.0.0.1",
            "Port": str(SERVER_PORT)
        }

        self.public_lobbies = []
        self.public_lobby_status = "Loading..."

        self.items = {
            "MAIN": ["Host Game", "Join Game", "Settings", "Quit"],
            "HOST_CONFIG": ["Lobby Name", "Port", "Host Name", "Public", "Start Server", "Back"],
            "JOIN_SELECT": ["Join Private Lobby", "Join Public Lobby", "Back"],
            "JOIN_PRIVATE": ["Player Name", "IP Address", "Port", "Connect", "Back"],
            "JOIN_PUBLIC": ["Refresh", "Back"],
            # Added Currency to settings
            "SETTINGS": ["Theme", "Font Size", "Fullscreen", "Currency", "Speech Interrupt", "Lobby Spy URL", "Back"]
        }

        self.selected_index = 0
        self.editing = False 
        self.announce_current_selection()

    def announce_current_selection(self):
        item = self.get_current_item_text()
        suffix = ""
        
        if self.state == "SETTINGS":
            if item == "Theme":
                suffix = f": {self.game.config.data['theme']}. Press Enter to toggle."
            elif item == "Speech Interrupt":
                status = "On" if self.game.config.data['speech_interrupt'] else "Off"
                suffix = f": {status}. Press Enter to toggle."
            elif item == "Font Size":
                suffix = f": {self.game.config.data['font_scale']}. Press Enter to change."
            elif item == "Fullscreen":
                status = "On" if self.game.config.data['fullscreen'] else "Off"
                suffix = f": {status}. Press Enter to toggle."
            elif item == "Currency":
                curr = "Pounds" if self.game.config.data['currency'] == "GBP" else "Dollars"
                suffix = f": {curr}. Press Enter to toggle."
            elif item == "Lobby Spy URL":
                val = self.game.config.data['lobby_spy_url']
                suffix = f": {val}. Press Enter to edit."

        elif self.state == "HOST_CONFIG":
            key = self.items["HOST_CONFIG"][self.selected_index]
            if key in ["Lobby Name", "Port", "Host Name"]:
                value = self.host_config[key]
                suffix = f": {value}. Press Enter to edit."
            elif key == "Public":
                state = "Checked" if self.host_config["Public"] else "Unchecked"
                suffix = f": {state}. Press Enter to toggle."
            elif key == "Start Server":
                suffix = ", button."
        
        elif self.state == "JOIN_PRIVATE":
            key = self.items["JOIN_PRIVATE"][self.selected_index]
            if key in ["IP Address", "Port", "Player Name"]:
                value = self.join_private_config[key]
                suffix = f": {value}. Press Enter to edit."
        
        accessibility.speak(f"{item} {suffix}")

    def get_current_item_text(self):
        current_list = self.items.get(self.state, [])
        if 0 <= self.selected_index < len(current_list):
            return current_list[self.selected_index]
        return ""

    def navigate(self, direction):
        if self.editing: return 
        current_list = self.items.get(self.state, [])
        if not current_list: return
        self.selected_index = (self.selected_index + direction) % len(current_list)
        self.announce_current_selection()

    def handle_text_input(self, event):
        if not self.editing: return
        if event.key == pygame.K_RETURN:
            self.editing = False
            if self.state == "HOST_CONFIG" and self.get_current_item_text() == "Host Name":
                self.game.config.data["player_name"] = self.host_config["Host Name"]
                self.game.config.save()
            elif self.state == "JOIN_PRIVATE" and self.get_current_item_text() == "Player Name":
                self.game.config.data["player_name"] = self.join_private_config["Player Name"]
                self.game.config.save()
            elif self.state == "SETTINGS" and self.get_current_item_text() == "Lobby Spy URL":
                self.game.config.save()
            
            accessibility.speak(f"Saved. {self.get_current_item_text()}")
            return
        elif event.key == pygame.K_ESCAPE:
            self.editing = False
            accessibility.speak("Cancelled edit.")
            self.game.config.load()
            return
        elif event.key == pygame.K_BACKSPACE:
            self.update_field_value(backspace=True)
        else:
            if len(event.unicode) > 0 and event.unicode.isprintable():
                self.update_field_value(char=event.unicode)

    def update_field_value(self, char=None, backspace=False):
        target_dict = None
        key = self.get_current_item_text()
        
        if self.state == "HOST_CONFIG": target_dict = self.host_config
        elif self.state == "JOIN_PRIVATE": target_dict = self.join_private_config
        elif self.state == "SETTINGS" and key == "Lobby Spy URL":
            target_dict = self.game.config.data
            key = "lobby_spy_url" 

        if target_dict is not None and key in target_dict:
            current_val = target_dict[key]
            if backspace:
                target_dict[key] = current_val[:-1]
                accessibility.speak("Delete")
            elif char:
                target_dict[key] = current_val + char
                accessibility.speak(char)

    def select(self):
        selection = self.get_current_item_text()
        
        if self.state == "MAIN":
            if selection == "Host Game": self.change_state("HOST_CONFIG")
            elif selection == "Join Game": self.change_state("JOIN_SELECT")
            elif selection == "Settings": self.change_state("SETTINGS")
            elif selection == "Quit": self.game.quit()

        elif self.state == "SETTINGS":
            if selection == "Theme":
                self.game.config.toggle_theme()
                accessibility.speak(f"Theme: {self.game.config.data['theme']}")
            elif selection == "Font Size":
                self.game.config.cycle_font_size()
                accessibility.speak(f"Font Size: {self.game.config.data['font_scale']}")
            elif selection == "Fullscreen":
                self.game.config.toggle_fullscreen()
                self.game.set_fullscreen(self.game.config.data["fullscreen"])
                state = "On" if self.game.config.data["fullscreen"] else "Off"
                accessibility.speak(f"Fullscreen: {state}")
            elif selection == "Currency":
                self.game.config.toggle_currency()
                curr = "Pounds" if self.game.config.data['currency'] == "GBP" else "Dollars"
                accessibility.speak(f"Currency: {curr}")
            elif selection == "Speech Interrupt":
                self.game.config.toggle_interrupt()
                status = "On" if self.game.config.data['speech_interrupt'] else "Off"
                accessibility.speak(f"Speech Interrupt: {status}")
            elif selection == "Lobby Spy URL":
                self.editing = True
                accessibility.speak("Editing Lobby Spy URL. Type now.")
            elif selection == "Back":
                self.change_state("MAIN")

        elif self.state == "HOST_CONFIG":
            if selection in ["Lobby Name", "Port", "Host Name"]:
                self.editing = True
                accessibility.speak(f"Editing {selection}. Type now.")
            elif selection == "Public":
                self.host_config["Public"] = not self.host_config["Public"]
                state = "Checked" if self.host_config["Public"] else "Unchecked"
                accessibility.speak(f"Public Lobby {state}")
            elif selection == "Start Server":
                self.start_hosting()
            elif selection == "Back":
                self.change_state("MAIN")

        elif self.state == "JOIN_SELECT":
            if selection == "Join Private Lobby": self.change_state("JOIN_PRIVATE")
            elif selection == "Join Public Lobby":
                self.change_state("JOIN_PUBLIC")
                self.fetch_public_lobbies()
            elif selection == "Back": self.change_state("MAIN")

        elif self.state == "JOIN_PRIVATE":
            if selection in ["IP Address", "Port", "Player Name"]:
                self.editing = True
                accessibility.speak(f"Editing {selection}. Type now.")
            elif selection == "Connect": self.connect_private()
            elif selection == "Back": self.change_state("JOIN_SELECT")

        elif self.state == "JOIN_PUBLIC":
            if selection == "Back": self.change_state("JOIN_SELECT")
            elif selection == "Refresh": self.fetch_public_lobbies()
            elif selection.startswith("Lobby:"):
                try:
                    lobby_idx = self.selected_index - 1 
                    if 0 <= lobby_idx < len(self.public_lobbies):
                        lobby_data = self.public_lobbies[lobby_idx]
                        ip = lobby_data.get('ip', '127.0.0.1')
                        port = lobby_data.get('port', SERVER_PORT)
                        self.game.connect_to_server(ip, int(port))
                except Exception as e:
                    print(e)
                    accessibility.speak("Error connecting to lobby.")

    def change_state(self, new_state):
        self.state = new_state
        self.selected_index = 0
        self.editing = False
        self.announce_current_selection()

    def start_hosting(self):
        try:
            port = self.host_config["Port"]
            name = self.host_config["Lobby Name"]
            host = self.host_config["Host Name"]
            is_public = "1" if self.host_config["Public"] else "0"
            spy_url = self.game.config.data["lobby_spy_url"]
            try: int(port)
            except ValueError:
                accessibility.speak("Invalid Port number.")
                return

            command = [sys.executable, "server.py", port, name, host, is_public, spy_url]
            self.game.server_process = subprocess.Popen(command)
            accessibility.speak(f"Starting lobby {name}. Please wait.")
            pygame.time.wait(1000)
            self.game.connect_to_server("127.0.0.1", int(port))
        except Exception as e:
            print(f"Failed to start server: {e}")
            accessibility.speak("Failed to start server.")

    def connect_private(self):
        ip = self.join_private_config["IP Address"]
        port_str = self.join_private_config["Port"]
        try:
            port = int(port_str)
            accessibility.speak(f"Connecting to {ip} on port {port}...")
            self.game.connect_to_server(ip, port)
        except ValueError:
            accessibility.speak("Invalid Port number.")

    def fetch_public_lobbies(self):
        self.public_lobby_status = "Fetching lobbies..."
        accessibility.speak("Fetching public lobbies list.")
        try:
            url = self.game.config.data["lobby_spy_url"]
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                self.public_lobbies = data 
                self.public_lobby_status = f"Found {len(self.public_lobbies)} lobbies."
                lobby_items = []
                for l in self.public_lobbies:
                    name = l.get('name', 'Unknown')
                    host = l.get('host', 'Unknown')
                    lobby_items.append(f"Lobby: {name} (Host: {host})")
                self.items["JOIN_PUBLIC"] = ["Refresh"] + lobby_items + ["Back"]
                accessibility.speak(self.public_lobby_status)
        except Exception as e:
            print(f"Spy Error: {e}")
            self.public_lobby_status = "Could not fetch lobbies."
            self.items["JOIN_PUBLIC"] = ["Refresh", "Back"]
            accessibility.speak("Could not reach Lobby Spy service.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.editing: self.handle_text_input(event)
            else:
                if event.key == pygame.K_UP: self.navigate(-1)
                elif event.key == pygame.K_DOWN: self.navigate(1)
                elif event.key == pygame.K_RETURN: self.select()
                elif event.key == pygame.K_BACKSPACE and self.state != "MAIN": pass 

    def draw(self):
        title = "Menu"
        if self.state == "HOST_CONFIG": title = "Host Game"
        elif self.state == "JOIN_SELECT": title = "Join Game"
        elif self.state == "JOIN_PRIVATE": title = "Join Private"
        elif self.state == "JOIN_PUBLIC": title = "Public Lobbies"
        elif self.state == "SETTINGS": title = "Settings"

        colors = self.game.config.colors
        font_main = self.game.config.fonts["main"]
        font_title = self.game.config.fonts["title"]
        font_small = self.game.config.fonts["small"]
        
        title_surf = font_title.render(title, True, colors["text"])
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 50))

        current_items = self.items.get(self.state, [])
        start_y = 150
        
        for i, item_label in enumerate(current_items):
            color = colors["highlight"] if i == self.selected_index else colors["text"]
            display_text = item_label
            
            if self.state == "HOST_CONFIG":
                if item_label in self.host_config:
                    val = self.host_config[item_label]
                    if item_label == "Public": val = "[X]" if val else "[ ]"
                    display_text = f"{item_label}: {val}"
                    if i == self.selected_index and self.editing: display_text += "|"

            elif self.state == "JOIN_PRIVATE":
                if item_label in self.join_private_config:
                    val = self.join_private_config[item_label]
                    display_text = f"{item_label}: {val}"
                    if i == self.selected_index and self.editing: display_text += "|"

            elif self.state == "SETTINGS":
                if item_label == "Theme":
                    display_text = f"Theme: {self.game.config.data['theme']}"
                elif item_label == "Speech Interrupt":
                    status = "On" if self.game.config.data['speech_interrupt'] else "Off"
                    display_text = f"Speech Interrupt: {status}"
                elif item_label == "Font Size":
                    display_text = f"Font Size: {self.game.config.data['font_scale']}"
                elif item_label == "Fullscreen":
                    status = "On" if self.game.config.data['fullscreen'] else "Off"
                    display_text = f"Fullscreen: {status}"
                elif item_label == "Currency":
                    val = "Pounds" if self.game.config.data['currency'] == "GBP" else "Dollars"
                    display_text = f"Currency: {val}"
                elif item_label == "Lobby Spy URL":
                    val = self.game.config.data['lobby_spy_url']
                    display_text = f"Lobby Spy: {val}"
                    if i == self.selected_index and self.editing: display_text += "|"

            item_surf = font_main.render(display_text, True, color)
            rect = item_surf.get_rect(center=(SCREEN_WIDTH//2, start_y + i * (font_main.get_height() + 10)))
            self.screen.blit(item_surf, rect)
        
        if self.state == "JOIN_PUBLIC":
            status_surf = font_small.render(self.public_lobby_status, True, colors["dim"])
            self.screen.blit(status_surf, (20, SCREEN_HEIGHT - 40))