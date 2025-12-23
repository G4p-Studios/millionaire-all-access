# config.py

import json
import os
import pygame
from settings import *

CONFIG_FILE = "config.json"

class Config:
    def __init__(self):
        # Default Settings
        self.data = {
            "theme": "Standard",
            "speech_interrupt": True,
            "player_name": "Player 1",
            "fullscreen": False,
            "font_scale": "Normal",
            "lobby_spy_url": LOBBY_SPY_URL,
            "currency": "GBP" # Default to Pounds
        }
        self.fonts = {}
        self.load()
        self.update_colors()
        self.update_fonts()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    saved_data = json.load(f)
                    self.data.update(saved_data)
            except Exception as e:
                print(f"Could not load config: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Could not save config: {e}")

    def update_colors(self):
        if self.data["theme"] == "High Contrast":
            self.colors = {
                "bg": HC_BG,
                "text": HC_TEXT,
                "highlight": HC_HL,
                "dim": (100, 100, 100),
                "alert": (255, 255, 255)
            }
        else:
            self.colors = {
                "bg": STD_BG,
                "text": STD_TEXT,
                "highlight": STD_HL,
                "dim": (200, 200, 200),
                "alert": (255, 0, 0)
            }

    def update_fonts(self):
        scale_map = {"Normal": 1.0, "Large": 1.25, "Extra Large": 1.5}
        multiplier = scale_map.get(self.data["font_scale"], 1.0)
        def scale(size): return int(size * multiplier)

        self.fonts = {
            "title": pygame.font.Font(None, scale(BASE_FONT_TITLE)),
            "main": pygame.font.Font(None, scale(BASE_FONT_MAIN)),
            "small": pygame.font.Font(None, scale(BASE_FONT_SMALL)),
            "huge": pygame.font.Font(None, scale(BASE_FONT_HUGE))
        }

    # --- Toggles ---

    def toggle_theme(self):
        self.data["theme"] = "High Contrast" if self.data["theme"] == "Standard" else "Standard"
        self.update_colors()
        self.save()

    def toggle_interrupt(self):
        self.data["speech_interrupt"] = not self.data["speech_interrupt"]
        self.save()
    
    def toggle_fullscreen(self):
        self.data["fullscreen"] = not self.data["fullscreen"]
        self.save()

    def cycle_font_size(self):
        modes = ["Normal", "Large", "Extra Large"]
        current = self.data["font_scale"]
        try:
            idx = modes.index(current)
        except ValueError: idx = 0
        self.data["font_scale"] = modes[(idx + 1) % len(modes)]
        self.update_fonts()
        self.save()

    def toggle_currency(self):
        if self.data["currency"] == "GBP":
            self.data["currency"] = "USD"
        else:
            self.data["currency"] = "GBP"
        self.save()

    def get_money_tree(self):
        if self.data["currency"] == "USD":
            return MONEY_TREE_USD
        return MONEY_TREE_GBP