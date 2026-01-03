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
        
        self.game.sounds.play_music("theme")
        
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

        self.join_public_config = {
            "Player Name": self.game.config.data["player_name"]
        }

        self.public_lobbies = []
        self.public_lobby_status = "Loading..."

        self.items = {
            "MAIN": ["Host Game", "Join Game", "Settings", "Quit"],
            "HOST_CONFIG": ["Lobby Name", "Port", "Host Name", "Public", "Start Server", "Back"],
            "JOIN_SELECT": ["Join Private Lobby", "Join Public Lobby", "Back"],
            "JOIN_PRIVATE": ["Player Name", "IP Address", "Port", "Connect", "Back"],
            "JOIN_PUBLIC": ["Player Name", "Refresh", "Back"],
            "SETTINGS": ["Theme", "Font Size", "Fullscreen", "Currency", "Speech Interrupt", "Lobby Spy URL", "Back"]
        }

        self.selected_index = 0
        self.editing = False
        self.cursor_pos = 0 
        self.selection_anchor = None 
        self.announce_current_selection()

    def announce_current_selection(self):
        item_text = self.get_current_item_text()
        control_type = "button"
        value_text = ""
        help_text = ""

        if self.state == "SETTINGS":
            if item_text == "Theme":
                control_type = "toggle"
                value_text = self.game.config.data['theme']
                help_text = "Press Enter to change"
            elif item_text == "Font Size":
                control_type = "toggle"
                value_text = self.game.config.data['font_scale']
                help_text = "Press Enter to change"
            elif item_text == "Fullscreen":
                control_type = "checkbox"
                state = self.game.config.data['fullscreen']
                value_text = "checked" if state else "unchecked"
            elif item_text == "Currency":
                control_type = "toggle"
                curr = self.game.config.data['currency']
                value_text = "Pounds" if curr == "GBP" else "Dollars"
                help_text = "Press Enter to change"
            elif item_text == "Speech Interrupt":
                control_type = "checkbox"
                state = self.game.config.data['speech_interrupt']
                value_text = "checked" if state else "unchecked"
            elif item_text == "Lobby Spy URL":
                control_type = "edit text"
                value_text = self.game.config.data['lobby_spy_url']
                help_text = "Press Enter to type"

        elif self.state == "HOST_CONFIG":
            if item_text in ["Lobby Name", "Port", "Host Name"]:
                control_type = "edit text"
                value_text = self.host_config.get(item_text, "")
                help_text = "Press Enter to type"
            elif item_text == "Public":
                control_type = "checkbox"
                state = self.host_config.get("Public", False)
                value_text = "checked" if state else "unchecked"
            
        elif self.state == "JOIN_PRIVATE":
            if item_text in ["Player Name", "IP Address", "Port"]:
                control_type = "edit text"
                value_text = self.join_private_config.get(item_text, "")
                help_text = "Press Enter to type"

        elif self.state == "JOIN_PUBLIC":
            if item_text == "Player Name":
                control_type = "edit text"
                value_text = self.join_public_config.get(item_text, "")
                help_text = "Press Enter to type"
            elif item_text.startswith("Lobby:"):
                pass

        announcement = item_text
        if value_text: announcement += f": {value_text}"
        announcement += f", {control_type}"
        if help_text: announcement += f". {help_text}"

        accessibility.speak(announcement)

    def get_current_item_text(self):
        current_list = self.items.get(self.state, [])
        if 0 <= self.selected_index < len(current_list):
            return current_list[self.selected_index]
        return ""

    def get_active_config_target(self):
        key = self.get_current_item_text()
        target_dict = None
        
        if self.state == "HOST_CONFIG": target_dict = self.host_config
        elif self.state == "JOIN_PRIVATE": target_dict = self.join_private_config
        elif self.state == "JOIN_PUBLIC" and key == "Player Name": target_dict = self.join_public_config
        elif self.state == "SETTINGS" and key == "Lobby Spy URL":
            target_dict = self.game.config.data
            key = "lobby_spy_url"

        if target_dict is not None and key in target_dict:
            return target_dict, key, target_dict[key]
        return None, None, None

    def navigate(self, direction):
        if self.editing: return 
        current_list = self.items.get(self.state, [])
        if not current_list: return
        self.selected_index = (self.selected_index + direction) % len(current_list)
        self.announce_current_selection()

    def delete_selection(self, current_val):
        if self.selection_anchor is None: return current_val, self.cursor_pos
        start = min(self.selection_anchor, self.cursor_pos)
        end = max(self.selection_anchor, self.cursor_pos)
        new_val = current_val[:start] + current_val[end:]
        return new_val, start

    def handle_text_input(self, event):
        if not self.editing: return
        
        target_dict, key, current_val = self.get_active_config_target()
        if target_dict is None: return

        mods = pygame.key.get_mods()
        is_shift = mods & pygame.KMOD_SHIFT
        is_ctrl = mods & pygame.KMOD_CTRL

        if event.key == pygame.K_RETURN:
            self.stop_editing()
            if self.state == "HOST_CONFIG" and key == "Host Name":
                self.game.config.data["player_name"] = current_val
                self.game.config.save()
            elif self.state == "JOIN_PRIVATE" and key == "Player Name":
                self.game.config.data["player_name"] = current_val
                self.game.config.save()
            elif self.state == "JOIN_PUBLIC" and key == "Player Name":
                self.game.config.data["player_name"] = current_val
                self.game.config.save()
            elif self.state == "SETTINGS" and key == "lobby_spy_url":
                self.game.config.save()
            accessibility.speak(f"Saved. {current_val}")
            return
            
        elif event.key == pygame.K_ESCAPE:
            self.stop_editing()
            accessibility.speak("Cancelled edit.")
            self.game.config.load()
            return

        elif event.key == pygame.K_a and is_ctrl:
            self.selection_anchor = 0
            self.cursor_pos = len(current_val)
            accessibility.speak("Select All")
            return

        elif event.key == pygame.K_LEFT:
            if is_shift:
                if self.selection_anchor is None: self.selection_anchor = self.cursor_pos
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
                    accessibility.speak(current_val[self.cursor_pos])
            else:
                if self.selection_anchor is not None:
                    self.cursor_pos = min(self.selection_anchor, self.cursor_pos)
                    self.selection_anchor = None
                elif self.cursor_pos > 0:
                    self.cursor_pos -= 1
                    accessibility.speak(current_val[self.cursor_pos])
        
        elif event.key == pygame.K_RIGHT:
            if is_shift:
                if self.selection_anchor is None: self.selection_anchor = self.cursor_pos
                if self.cursor_pos < len(current_val):
                    self.cursor_pos += 1
                    accessibility.speak(current_val[self.cursor_pos-1])
            else:
                if self.selection_anchor is not None:
                    self.cursor_pos = max(self.selection_anchor, self.cursor_pos)
                    self.selection_anchor = None
                elif self.cursor_pos < len(current_val):
                    self.cursor_pos += 1
                    accessibility.speak(current_val[self.cursor_pos-1])

        elif event.key == pygame.K_HOME:
            if is_shift:
                if self.selection_anchor is None: self.selection_anchor = self.cursor_pos
                self.cursor_pos = 0
            else:
                self.selection_anchor = None
                self.cursor_pos = 0
            accessibility.speak("Start")

        elif event.key == pygame.K_END:
            if is_shift:
                if self.selection_anchor is None: self.selection_anchor = self.cursor_pos
                self.cursor_pos = len(current_val)
            else:
                self.selection_anchor = None
                self.cursor_pos = len(current_val)
            accessibility.speak("End")

        elif event.key == pygame.K_BACKSPACE:
            if self.selection_anchor is not None and self.selection_anchor != self.cursor_pos:
                new_val, new_pos = self.delete_selection(current_val)
                target_dict[key] = new_val
                self.cursor_pos = new_pos
                self.selection_anchor = None
                accessibility.speak("Selection deleted")
            elif self.cursor_pos > 0:
                deleted_char = current_val[self.cursor_pos - 1]
                target_dict[key] = current_val[:self.cursor_pos - 1] + current_val[self.cursor_pos:]
                self.cursor_pos -= 1
                accessibility.speak(f"{deleted_char} deleted")
        
        elif event.key == pygame.K_DELETE:
            if self.selection_anchor is not None and self.selection_anchor != self.cursor_pos:
                new_val, new_pos = self.delete_selection(current_val)
                target_dict[key] = new_val
                self.cursor_pos = new_pos
                self.selection_anchor = None
                accessibility.speak("Selection deleted")
            elif self.cursor_pos < len(current_val):
                deleted_char = current_val[self.cursor_pos]
                target_dict[key] = current_val[:self.cursor_pos] + current_val[self.cursor_pos + 1:]
                accessibility.speak(f"{deleted_char} deleted")

        else:
            if len(event.unicode) > 0 and event.unicode.isprintable() and not is_ctrl:
                char = event.unicode
                if self.selection_anchor is not None and self.selection_anchor != self.cursor_pos:
                    temp_val, temp_pos = self.delete_selection(current_val)
                    current_val = temp_val
                    self.cursor_pos = temp_pos
                    self.selection_anchor = None
                
                target_dict[key] = current_val[:self.cursor_pos] + char + current_val[self.cursor_pos:]
                self.cursor_pos += 1
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
                self.start_editing()
            elif selection == "Back":
                self.change_state("MAIN")

        elif self.state == "HOST_CONFIG":
            if selection in ["Lobby Name", "Port", "Host Name"]:
                self.start_editing()
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
                self.start_editing()
            elif selection == "Connect": self.connect_private()
            elif selection == "Back": self.change_state("JOIN_SELECT")

        elif self.state == "JOIN_PUBLIC":
            if selection == "Back": self.change_state("JOIN_SELECT")
            elif selection == "Refresh": self.fetch_public_lobbies()
            elif selection == "Player Name": self.start_editing()
            elif selection.startswith("Lobby:"):
                try:
                    lobby_idx = self.selected_index - 2 
                    if 0 <= lobby_idx < len(self.public_lobbies):
                        lobby_data = self.public_lobbies[lobby_idx]
                        ip = lobby_data.get('ip', '127.0.0.1')
                        port = lobby_data.get('port', SERVER_PORT)
                        self.game.connect_to_server(ip, int(port))
                except Exception:
                    accessibility.speak("Error connecting to lobby.")

    def start_editing(self):
        target, key, val = self.get_active_config_target()
        if target is not None:
            self.editing = True
            pygame.key.set_repeat(400, 30)
            self.cursor_pos = len(val)
            self.selection_anchor = None
            accessibility.speak(f"Editing {key}. Type now.")

    def stop_editing(self):
        self.editing = False
        self.selection_anchor = None
        pygame.key.set_repeat(0)

    def change_state(self, new_state):
        self.state = new_state
        self.selected_index = 0
        self.stop_editing()
        self.announce_current_selection()

    def start_hosting(self):
        pygame.event.clear()
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
        pygame.event.clear()
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
                self.items["JOIN_PUBLIC"] = ["Player Name", "Refresh"] + lobby_items + ["Back"]
                accessibility.speak(self.public_lobby_status)
        except Exception as e:
            print(f"Spy Error: {e}")
            self.public_lobby_status = "Could not fetch lobbies."
            self.items["JOIN_PUBLIC"] = ["Player Name", "Refresh", "Back"]
            accessibility.speak("Could not reach Lobby Spy service.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.editing:
                self.handle_text_input(event)
            # --- MODIFIED: Handle Escape for navigation ---
            elif event.key == pygame.K_ESCAPE and self.state != "MAIN":
                self.change_state("MAIN")
            else:
                if event.key == pygame.K_UP: self.navigate(-1)
                elif event.key == pygame.K_DOWN: self.navigate(1)
                elif event.key == pygame.K_RETURN: self.select()
                # Remove Backspace nav, rely on Escape
                # elif event.key == pygame.K_BACKSPACE and self.state != "MAIN": pass 

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
            is_active = (i == self.selected_index and self.editing)
            
            val = ""
            if self.state == "HOST_CONFIG" and item_label in self.host_config:
                val = self.host_config[item_label]
                if item_label == "Public": val = "[X]" if val else "[ ]"
                display_text = f"{item_label}: {val}"
            elif self.state == "JOIN_PRIVATE" and item_label in self.join_private_config:
                val = self.join_private_config[item_label]
                display_text = f"{item_label}: {val}"
            elif self.state == "SETTINGS":
                if item_label == "Lobby Spy URL":
                    val = self.game.config.data['lobby_spy_url']
                    display_text = f"Lobby Spy: {val}"
                elif item_label == "Theme": display_text = f"Theme: {self.game.config.data['theme']}"
                elif item_label == "Speech Interrupt": display_text = f"Speech Interrupt: {'On' if self.game.config.data['speech_interrupt'] else 'Off'}"
                elif item_label == "Font Size": display_text = f"Font Size: {self.game.config.data['font_scale']}"
                elif item_label == "Fullscreen": display_text = f"Fullscreen: {'On' if self.game.config.data['fullscreen'] else 'Off'}"
                elif item_label == "Currency": display_text = f"Currency: {'Pounds' if self.game.config.data['currency'] == 'GBP' else 'Dollars'}"
            elif self.state == "JOIN_PUBLIC" and item_label == "Player Name":
                val = self.join_public_config[item_label]
                display_text = f"{item_label}: {val}"

            center_x = SCREEN_WIDTH // 2
            center_y = start_y + i * (font_main.get_height() + 10)

            if is_active:
                label_str = f"{item_label}: "
                if item_label == "Lobby Spy URL": label_str = "Lobby Spy: "
                label_surf = font_main.render(label_str, True, color)
                
                sel_start = self.cursor_pos
                sel_end = self.cursor_pos
                if self.selection_anchor is not None:
                    sel_start = min(self.selection_anchor, self.cursor_pos)
                    sel_end = max(self.selection_anchor, self.cursor_pos)

                pre_text = val[:sel_start]
                sel_text = val[sel_start:sel_end]
                post_text = val[sel_end:]

                pre_surf = font_main.render(pre_text, True, color)
                sel_surf = font_main.render(sel_text, True, colors["bg"])
                post_surf = font_main.render(post_text, True, color)

                cursor_rect_h = font_main.get_height()
                total_w = label_surf.get_width() + pre_surf.get_width() + sel_surf.get_width() + post_surf.get_width()
                start_x = center_x - (total_w // 2)

                self.screen.blit(label_surf, (start_x, center_y))
                current_x = start_x + label_surf.get_width()

                self.screen.blit(pre_surf, (current_x, center_y))
                current_x += pre_surf.get_width()

                if sel_text:
                    sel_rect = pygame.Rect(current_x, center_y, sel_surf.get_width(), cursor_rect_h)
                    pygame.draw.rect(self.screen, colors["highlight"], sel_rect)
                    self.screen.blit(sel_surf, (current_x, center_y))
                    current_x += sel_surf.get_width()
                
                self.screen.blit(post_surf, (current_x, center_y))
                
                if self.selection_anchor is None:
                    cursor_x = start_x + label_surf.get_width() + font_main.size(val[:self.cursor_pos])[0]
                    if pygame.time.get_ticks() % 1000 < 500:
                        pygame.draw.line(self.screen, color, (cursor_x, center_y), (cursor_x, center_y + cursor_rect_h), 2)
            else:
                item_surf = font_main.render(display_text, True, color)
                rect = item_surf.get_rect(center=(center_x, center_y))
                self.screen.blit(item_surf, rect)
        
        if self.state == "JOIN_PUBLIC":
            status_surf = font_small.render(self.public_lobby_status, True, colors["dim"])
            self.screen.blit(status_surf, (20, SCREEN_HEIGHT - 40))