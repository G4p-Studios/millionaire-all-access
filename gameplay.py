# gameplay.py

import pygame
import json
import time
import random
from settings import *
import accessible_output as accessibility

class Gameplay:
    def __init__(self, game):
        pygame.key.set_repeat(0)
        self.game = game
        self.screen = game.screen
        self.questions = []
        self.current_question_index = 0
        self.money_tree = self.game.config.get_money_tree()
        self.lifelines = {"1: 50:50": True, "2: Phone a Friend": True, "3: Ask the Audience": True}
        self.answers_to_display = ['A', 'B', 'C', 'D']
        
        # State Management for Answering
        self.selected_answer = None 
        self.is_locked_in = False   
        
        self.load_questions()
        if self.questions:
            self.setup_new_question()

    def load_questions(self):
        try:
            with open('questions.json', 'r') as f:
                self.questions = json.load(f)
            if not self.questions:
                accessibility.speak("Error: Question file is empty. Returning to menu.")
                self.game.game_state = 'menu'
        except FileNotFoundError:
            accessibility.speak("Error: questions.json file not found. Returning to menu.")
            self.game.game_state = 'menu'
        except json.JSONDecodeError:
            accessibility.speak("Error: Could not read the questions.json file. Returning to menu.")
            self.game.game_state = 'menu'

    def setup_new_question(self):
        pygame.event.clear()
        
        # Reset Answer State
        self.selected_answer = None
        self.is_locked_in = False
        self.answers_to_display = ['A', 'B', 'C', 'D']
        
        if not self.questions or self.current_question_index >= len(self.questions) or self.current_question_index >= len(self.money_tree):
            winnings = self.money_tree[len(self.questions) - 1]
            self.game.sounds.play("win_14")
            duration = self.game.sounds.get_length("win_14")
            pygame.time.wait(int(duration * 1000) + 500)
            accessibility.speak(f"Congratulations! You have answered all the questions and won {winnings}!")
            pygame.time.wait(2000)
            self.game.game_state = 'menu'
            return
        
        # --- BACKGROUND MUSIC LOGIC ---
        idx = self.current_question_index
        if idx < 5:
            self.game.sounds.play_music("q_bed_1_5")
        elif idx == 5: self.game.sounds.play_music("q_bed_6")
        elif idx == 6: self.game.sounds.play_music("q_bed_7")
        elif idx == 7: self.game.sounds.play_music("q_bed_8")
        elif idx == 8: self.game.sounds.play_music("q_bed_9")
        elif idx == 9: self.game.sounds.play_music("q_bed_10")
        elif idx == 10: self.game.sounds.play_music("q_bed_11")
        elif idx == 11: self.game.sounds.play_music("q_bed_12")
        elif idx == 12: self.game.sounds.play_music("q_bed_13")
        elif idx == 13: self.game.sounds.play_music("q_bed_14")
        elif idx == 14: self.game.sounds.play_music("q_bed_15")
            
        self.announce_question()

    def announce_question(self):
        q_data = self.questions[self.current_question_index]
        question_text = q_data['question']
        all_answers = q_data['answers']
        prize_money = self.money_tree[self.current_question_index]
        full_announcement = f"Question {self.current_question_index + 1} for {prize_money}. {question_text}. "
        if 'A' in self.answers_to_display: full_announcement += f"A: {all_answers[0]}. "
        if 'B' in self.answers_to_display: full_announcement += f"B: {all_answers[1]}. "
        if 'C' in self.answers_to_display: full_announcement += f"C: {all_answers[2]}. "
        if 'D' in self.answers_to_display: full_announcement += f"D: {all_answers[3]}."
        
        should_interrupt = self.game.config.data["speech_interrupt"]
        accessibility.speak(full_announcement, interrupt=should_interrupt)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # 1. LOCKED IN STATE: Waiting for Host Reveal
            if self.is_locked_in:
                if event.key == pygame.K_RETURN:
                    self.reveal_answer()
                return 

            # 2. NORMAL GAMEPLAY
            answer_key = None
            if event.key == pygame.K_a: answer_key = 'A'
            elif event.key == pygame.K_b: answer_key = 'B'
            elif event.key == pygame.K_c: answer_key = 'C'
            elif event.key == pygame.K_d: answer_key = 'D'
            
            if answer_key:
                if answer_key not in self.answers_to_display:
                    accessibility.speak(f"Option {answer_key} is not available.")
                else:
                    # Index 5 is the 2,000 question.
                    if self.current_question_index < 5:
                        self.selected_answer = answer_key
                        self.reveal_answer() # Instant
                    else:
                        if self.selected_answer == answer_key:
                            self.lock_in_answer(answer_key)
                        else:
                            self.select_answer(answer_key)
            
            elif event.key == pygame.K_r:
                accessibility.speak("Reading question again.")
                self.announce_question()
            elif event.key == pygame.K_w: 
                self.walk_away()
            elif event.key == pygame.K_1: self.use_lifeline("1: 50:50")
            elif event.key == pygame.K_2: self.use_lifeline("2: Phone a Friend")
            elif event.key == pygame.K_3: self.use_lifeline("3: Ask the Audience")

    def select_answer(self, option):
        self.selected_answer = option
        accessibility.speak(f"{option} Selected. Press {option} again to lock in.")

    def lock_in_answer(self, option):
        self.is_locked_in = True
        self.game.sounds.stop_music()
        
        idx = self.current_question_index
        sound_key = None
        
        # 2k or 64k
        if idx == 5 or idx == 10: sound_key = "final_answer_5"
        # 4k or 125k
        elif idx == 6 or idx == 11: sound_key = "final_answer_6"
        # 8k or 250k
        elif idx == 7 or idx == 12: sound_key = "final_answer_7"
        # 16k or 500k
        elif idx == 8 or idx == 13: sound_key = "final_answer_8"
        # 32k or 1M
        elif idx == 9 or idx == 14: sound_key = "final_answer_9"
        else: sound_key = "final_answer" 
        
        if sound_key:
            self.game.sounds.play(sound_key)
        
        accessibility.speak(f"{option} Locked In. Waiting for result.", interrupt=True)

    def reveal_answer(self):
        """Resolves the question."""
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        
        self.game.sounds.stop_music() 
        self.game.sounds.stop_all() 

        if self.selected_answer == correct_answer:
            sound_key = f"win_{self.current_question_index}"
            self.game.sounds.play(sound_key)
            
            duration = self.game.sounds.get_length(sound_key)
            wait_ms = int(duration * 1000) + 500
            
            pygame.time.wait(wait_ms)
            
            winnings = self.money_tree[self.current_question_index]
            accessibility.speak(f"Correct! You have won {winnings}.", interrupt=True)
            
            pygame.time.wait(1000)
            pygame.event.clear()
            self.current_question_index += 1
            self.setup_new_question() 
        else:
            sound_key = f"lose_{self.current_question_index}"
            self.game.sounds.play(sound_key)
            
            duration = self.game.sounds.get_length(sound_key)
            wait_ms = int(duration * 1000) + 500
            pygame.time.wait(wait_ms)
            
            accessibility.speak(f"Incorrect. The correct answer was {correct_answer}. Game over.", interrupt=True)
            pygame.time.wait(2000)
            self.game.game_state = 'menu'

    def use_lifeline(self, name):
        if self.is_locked_in:
            accessibility.speak("Cannot use lifelines after locking in.")
            return

        if self.lifelines.get(name):
            self.game.sounds.play("lifeline")
            accessibility.speak(f"Using {name}.", interrupt=True)
            self.lifelines[name] = False
            pygame.time.wait(1000)
            pygame.event.clear()
            
            if name == "1: 50:50": self._use_fifty_fifty()
            elif name == "2: Phone a Friend": self._use_phone_a_friend()
            elif name == "3: Ask the Audience": self._use_ask_the_audience()
        else:
            accessibility.speak(f"You have already used the {name} lifeline.", interrupt=True)

    def _use_fifty_fifty(self):
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        all_answers = ['A', 'B', 'C', 'D']
        incorrect_answers = [ans for ans in all_answers if ans != correct_answer]
        answer_to_keep = random.choice(incorrect_answers)
        self.answers_to_display = sorted([correct_answer, answer_to_keep])
        removed_options = [ans for ans in all_answers if ans not in self.answers_to_display]
        accessibility.speak(f"The computer has removed options {removed_options[0]} and {removed_options[1]}. The remaining options are {self.answers_to_display[0]} and {self.answers_to_display[1]}.")

    def _use_phone_a_friend(self):
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        is_correct = random.random() > (self.current_question_index / 20)
        if is_correct: chosen_answer = correct_answer
        else:
            incorrect_answers = [ans for ans in ['A', 'B', 'C', 'D'] if ans != correct_answer]
            chosen_answer = random.choice(incorrect_answers)
        accessibility.speak(f"Your friend is thinking... they say they are pretty sure the answer is {chosen_answer}.")

    def _use_ask_the_audience(self):
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        percentages = [0, 0, 0, 0]
        correct_vote = 40 + random.randint(0, 30)
        percentages[ord(correct_answer) - ord('A')] = correct_vote
        remaining_vote = 100 - correct_vote
        p1 = random.randint(0, remaining_vote)
        p2 = random.randint(0, remaining_vote - p1)
        p3 = remaining_vote - p1 - p2
        temp_percentages = sorted([p1, p2, p3], reverse=True)
        idx = 0
        for i in range(4):
            if i != (ord(correct_answer) - ord('A')):
                percentages[i] = temp_percentages[idx]
                idx += 1
        announcement = f"The audience results are: A {percentages[0]}%, B {percentages[1]}%, C {percentages[2]}%, D {percentages[3]}%."
        accessibility.speak(announcement)

    def walk_away(self):
        winnings = "nothing" if self.current_question_index == 0 else self.money_tree[self.current_question_index - 1]
        self.game.sounds.stop_music()
        self.game.sounds.play("walk_away")
        duration = self.game.sounds.get_length("walk_away")
        pygame.time.wait(int(duration * 1000) + 500)
        accessibility.speak(f"You have chosen to walk away with {winnings}. Congratulations!", interrupt=True)
        pygame.time.wait(2000)
        self.game.game_state = 'menu'

    def draw(self):
        if not self.questions or self.current_question_index >= len(self.questions): return

        colors = self.game.config.colors
        font_main = self.game.config.fonts["main"]
        font_title = self.game.config.fonts["title"]
        font_small = self.game.config.fonts["small"]

        prize_money = self.money_tree[self.current_question_index]
        winnings_text = f"Question Value: {prize_money}"
        winnings_surface = font_title.render(winnings_text, True, colors["highlight"])
        winnings_rect = winnings_surface.get_rect(center=(SCREEN_WIDTH / 2, 50))
        self.screen.blit(winnings_surface, winnings_rect)
        
        q_data = self.questions[self.current_question_index]
        question_text = q_data['question']
        question_surface = font_title.render(question_text, True, colors["text"])
        question_rect = question_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
        self.screen.blit(question_surface, question_rect)

        answers = q_data['answers']
        answer_labels = ['A', 'B', 'C', 'D']
        for i, label in enumerate(answer_labels):
            if label in self.answers_to_display:
                answer_text = f"{label}: {answers[i]}"
                
                # --- COLOR LOGIC ---
                text_color = colors["text"]
                if self.is_locked_in and label == self.selected_answer:
                    text_color = STD_SEL if self.game.config.data["theme"] == "Standard" else HC_SEL
                elif label == self.selected_answer:
                    text_color = colors["highlight"]

                answer_surface = font_main.render(answer_text, True, text_color)
                x_pos = SCREEN_WIDTH / 4 + (i % 2) * (SCREEN_WIDTH / 2)
                y_pos = SCREEN_HEIGHT / 2 + (i // 2) * 150
                answer_rect = answer_surface.get_rect(center=(x_pos, y_pos))
                self.screen.blit(answer_surface, answer_rect)
        
        for i, (name, available) in enumerate(self.lifelines.items()):
            color = colors["text"] if available else colors["dim"]
            lifeline_surface = font_small.render(name, True, color)
            lifeline_rect = lifeline_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100 + i * 40))
            self.screen.blit(lifeline_surface, lifeline_rect)