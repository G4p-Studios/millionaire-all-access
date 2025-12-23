# gameplay.py

import pygame
import json
import time
import random
from settings import *
import accessible_output as accessibility

class Gameplay:
    def __init__(self, game):
        """
        Initializes the main gameplay screen.
        :param game: The main game object.
        """
        self.game = game
        self.screen = game.screen
        self.questions = []
        self.current_question_index = 0
        self.money_tree = MONEY_TREE
        
        # Lifeline Management
        self.lifelines = {"1: 50:50": True, "2: Phone a Friend": True, "3: Ask the Audience": True}
        self.answers_to_display = ['A', 'B', 'C', 'D']

        # Fonts
        self.question_font = pygame.font.Font(None, 64)
        self.answer_font = pygame.font.Font(None, 48)
        self.winnings_font = pygame.font.Font(None, 52)
        self.lifeline_font = pygame.font.Font(None, 40)

        self.load_questions()
        if self.questions:
            self.setup_new_question()

    def load_questions(self):
        """Loads questions from the questions.json file."""
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
        """
        Resets the state for a new question and then announces it.
        """
        if not self.questions or self.current_question_index >= len(self.questions) or self.current_question_index >= len(self.money_tree):
            winnings = self.money_tree[len(self.questions) - 1]
            accessibility.speak(f"Congratulations! You have answered all the questions and won {winnings}!")
            pygame.time.wait(2000)
            self.game.game_state = 'menu'
            return
        
        # Reset 50:50 effect for the new question
        self.answers_to_display = ['A', 'B', 'C', 'D']
        self.announce_question() # Announce the newly set up question

    def announce_question(self):
        """
        Announces the current question and the answers that are currently visible.
        This does NOT reset the 50:50 state.
        """
        q_data = self.questions[self.current_question_index]
        question_text = q_data['question']
        all_answers = q_data['answers']
        prize_money = self.money_tree[self.current_question_index]

        full_announcement = f"Question {self.current_question_index + 1} for {prize_money}. {question_text}. "
        
        # Only read the answers that are still available
        if 'A' in self.answers_to_display: full_announcement += f"A: {all_answers[0]}. "
        if 'B' in self.answers_to_display: full_announcement += f"B: {all_answers[1]}. "
        if 'C' in self.answers_to_display: full_announcement += f"C: {all_answers[2]}. "
        if 'D' in self.answers_to_display: full_announcement += f"D: {all_answers[3]}."
        
        accessibility.speak(full_announcement, interrupt=True)

    def handle_event(self, event):
        """Handles keyboard input for the gameplay screen."""
        if event.type == pygame.KEYDOWN:
            answer_key = None
            if event.key == pygame.K_a: answer_key = 'A'
            elif event.key == pygame.K_b: answer_key = 'B'
            elif event.key == pygame.K_c: answer_key = 'C'
            elif event.key == pygame.K_d: answer_key = 'D'
            elif event.key == pygame.K_r:
                # --- THIS IS THE FIX: Call the announce function, not the setup function ---
                accessibility.speak("Reading question again.")
                self.announce_question()
            elif event.key == pygame.K_w:
                self.walk_away()
            elif event.key == pygame.K_1: self.use_lifeline("1: 50:50")
            elif event.key == pygame.K_2: self.use_lifeline("2: Phone a Friend")
            elif event.key == pygame.K_3: self.use_lifeline("3: Ask the Audience")
            
            if answer_key:
                # Only allow answering if the option is visible
                if answer_key in self.answers_to_display:
                    self.check_answer(answer_key)
                else:
                    accessibility.speak(f"Option {answer_key} is not available.")

    def use_lifeline(self, name):
        """Central function to handle using a lifeline."""
        if self.lifelines.get(name):
            accessibility.speak(f"Using {name}.", interrupt=True)
            self.lifelines[name] = False
            pygame.time.wait(500)

            if name == "1: 50:50": self._use_fifty_fifty()
            elif name == "2: Phone a Friend": self._use_phone_a_friend()
            elif name == "3: Ask the Audience": self._use_ask_the_audience()
        else:
            accessibility.speak(f"You have already used the {name} lifeline.", interrupt=True)

    def _use_fifty_fifty(self):
        """Removes two incorrect answers."""
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        all_answers = ['A', 'B', 'C', 'D']
        incorrect_answers = [ans for ans in all_answers if ans != correct_answer]
        
        answer_to_keep = random.choice(incorrect_answers)
        self.answers_to_display = sorted([correct_answer, answer_to_keep])

        removed_options = [ans for ans in all_answers if ans not in self.answers_to_display]
        accessibility.speak(f"The computer has removed options {removed_options[0]} and {removed_options[1]}. The remaining options are {self.answers_to_display[0]} and {self.answers_to_display[1]}.")

    def _use_phone_a_friend(self):
        """Simulates the Phone a Friend lifeline."""
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        is_correct = random.random() > (self.current_question_index / 20)
        
        if is_correct:
            chosen_answer = correct_answer
        else:
            incorrect_answers = [ans for ans in ['A', 'B', 'C', 'D'] if ans != correct_answer]
            chosen_answer = random.choice(incorrect_answers)
        
        accessibility.speak(f"Your friend is thinking... they say they are pretty sure the answer is {chosen_answer}.")

    def _use_ask_the_audience(self):
        """Simulates the Ask the Audience lifeline."""
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
        """Handles the player choosing to walk away."""
        winnings = "nothing" if self.current_question_index == 0 else self.money_tree[self.current_question_index - 1]
        accessibility.speak(f"You have chosen to walk away with {winnings}. Congratulations!", interrupt=True)
        pygame.time.wait(2000)
        self.game.game_state = 'menu'

    def check_answer(self, selected_option):
        """Checks if the selected answer is correct."""
        correct_answer = self.questions[self.current_question_index]['correct_answer']
        
        if selected_option == correct_answer:
            winnings = self.money_tree[self.current_question_index]
            accessibility.speak(f"Correct! You have won {winnings}.", interrupt=True)
            pygame.time.wait(1000)
            self.current_question_index += 1
            self.setup_new_question() # Use the setup function to move to the next question
        else:
            accessibility.speak(f"Incorrect. The correct answer was {correct_answer}. Game over.", interrupt=True)
            pygame.time.wait(2000)
            self.game.game_state = 'menu'

    def draw(self):
        """Draws the game screen, including lifelines."""
        if not self.questions or self.current_question_index >= len(self.questions):
            return

        # Draw Winnings
        prize_money = self.money_tree[self.current_question_index]
        winnings_text = f"Question Value: {prize_money}"
        winnings_surface = self.winnings_font.render(winnings_text, True, (255, 255, 0))
        winnings_rect = winnings_surface.get_rect(center=(SCREEN_WIDTH / 2, 50))
        self.screen.blit(winnings_surface, winnings_rect)
        
        # Draw Question
        q_data = self.questions[self.current_question_index]
        question_text = q_data['question']
        question_surface = self.question_font.render(question_text, True, WHITE)
        question_rect = question_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
        self.screen.blit(question_surface, question_rect)

        # Draw Answers
        answers = q_data['answers']
        answer_labels = ['A', 'B', 'C', 'D']
        for i, label in enumerate(answer_labels):
            if label in self.answers_to_display:
                answer_text = f"{label}: {answers[i]}"
                answer_surface = self.answer_font.render(answer_text, True, WHITE)
                
                x_pos = SCREEN_WIDTH / 4 + (i % 2) * (SCREEN_WIDTH / 2)
                y_pos = SCREEN_HEIGHT / 2 + (i // 2) * 100
                
                answer_rect = answer_surface.get_rect(center=(x_pos, y_pos))
                self.screen.blit(answer_surface, answer_rect)
        
        # Draw Lifelines
        for i, (name, available) in enumerate(self.lifelines.items()):
            color = WHITE if available else (100, 100, 100)
            lifeline_surface = self.lifeline_font.render(name, True, color)
            lifeline_rect = lifeline_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100 + i * 30))
            self.screen.blit(lifeline_surface, lifeline_rect)