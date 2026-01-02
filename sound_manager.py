# sound_manager.py

import pygame
import os
from settings import SOUND_FILES

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
        self.load_sounds()

    def load_sounds(self):
        if not self.enabled: return
        
        sound_dir = "sounds"
        if not os.path.exists(sound_dir):
            try:
                os.makedirs(sound_dir)
            except: pass
            return

        for key, filename in SOUND_FILES.items():
            path = os.path.join(sound_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Could not load {filename}: {e}")
            else:
                print(f"Missing sound file: {path}")

    def play(self, key, loops=0):
        if not self.enabled: return
        if key in self.sounds:
            self.sounds[key].play(loops=loops)

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