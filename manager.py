import multiprocessing

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty, ListProperty, NumericProperty, StringProperty)
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

import data_caching, prompts, puzzleboard, score, strings, used_letters, values
from my_widgets import bind_keyboard, Fullscreenable

Builder.load_file(strings.file_kv_manager)

class SquareButton(Button):
    """
    A button with its width set to equal its height
    """
    
    pass

class CommQueue:
    """
    Contains two Queues named `a` and `b`.
    This way, a parent process can write to `a`
    and read from `b`, and the child process
    can do the opposite.
    """
    
    def __init__(self):
        self.a = multiprocessing.Queue()
        self.b = multiprocessing.Queue()

class PlayerButton(ButtonBehavior, score.ScoreLayout):
    """
    A ScoreLayout which also serves as a button
    to select a player.
    """
    
    def __init__(self, bg_color=(0, 0, 0, 1), **kwargs):
        super(PlayerButton, self).__init__(**kwargs)
        self.bg_color = bg_color

class ManagerLayout(BoxLayout, Fullscreenable):
    """
    A BoxLayout for the ManagerApp.
    """
    
    game = ListProperty([])
    puzzle_string = StringProperty('')
    seconds_left = NumericProperty(0)
    revealed = BooleanProperty(True)
    tossup_players_done = ListProperty([])
    final_spin_bonus = NumericProperty(0)
    
    def __init__(self, puzzle_queue, red_q, ylw_q, blu_q, letters_q, **kwargs):
        """Create the layout."""
        super(ManagerLayout, self).__init__(**kwargs)
        
        self.puzzle_queue = puzzle_queue
        self.red_q = red_q
        self.ylw_q = ylw_q
        self.blu_q = blu_q
        self.letters_q = letters_q
        
        self.selected_player = 0
        self.unavailable_letters = []
        self.tossup_running = False
        self.puzzle_clue = ''
        self.speedup_consonants_remaining = True
        self.consonants_remaining = True
        self.vowels_remaining = True
    
        self.load_settings()
        self.tossup_button.disabled = False
        
        self.bind_keyboard_self()
        
        if self.puzzle_queue:
            Clock.schedule_once(self.check_queue, values.queue_start)
    
    def on_touch_down(self, touch):
        """
        Detect a click/touch.
        If a TextInput is clicked, focus the TextInput.
        Otherwise, bind the keyboard to self.
        """
        
        self.text_input_clicked = False
        
        def filter(widget):
            for child in widget.children:
                if self.text_input_clicked:
                    break
                filter(child)
            if (
                    isinstance(widget, TextInput)
                    and widget.collide_point(*touch.pos)):
                self.text_input_clicked = True
        
        filter(self)
        
        if not self.text_input_clicked:
            self.bind_keyboard_self()
        
        return super(ManagerLayout, self).on_touch_down(touch)
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Check the keys pressed.
        If tab is pressed, target the first TextInput.
        If a letter is pressed with no modifiers,
        guess a letter.
        If a registered hotkey is detected,
        perform the associated action.
        """
        
        valid_hotkey_modifiers = ['ctrl', 'alt', 'shift']
        relevant_modifiers = [
            mod for mod in valid_hotkey_modifiers if mod in modifiers]
        
        letter = keycode[1]
        combination = '+'.join(relevant_modifiers + [letter])
        if letter == 'tab':
            self.name_input.focus = True
        elif (
                not relevant_modifiers
                and letter in strings.alphabet
                and self.selected_player != 0
                and self.get_value() != 0
                and self.game
                and self.game[0]['round_type'] not in [
                    strings.round_type_tossup,
                    strings.round_type_triple_tossup,
                    strings.round_type_triple_tossup_final,
                    strings.round_type_bonus]):
            self.guessed_letter(letter)
        elif combination == self.hotkeys.get('select_1'):
            self.select_red()
        elif combination == self.hotkeys.get('select_2'):
            self.select_yellow()
        elif combination == self.hotkeys.get('select_3'):
            self.select_blue()
        elif combination == self.hotkeys.get('select_next'):
            self.select_next_player()
        elif combination == self.hotkeys.get('select_puzzle'):
            self.choose_puzzle()
        elif combination == self.hotkeys.get('clear_puzzle'):
            self.clear_puzzle()
        elif combination == self.hotkeys.get('solve'):
            self.reveal_puzzle()
        elif combination == self.hotkeys.get('timer_start'):
            if self.game and self.game[0]['round_type'] in [
                    strings.round_type_tossup,
                    strings.round_type_triple_tossup,
                    strings.round_type_triple_tossup_final]:
                self.timer.start_stop_reset()
        elif combination == self.hotkeys.get('timer_reset'):
            if self.game and self.game[0]['round_type'] in [
                    strings.round_type_tossup,
                    strings.round_type_triple_tossup,
                    strings.round_type_triple_tossup_final]:
                self.timer.reset()
        elif combination == self.hotkeys.get('start_tossup'):
            self.tossup()
        elif combination == self.hotkeys.get('bonus_round'):
            self.bonus_round()
        elif not (
                self.game
                and self.game[0]['round_type'] in [
                    strings.round_type_tossup,
                    strings.round_type_triple_tossup,
                    strings.round_type_triple_tossup_final,
                    strings.round_type_bonus]):
            # following hotkeys cannot be used in a tossup
            if combination == self.hotkeys.get('lose_turn'):
                self.lose_turn()
            elif combination == self.hotkeys.get('bankrupt'):
                self.bankrupt()
            elif combination == self.hotkeys.get('bank_score'):
                self.bank_score()
    
    def _keyboard_closed(self):
        """Remove keyboard binding when the keyboard is closed."""
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def bind_keyboard_self(self, instance=None):
        """Bind the keyboard to self."""
        bind_keyboard(self)
    
    def check_queue(self, instance):
        """
        Check the queue for incoming commands.
        """
        
        try:
            command, args = self.puzzle_queue.b.get(block=False)
            if command == 'puzzle_loaded':
                self.puzzle_string = ' '.join(args['puzzle'].split())
                self.puzzle_clue = args['clue']
                self.show_puzzle()
            elif command == 'ding':
                if not self.timer.final_spin_started:
                    self.play_sound(strings.file_sound_ding)
            elif command == 'matches':
                self.correct_letter(args)
            elif command == 'tossup_timeout':
                self.revealed = True
                self.tossup()
            elif command == 'reveal_finished':
                if self.timer.final_spin_started:
                    Clock.schedule_once(
                        self.speedup_buzz,
                        values.speedup_timeout)
            elif command == 'no_more_consonants':
                if self.timer.final_spin_started:
                    self.speedup_consonants_remaining = False
                else:
                    self.no_more_consonants()
            elif command == 'no_more_vowels':
                self.no_more_vowels()
        except:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)
    
    def show_puzzle(self, instance=None):
        """
        Show the current puzzle
        (and clue, if any)
        in the `puzzle_label`.
        """
        
        if self.puzzle_string:
            self.puzzle_label.text = self.puzzle_string
            if self.puzzle_clue:
                self.puzzle_label.text += ('\n'
                    + strings.mgr_label_clue + self.puzzle_clue)
        else:
            self.puzzle_label.text = ''
    
    def check_eligible(self, player):
        """
        Before selecting a player,
        use this method to make sure that this player
        is eligible to take a turn.
        A player is ineligible during a toss-up if:
            the player already took a turn in this toss-up
            or
            another player is currently guessing
        """
        
        # True if the player already rang in on this toss-up
        already_rang = (player in self.tossup_players_done)
        
        # True if a tossup has been started but is currently paused.
        # This means another player has already rung in.
        not_my_turn = (self.tossup_players_done and not self.tossup_running)
        
        if already_rang or not_my_turn:
            return False
        return True
    
    def select_red(self):
        """
        Change the colors of TextInput boxes
        to indicate that the red player has been selected.
        """
        
        player = 1
        
        if self.check_eligible(player):
            self.selected_player = player
            self.selection_color(values.color_light_red)
            if self.btn_red.name:
                self.name_input.text = self.btn_red.name
            self.stop_all_flashing()
            self.red_q.put(('flash', None))
            self.letters_q.put(('flash', 'red', None))
            if self.tossup_running:
                self.tossup(player=self.selected_player)
            if (self.timer.final_spin_started
                    and not self.speedup_consonants_remaining):
                self.no_more_consonants()
    
    def select_yellow(self):
        """
        Change the colors of TextInput boxes
        to indicate that the yellow player has been selected.
        """
        
        player = 2
        
        if self.check_eligible(player):
            self.selected_player = player
            self.selection_color(values.color_light_yellow)
            if self.btn_ylw.name:
                self.name_input.text = self.btn_ylw.name
            self.stop_all_flashing()
            self.ylw_q.put(('flash', None))
            self.letters_q.put(('flash', 'yellow', None))
            if self.tossup_running:
                self.tossup(player=self.selected_player)
            if (self.timer.final_spin_started
                    and not self.speedup_consonants_remaining):
                self.no_more_consonants()
    
    def select_blue(self):
        """
        Change the colors of TextInput boxes
        to indicate that the blue player has been selected.
        """
        
        player = 3
        
        if self.check_eligible(player):
            self.selected_player = player
            self.selection_color(values.color_light_blue)
            if self.btn_blu.name:
                self.name_input.text = self.btn_blu.name
            self.stop_all_flashing()
            self.blu_q.put(('flash', None))
            self.letters_q.put(('flash', 'blue', None))
            if self.tossup_running:
                self.tossup(player=self.selected_player)
            if (self.timer.final_spin_started
                    and not self.speedup_consonants_remaining):
                self.no_more_consonants()
    
    def select_next_player(self):
        """
        Select the next player.
        """
        
        if self.selected_player == 1:
            # red selected, select yellow
            self.select_yellow()
        elif self.selected_player == 2:
            # yellow selected, select blue
            self.select_blue()
        else:
            # blue or no player selected, select red
            self.select_red()
    
    def deselect_player(self):
        """
        Deselect the selected player.
        """
        
        self.selected_player = 0
        self.selection_color(values.color_white)
        self.name_input.text = ''
        self.stop_all_flashing()
    
    def selection_color(self, color):
        """
        Change the color of TextInput boxes to the specified `color`.
        """
        
        self.name_input.background_color = color
        self.score_edit.background_color = color
        self.custom_value.background_color = color
    
    def update_name(self, text):
        """
        Update the name of the selected player.
        """
        
        if self.selected_player == 1:
            self.btn_red.name = text
            self.red_q.put(('name', text))
            self.letters_q.put(('name', 'red', text))
        elif self.selected_player == 2:
            self.btn_ylw.name = text
            self.ylw_q.put(('name', text))
            self.letters_q.put(('name', 'yellow', text))
        elif self.selected_player == 3:
            self.btn_blu.name = text
            self.blu_q.put(('name', text))
            self.letters_q.put(('name', 'blue', text))
    
    def get_score(self):
        """
        Get the score of the selected player.
        """
        
        if self.selected_player == 1:
            return self.btn_red.score
        elif self.selected_player == 2:
            return self.btn_ylw.score
        elif self.selected_player == 3:
            return self.btn_blu.score
        return 0
    
    def set_score(self, score):
        """
        Set the score of the selected player.
        """
        
        if self.selected_player == 1:
            self.btn_red.score = score
            self.red_q.put(('score', score))
            self.letters_q.put(('score', 'red', score))
        elif self.selected_player == 2:
            self.btn_ylw.score = score
            self.ylw_q.put(('score', score))
            self.letters_q.put(('score', 'yellow', score))
        elif self.selected_player == 3:
            self.btn_blu.score = score
            self.blu_q.put(('score', score))
            self.letters_q.put(('score', 'blue', score))
    
    def add_score(self, score):
        """
        Add `score` to the selected player's score.
        """
        
        self.set_score(self.get_score() + score)
    
    def get_total(self):
        """
        Get the game total of the selected player.
        """
        
        if self.selected_player == 1:
            return self.btn_red.total
        elif self.selected_player == 2:
            return self.btn_ylw.total
        elif self.selected_player == 3:
            return self.btn_blu.total
        return 0
    
    def set_total(self, total):
        """
        Set the game total of the selected player.
        """
        
        if self.selected_player == 1:
            self.btn_red.total = total
            self.red_q.put(('total', total))
            self.letters_q.put(('total', 'red', total))
        elif self.selected_player == 2:
            self.btn_ylw.total = total
            self.ylw_q.put(('total', total))
            self.letters_q.put(('total', 'yellow', total))
        elif self.selected_player == 3:
            self.btn_blu.total = total
            self.blu_q.put(('total', total))
            self.letters_q.put(('total', 'blue', total))
    
    def add_total(self, total):
        """
        Add `total` to the selected player's game total.
        """
        
        self.set_total(self.get_total() + total)
    
    def choose_puzzle(self):
        """
        Prompt the user to select a puzzle.
        """
        prompts.LoadGamePrompt(
                self.load_game,
                on_dismiss=self.bind_keyboard_self
            ).open()
    
    def load_game(self, game):
        """
        Load the game returned by a LoadGamePrompt.
        """
        
        self.game = game
        if game:
            self.load_puzzle(self.game[0]['puzzle'])
    
    def load_puzzle(self, puzzle):
        """
        Tell the layout to load `puzzle`.
        """
        
        if self.tossup_running:
            self.tossup()
        self.unavailable_letters = []
        self.puzzle_queue.a.put(('load', puzzle))
        self.letters_q.put(('reload', None, None))
        self.tossup_players_done = []
        self.consonants_remaining = True
        self.vowels_remaining = True
        self.speedup_consonants_remaining = True
        
        # consider revealed if the puzzleboard is clear
        self.revealed = True if not puzzle['puzzle'].split() else False
    
    def next_puzzle(self):
        """
        If there are still puzzles in the
        list `game`, load the next one.
        """
        
        try:
            self.game.pop(0)
            puzzle = self.game[0]
            
            if self.timer.final_spin_started:
                while puzzle['round_type'] == strings.round_type_speedup:
                    self.game.pop(0)
                    puzzle = self.game[0]
                self.timer.final_spin_started = False
            
            self.load_puzzle(puzzle['puzzle'])
        except IndexError:
            pass
    
    def clear_puzzle(self):
        """
        Clear the puzzleboard.
        """
        
        self.load_puzzle({
            'category': '',
            'clue': '',
            'puzzle': ' ' * 52})
    
    def tossup(self, player=None):
        """
        If there is no tossup in progress, start one.
        If there is a tossup in progress, pause it.
        If `player` is 1, 2, or 3,
        select that player.
        """
        
        if player:
            if player in self.tossup_players_done:
                return  
            self.tossup_players_done.append(player)
        
        if self.tossup_running:
            self.puzzle_queue.a.put(('pause_tossup', None))
            self.tossup_button.disabled = False
            
            if player == 1:
                self.select_red()
            elif player == 2:
                self.select_yellow()
            elif player == 3:
                self.select_blue()
        else:
            if set(self.tossup_players_done) == set([1, 2, 3]):
                return
            self.tossup_button.disabled = True
            self.puzzle_queue.a.put(('tossup', None))
            self.deselect_player()
        
        self.tossup_running = not self.tossup_running
    
    def stop_all_flashing(self):
        """
        Tell all ScoreApps to stop flashing.
        """
        
        self.red_q.put(('stop_flash', None))
        self.ylw_q.put(('stop_flash', None))
        self.blu_q.put(('stop_flash', None))
        self.letters_q.put(('stop_flash', 'red', None))
        self.letters_q.put(('stop_flash', 'yellow', None))
        self.letters_q.put(('stop_flash', 'blue', None))
    
    def reveal_puzzle(self, player_solved=True):
        """
        Tell the layout to reveal the puzzle.
        If `player_solved` is False, do not play
        the sounds indicating their success.
        """
        
        if player_solved:
            if self.game:
                round_type = self.game[0]['round_type']
                if round_type == strings.round_type_bonus:
                    self.play_sound(strings.file_sound_solve_bonus)
                elif round_type == strings.round_type_triple_tossup:
                    self.play_sound(strings.file_sound_solve_triple_tossup)
                elif round_type in [
                        strings.round_type_tossup,
                        strings.round_type_triple_tossup_final]:
                    self.play_sound(strings.file_sound_solve_tossup)
                    self.add_total(int(self.game[0]['round_reward']))
                else:
                    # not a tossup or bonus round,
                    # increase score if less than minimum prize
                    if self.get_score() < self.min_win:
                        self.set_score(self.min_win)
                    
                    if self.game[0]['puzzle']['clue']:
                        self.play_sound(strings.file_sound_solve_clue)
                    else:
                        self.play_sound(strings.file_sound_solve)
        self.puzzle_queue.a.put(('reveal', None))
        self.stop_all_flashing()
        
        self.revealed = True
    
    def solve_clue(self, player_solved):
        """
        If `player_solved` is True,
        add `clue_solve_reward` to the
        selected player's score, and play
        the 'clue correct' sound.
        Otherwise, play the buzzer sound.
        """
        
        if player_solved:
            self.add_score(self.clue_solve_reward)
            self.play_sound(strings.file_sound_clue_correct)
        else:
            self.play_sound(strings.file_sound_buzz)
    
    def guess_letter(self):
        """
        Open a prompt to select a letter.
        """
        
        if (
                self.selected_player == 0
                or self.get_value() == 0):
            return
        popup = prompts.ChooseLetterPrompt(
            self.guessed_letter,
            self.unavailable_letters,
            on_dismiss=self.bind_keyboard_self)
        popup.open()
        bind_keyboard(popup)
        popup.bind(on_dismiss=popup.release_keyboard)
    
    def guessed_letter(self, letter):
        """
        Pass the `letter` to the PuzzleLayout to check for matches.
        This runs after `guess_letter()` is called
        and a letter is chosen.
        """
        
        self.unavailable_letters.append(letter.lower())
        self.puzzle_queue.a.put(('letter', letter))
        self.letters_q.put(('remove_letter', None, letter))
    
    def buy_vowel(self):
        """
        If the player can afford a vowel,
        subtract `vowel_price` from their score.
        """
        
        if self.get_score() >= self.vowel_price:
            self.add_score(-self.vowel_price)
    
    def bonus_round_letters(self, letters):
        """
        Pass the list of selected letters to the puzzleboard,
        and remove them from the used letter board.
        """
        
        self.unavailable_letters.extend(letters)
        self.puzzle_queue.a.put(('bonus_round_letters', letters))
        self.letters_q.put(('remove_letters', None, letters))
    
    def get_value(self):
        """
        Get the value indicated by the custom cash value input box.
        If the box is empty, get the value
        indicated by the cash value spinner.
        """
        
        custom_value = self.custom_value.text
        if custom_value:
            return data_caching.str_to_int(custom_value)
        else:
            return sum([data_caching.str_to_int(number)
                for number in self.dropdown.text.split('+')])
    
    def correct_letter(self, match):
        """
        Adjust the selected player's score based on the number of matches.
        `match` is a tuple of the form (letter, number)
        indicating the letter and the number of matches.
        """
        
        letter, matches = match
        if letter.lower() not in 'aeiou':
            self.add_score(matches * self.get_value())
        self.custom_value.text = ''
        
        if not matches and not self.timer.final_spin_started:
            self.play_sound(strings.file_sound_buzz)
        
        # show number of matches in puzzle_label
        self.puzzle_label.text = strings.label_matches.format(
            letter=letter.upper(), matches=matches)
        # schedule to show the puzzle again
        Clock.schedule_once(self.show_puzzle, values.time_show_matches)
    
    def bonus_round(self):
        """
        Prompts the user to enter the contestant's
        letters for the bonus round.
        """
        
        prompts.BonusRoundPrompt(
                letters_callback=self.bonus_round_letters,
                solve_callback=self.reveal_puzzle,
                on_dismiss=self.bind_keyboard_self
            ).open()
    
    def no_more_consonants(self):
        """
        Play a sound indicating no more consonants,
        and remove consonants from letterboard.
        """
        
        # only do this once per round
        if self.consonants_remaining:
            self.consonants_remaining = False
            
            self.play_sound(strings.file_sound_no_more_consonants)
            
            self.unavailable_letters.extend([
                c for c in strings.alphabet if not c in 'aeiou'
                and not c in self.unavailable_letters])
            self.letters_q.put(('no_more_consonants', None, None))
    
    def no_more_vowels(self):
        """
        Play a sound indicating no more vowels,
        and remove vowels from letterboard.
        """
        
        # only do this once per round
        if self.vowels_remaining:
            self.vowels_remaining = False
            
            self.play_sound(strings.file_sound_no_more_vowels)
        
            self.unavailable_letters.extend([
                c for c in strings.alphabet if c in 'aeiou'
                and not c in self.unavailable_letters])
            self.letters_q.put(('no_more_vowels', None, None))
    
    def lose_turn(self):
        """
        Player has lost a turn;
        move to next player.
        """
        
        self.select_next_player()
    
    def bankrupt(self):
        """
        Bankrupt the selected player.
        """
        
        if self.selected_player:
            self.play_sound(strings.file_sound_bankrupt)
            self.set_score(0)
    
    def bank_score(self):
        """
        Add the selected player's score
        to their game total,
        then set each player's score to 0.
        """
        
        self.add_total(self.get_score())
        
        # set score = 0 for each player
        tmp = self.selected_player
        for i in range(1, 4):
            self.selected_player = i
            self.set_score(0)
        
        self.selected_player = tmp
    
    def cash_settings(self):
        """
        Open a Popup prompting the user
        to fill in some game settings.
        """
        
        popup = prompts.ManagerSettingsPrompt()
        popup.bind(on_dismiss=self.load_settings)
        popup.bind(on_dismiss=self.bind_keyboard_self)
        popup.open()
    
    def load_settings(self, instance=None):
        """
        Load settings from file.
        """
        
        settings = data_caching.get_variables()
        
        try:
            self.vowel_price = int(settings.get('vowel_price'))
        except (ValueError, TypeError):
            self.vowel_price = values.default_vowel_price
        
        try:
            self.min_win = int(settings.get('min_win'))
        except (ValueError, TypeError):
            self.min_win = values.default_min_win
        
        try:
            self.clue_solve_reward = int(settings.get('clue_solve_reward'))
        except (ValueError, TypeError):
            self.clue_solve_reward = values.default_clue_solve_reward
        
        try:
            self.final_spin_bonus = int(settings.get('final_spin_bonus'))
        except (ValueError, TypeError):
            self.final_spin_bonus = values.default_final_spin_bonus
        
        try:
            minutes, seconds = settings.get('timer_time', ':').split(':')
        except ValueError:
            minutes, seconds = (0, 0)
        minutes = data_caching.str_to_int(minutes)
        seconds = data_caching.str_to_int(seconds)
        self.timer.start_time = (minutes * 60) + seconds
        self.timer.seconds_left = self.timer.start_time
        
        self.dropdown.values = [strings.currency_format.format(value)
            for value in settings.get('cash_values', [])]
        
        self.hotkeys = {
            name: settings.get(name, default).lower()
            for name, default
            in zip(values.hotkey_names, values.hotkey_defaults)}
    
    def play_sound(self, filename):
        """
        Play the audio file specified by `filename`.
        """
        
        sound = SoundLoader.load(filename)
        if sound:
            sound.play()
    
    def speedup_buzz(self, instance):
        """
        Play the buzz sound.
        Does nothing if the puzzle has already been solved.
        """
        
        if self.timer.final_spin_started:
            self.play_sound(strings.file_sound_buzz)
    
    def update_dropdown(self):
        """
        Update the cash values dropdown
        so that it indicates if the
        final spin bonus is applied.
        """
        
        # this function will be called every time the text changes.
        # ignore_on_text is used to avoid recursion
        if not self.dropdown.ignore_on_text:
            self.dropdown.ignore_on_text = True
            
            text = self.dropdown.text
            values = self.dropdown.values
            bonus = self.dropdown.bonus_values
            
            if self.timer.final_spin_started:
                # final spin started; bonus should be shown
                try:
                    self.dropdown.text = bonus[values.index(text)]
                except ValueError:
                    # text not in values; bonus already shown
                    pass
            else:
                # final spin not started; bonus should not be shown
                try:
                    self.dropdown.text = values[bonus.index(text)]
                except ValueError:
                    # text not in bonus; bonus already not shown
                    pass
            
            self.dropdown.ignore_on_text = False
    
    def show_hide(self, widget, horizontal=True):
        """
        Toggle a widget's visibility by setting
        its size_hint_x to 0 or 1.
        Or, if `horizontal` is False,
        alter the size_hint_y instead.
        """
        
        def make_invisible(a, w):
            """
            Set the widget's opacity and width to 0.
            """
            
            if horizontal:
                widget.width = 0
            else:
                widget.height = 0
            widget.opacity = 0
        
        attr = 'size_hint_x' if horizontal else 'size_hint_y'
        
        # 1 if already hidden, 0 if shown
        val = 0 if getattr(widget, attr) else 1
        
        # animate widget until attr == val
        animation = Animation(**{attr: val}, d=0.5)
        
        if not val:
            animation.bind(on_complete=make_invisible)
        else:
            widget.opacity = 1
        
        animation.start(widget)
    
    def exit_app(self):
        """
        Tell all apps to stop, then stop this app.
        """
        
        self.exit_other_apps()
        App.get_running_app().stop()
    
    def exit_other_apps(self):
        """
        Tell all other apps to stop.
        """
        
        for q in [self.puzzle_queue.a, self.red_q, self.ylw_q, self.blu_q]:
            q.put(('exit', None))
        self.letters_q.put(('exit', None, None))

class ManagerApp(App):
    """
    An app to manage the PuzzleboardApp.
    """
    
    def __init__(self, *args, **kwargs):
        """Create the app."""
        super(ManagerApp, self).__init__(**kwargs)
        self.args = args
    
    def build(self):
        """Build the app."""
        return ManagerLayout(*self.args)
    
    def on_stop(self):
        """
        Close other apps when this app is closed.
        """
        
        self.root.exit_other_apps()

class ScoreApp(App):
    """
    An app showing a player's score.
    """
    
    def __init__(self, bg_color, queue, **kwargs):
        """Create the app."""
        super(ScoreApp, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.queue = queue
    
    def build(self):
        """Build the app."""
        return score.ScoreLayout(self.bg_color, queue=self.queue)

class LetterboardApp(App):
    """
    An app showing the available letters
    and players' scores.
    """
    
    def __init__(self, queue, **kwargs):
        """Create the app."""
        super(LetterboardApp, self).__init__(**kwargs)
        self.queue = queue
    
    def build(self):
        """Build the app."""
        return used_letters.LettersWithScore(queue=self.queue)

def launchManager(*args):
    """
    Launch a ManagerApp.
    """
    
    ManagerApp(*args).run()

def launchScore(*args):
    """
    Launch a ScoreApp.
    """
    
    ScoreApp(*args).run()

def launchLetterboard(*args):
    """
    Launch a LetterboardApp.
    """
    
    LetterboardApp(*args).run()

if __name__ == '__main__':
    puzzle_q = CommQueue()
    red_q = multiprocessing.Queue()
    ylw_q = multiprocessing.Queue()
    blu_q = multiprocessing.Queue()
    letters_q = multiprocessing.Queue()
    
    manager_process = multiprocessing.Process(
        target=launchManager,
        args=(puzzle_q, red_q, ylw_q, blu_q, letters_q))
    red = multiprocessing.Process(
        target=launchScore,
        args=(values.color_red, red_q))
    ylw = multiprocessing.Process(
        target=launchScore,
        args=(values.color_yellow, ylw_q))
    blu = multiprocessing.Process(
        target=launchScore,
        args=((values.color_blue, blu_q)))
    letters = multiprocessing.Process(
        target=launchLetterboard,
        args=(letters_q,))
    
    manager_process.start()
    red.start()
    ylw.start()
    blu.start()
    letters.start()
    
    puzzleboard.PuzzleboardApp(puzzle_q).run()
