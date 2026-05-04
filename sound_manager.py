# sound_manager.py

import pygame
import os
from settings import SOUND_FILES, SOUND_CATEGORIES, SOUND_SEARCH_PATHS

class SoundManager:
    def __init__(self):
        # Frequency, size, channels, buffer
        try:
            pygame.mixer.init(44100, -16, 2, 2048)
            self.enabled = True
        except Exception as e:
            print(f"Sound Error: {e}")
            self.enabled = False

        self.sounds = {}
        self.music_channel = None
        self.session_asset_root = None
        self.load_sounds()

    def load_sounds(self):
        if not self.enabled: return

        self.sounds = {}

        for root in SOUND_SEARCH_PATHS:
            try:
                os.makedirs(root, exist_ok=True)
            except Exception:
                pass

        if self.session_asset_root:
            try:
                os.makedirs(self.session_asset_root, exist_ok=True)
            except Exception:
                pass

        for key, filename in SOUND_FILES.items():
            path = self._resolve_sound_path(key, filename)
            if path and os.path.exists(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Could not load {path}: {e}")
            else:
                print(f"Missing sound file for {key}: {filename}")

    def _resolve_sound_path(self, key, filename):
        category = SOUND_CATEGORIES.get(key)
        candidates = []

        if self.session_asset_root:
            if category:
                candidates.append(os.path.join(self.session_asset_root, category, filename))
            candidates.append(os.path.join(self.session_asset_root, filename))

        for root in SOUND_SEARCH_PATHS:
            if category:
                candidates.append(os.path.join(root, category, filename))
            candidates.append(os.path.join(root, filename))

        for path in candidates:
            if os.path.exists(path):
                return path

        return None

    def set_session_asset_root(self, path):
        self.session_asset_root = path
        self.load_sounds()

    def play(self, key, loops=0):
        if not self.enabled: return
        if key in self.sounds:
            self.sounds[key].play(loops=loops)

    def play_ui(self, key, fallback_key=None):
        if not self.enabled:
            return
        if key in self.sounds:
            self.sounds[key].play()
            return
        if fallback_key and fallback_key in self.sounds:
            self.sounds[fallback_key].play()

    def play_music(self, key, loops=-1):
        if not self.enabled: return
        if self.music_channel:
            self.music_channel.stop()

        if key in self.sounds:
            self.music_channel = self.sounds[key].play(loops=loops)

    def stop_music(self):
        if self.music_channel:
            self.music_channel.stop()
            self.music_channel = None

    def stop_all(self):
        if self.enabled:
            pygame.mixer.stop()

    def get_length(self, key):
        """Returns the length of the sound in seconds. Returns 0 if not found."""
        if self.enabled and key in self.sounds:
            return self.sounds[key].get_length()
        return 0