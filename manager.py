import multiprocessing
import queue

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty, ListProperty, NumericProperty, StringProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

import data_caching
import prompts
import puzzleboard
import score
import strings
import used_letters
import values
from my_widgets import Fullscreenable, KeyboardBindable

Builder.load_file(values.file_kv_manager)


class ManagerLayout(BoxLayout, Fullscreenable, KeyboardBindable):
    """
    The root layout for the manager app.
    """

    game = ListProperty([])
    puzzle_string = StringProperty('')
    revealed = BooleanProperty(True)
    tossup_players_done = ListProperty([])
    final_spin_bonus = NumericProperty(0)
    selected_player = NumericProperty(0)
    matches = NumericProperty(0)

    def __init__(
            self, puzzle_queue_out, puzzle_queue_in,
            red_q, ylw_q, blu_q, letters_q, **kwargs):
        """
        Create the layout.

        :param puzzle_queue_out: Queue to send information to the
                                 puzzleboard
        :type puzzle_queue_out: multiprocessing.Queue
        :param puzzle_queue_in: Queue to receive information from the
                                puzzleboard
        :type puzzle_queue_in: multiprocessing.Queue
        :param red_q: Queue to use for the 1st scoreboard
        :type red_q: multiprocessing.Queue
        :param ylw_q: Queue to use for the 2nd scoreboard
        :type ylw_q: multiprocessing.Queue
        :param blu_q: Queue to use for the 3rd scoreboard
        :type blu_q: multiprocessing.Queue
        :param letters_q: Queue to use for the used letters board
        :type letters_q: multiprocessing.Queue
        :param kwargs: Additional keyword arguments for the layout
        :return: None
        """

        super(ManagerLayout, self).__init__(**kwargs)

        self.puzzle_queue_out = puzzle_queue_out
        self.puzzle_queue_in = puzzle_queue_in
        self.red_q = red_q
        self.ylw_q = ylw_q
        self.blu_q = blu_q
        self.letters_q = letters_q

        self.unavailable_letters = []
        self.tossup_running = False
        self.tossup_sound = SoundLoader.load(values.file_sound_tossup)
        self.puzzle_clue = ''
        self.speedup_consonants_remaining = True
        self.consonants_remaining = True
        self.vowels_remaining = True
        self.tiebreaker_started = False
        self.tie_resolved = False

        self.vowel_price = 0
        self.min_win = 0
        self.clue_solve_reward = 0
        self.hotkeys = {}

        self.load_settings()
        self.tossup_button.disabled = False

        self.get_keyboard()

        if self.puzzle_queue_in:
            Clock.schedule_once(self.check_queue, values.queue_start)

        App.get_running_app().bind(on_stop=self.exit_other_apps)

    def on_touch_down(self, touch):
        """
        Detect a click/touch.
        If a TextInput is clicked, focus the TextInput.
        Otherwise, bind the keyboard to self.

        :param touch: A touch down event
        :type touch: kivy.input.motionevent.MotionEvent
        :return: True if the touch was consumed, otherwise False
        :rtype: bool
        """

        def filter_children(widget):
            """
            Check a widget and its children for TextInput widgets that
            correspond with the position of the touch.

            :param widget: A Widget
            :type widget: kivy.uix.widget.Widget
            :return: True if a TextInput is found, otherwise False
            :rtype: bool
            """

            if (
                    isinstance(widget, TextInput)
                    and widget.collide_point(*touch.pos)):
                return True
            else:
                for child in widget.children:
                    if filter_children(child):
                        return True
                return False

        if not filter_children(self):
            self.get_keyboard()

        return super(ManagerLayout, self).on_touch_down(touch)

    def _on_keyboard_down(self, _keyboard, keycode, _text, modifiers):
        """
        Check keys entered on the keyboard.
        If tab is pressed, target the first TextInput.
        If a letter is pressed with no modifiers, guess a letter.
        If a registered hotkey is detected, perform the associated
        action.

        :param _keyboard: A Keyboard
        :type _keyboard: kivy.core.window.Keyboard
        :param keycode: An integer and a string representing the keycode
        :type keycode: tuple
        :param _text: The text of the pressed key
        :type _text: str
        :param modifiers: A list of modifiers
        :type modifiers: list
        :return: True if key was handled, otherwise False
        :rtype: bool
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
                and (self.get_value() is not None
                     or letter in strings.vowels)
                and self.game
                and self.game[0]['round_type'] not in [
                    strings.round_type_tossup,
                    strings.round_type_triple_tossup,
                    strings.round_type_triple_tossup_final,
                    strings.round_type_bonus]):
            self.guessed_letter(letter)
        elif combination == self.hotkeys.get('select_1'):
            self.select_player(1)
        elif combination == self.hotkeys.get('select_2'):
            self.select_player(2)
        elif combination == self.hotkeys.get('select_3'):
            self.select_player(3)
        elif combination == self.hotkeys.get('select_next'):
            self.select_player((self.selected_player % 3) + 1)
        elif combination == self.hotkeys.get('increase_score'):
            self.increase_score()
        elif combination == self.hotkeys.get('select_puzzle'):
            self.choose_puzzle()
        elif combination == self.hotkeys.get('clear_puzzle'):
            self.clear_puzzle()
        elif combination == self.hotkeys.get('solve'):
            if self.select_layout_manager.current == 'select':
                self.choose_puzzle()
            elif self.select_layout_manager.current == 'next':
                self.next_puzzle()
            elif self.select_layout_manager.current == 'clue':
                self.solve_clue(True)
                self.select_layout_manager.clue_solved = True
            else:
                self.reveal_puzzle()
        elif (
                combination == self.hotkeys.get('timer_start')
                and self.game
                and self.game[0]['round_type'] == strings.round_type_speedup):
            self.timer.start_stop_reset()
        elif (
                combination == self.hotkeys.get('timer_reset')
                and self.game
                and self.game[0]['round_type'] == strings.round_type_speedup):
            self.timer.reset()
        elif combination == self.hotkeys.get('start_tossup'):
            if (
                    self.puzzle_string
                    and not self.tossup_button.disabled
                    and self.game
                    and self.game[0]['round_type'] in [
                        strings.round_type_tossup,
                        strings.round_type_triple_tossup,
                        strings.round_type_triple_tossup_final]):
                self.tossup()
            elif (
                    self.timer.current == 'timeout'
                    and self.game
                    and self.game[0]['round_type']
                    == strings.round_type_speedup):
                self.timer.final_spin_started = True
                self.timer.start_stop_reset()
        elif combination == self.hotkeys.get('buzzer'):
            if self.select_layout_manager.current == 'solve?':
                self.reveal_puzzle(False)
            elif self.select_layout_manager.current == 'clue':
                self.solve_clue(False)
                self.select_layout_manager.clue_solved = True
            else:
                self.play_sound(values.file_sound_buzz)
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
            elif combination == self.hotkeys.get('buy_vowel'):
                self.buy_vowel()
            elif combination == self.hotkeys.get('bank_score'):
                self.bank_score()
            else:
                return False
        else:
            return False
        return True

    def check_queue(self, _dt):
        """
        Check the queue for incoming commands to execute.

        Each command in the queue should be a tuple of the form:

        (command_string, args)

        Available commands are:

        'puzzle_loaded':
            Display the puzzle in the layout.
            *args* is a puzzle dict.
            See :func:`data_caching.add_puzzle` for a description of
            puzzle dicts.
        'ding':
            Play a 'ding' sound (as a panel turns blue). Does nothing if
            it is currently the speed-up round.
            *args* is ignored.
        'matches':
            Display the number of matches for a letter.
            *args* is a tuple consisting of a single-character string
            and the number of matches.
        'tossup_timeout':
            Indicate that time is up for solving a toss-up
            *args* is ignored.
        'reveal_finished':
            Schedule a buzzer to play when a player runs out of time to
            solve the puzzle in a speed-up round. Does nothing if it is
            not the speed-up round. The amount of time before the buzzer
            sound plays is defined by `values.speedup_timeout`.
            *args* is ignored.
        'no_more_consonants':
            Play a sound indicating that no consonants remain. If it is
            currently the speed-up round, this sound is postponed until
            the next player's turn.
            *args* is ignored.
        'no_more_vowels':
            Play a sound indicating that no vowels remain.
            *args* is ignored.

        :param _dt: The time elapsed between scheduling and calling
        :type _dt: float
        :return: None
        """

        try:
            command, args = self.puzzle_queue_in.get(block=False)
            if command == 'puzzle_loaded':
                self.puzzle_string = ' '.join(args['puzzle'].split())
                if self.puzzle_string:
                    self.tie_resolved = False
                self.puzzle_clue = args['clue']
                self.display_puzzle()
            elif command == 'ding':
                if not self.timer.final_spin_started:
                    self.play_sound(values.file_sound_ding)
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
        except queue.Empty:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)

    def display_puzzle(self, _dt=None):
        """
        Show the current puzzle (and clue, if any) in the
        `puzzle_label`.

        :param _dt: The time elapsed between scheduling and calling,
                    defaults to None
        :type _dt: float, optional
        :return: None
        """

        if self.puzzle_string:
            self.puzzle_label.text = self.puzzle_string
            if self.puzzle_clue:
                self.puzzle_label.text += (
                        '\n' + strings.label_manager_clue + self.puzzle_clue)
        else:
            self.puzzle_label.text = ''

    def select_player(self, player_number):
        """
        Select the player indicated by `player_number`.
        If `player_number` is not 1, 2, or 3, deselect all players.
        If the player is ineligible to take a turn, do nothing.

        :param player_number: The number of the player
        :type player_number: int
        :return: None
        """

        if player_number == 1:
            color, button, q = 'red', self.btn_red, self.red_q
        elif player_number == 2:
            color, button, q = 'yellow', self.btn_ylw, self.ylw_q
        elif player_number == 3:
            color, button, q = 'blue', self.btn_blu, self.blu_q
        else:
            # deselect
            self.selected_player = 0
            self.name_input.text = ''
            self.stop_all_flashing()
            return

        # True if the player already rang in on this toss-up
        already_rang = (player_number in self.tossup_players_done)
        # True if a tossup has been started but is currently paused.
        # This means another player has already rung in.
        not_my_turn = (self.tossup_players_done and not self.tossup_running)
        if already_rang or not_my_turn:
            # player is ineligible
            return

        self.selected_player = player_number
        self.name_input.text = button.name
        self.stop_all_flashing()
        q.put(('flash', None))
        self.letters_q.put(('flash', color, None))
        if self.tossup_running:
            self.tossup(player=self.selected_player)
        if (
                self.timer.final_spin_started
                and not self.speedup_consonants_remaining):
            self.no_more_consonants()

    def select_winner(self):
        """
        Select a player to proceed to the bonus round, then set the
        layout to bonus round mode.

        :return: None
        """

        max_score = 0
        winning_players = []

        tmp = self.selected_player
        for player_index in range(1, 4):
            self.selected_player = player_index
            total = self.get_total()
            if total > max_score:
                max_score = total
                winning_players = [player_index]
            elif total == max_score:
                winning_players.append(player_index)
        self.selected_player = tmp

        def load_tiebreaker(puzzle):
            """
            Load a puzzle dict as a tiebreaker toss-up.

            `puzzle` is a puzzle dict.
            See :func:`data_caching.add_puzzle` for a description of
            puzzle dicts.

            :param puzzle: A puzzle dict
            :type puzzle: dict
            :return: None
            """

            self.tiebreaker_started = True
            game_round = {
                'round_type': strings.round_type_tossup,
                'round_reward': 0,
                'puzzle': puzzle}
            self.game = [game_round] + self.game
            self.load_puzzle(puzzle)
            self.tossup_players_done = [
                i for i in range(1, 4) if i not in winning_players]

        def winner_chosen(i):
            """
            Declare player `i`
            as the winner.

            :param i: The player number
            :type i: int
            :return: None
            """

            self.select_player(i)
            self.load_puzzle(self.game[0]['puzzle'])

        if len(winning_players) > 1:
            if not self.tie_resolved:
                prompts.TiebreakerPrompt(
                    load_tiebreaker, winner_chosen, winning_players,
                    player_names=[btn.name for btn in (
                        self.btn_red, self.btn_ylw, self.btn_blu)]
                ).open()
            else:
                # proceed to bonus round with selected player
                self.load_puzzle(self.game[0]['puzzle'])
        else:
            winner_chosen(winning_players[0])

    def update_name(self, text):
        """
        Update the name of the selected player.

        :param text: A name for the player
        :type text: str
        :return: None
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
        Returns 0 if no player is selected.

        :return: The player's score
        :rtype: int
        """

        if self.selected_player == 1:
            return self.btn_red.score
        elif self.selected_player == 2:
            return self.btn_ylw.score
        elif self.selected_player == 3:
            return self.btn_blu.score
        return 0

    def set_score(self, new_score):
        """
        Set the score of the selected player.

        :param new_score: The new score
        :type new_score: int
        :return: None
        """

        if self.selected_player == 1:
            self.btn_red.score = new_score
            self.red_q.put(('score', new_score))
            self.letters_q.put(('score', 'red', new_score))
        elif self.selected_player == 2:
            self.btn_ylw.score = new_score
            self.ylw_q.put(('score', new_score))
            self.letters_q.put(('score', 'yellow', new_score))
        elif self.selected_player == 3:
            self.btn_blu.score = new_score
            self.blu_q.put(('score', new_score))
            self.letters_q.put(('score', 'blue', new_score))

    def add_score(self, new_score):
        """
        Add `new_score` to the selected player's score.

        :param new_score: The number to be added
        :type new_score: int
        :return: None
        """

        self.set_score(self.get_score() + new_score)

    def get_total(self):
        """
        Get the game total of the selected player.
        Returns 0 if no player is selected.

        :return: The player's total
        :rtype: int
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

        :param total: The player's new total
        :type total: int
        :return: None
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

        :param total: The number to be added
        :type total: int
        :return: None
        """

        self.set_total(self.get_total() + total)

    def reset_scores(self):
        """
        Reset all players' scores and game totals.

        :return: None
        """

        for i in range(1, 4):
            self.selected_player = i
            self.set_score(0)
            self.set_total(0)

        self.select_player(0)

    def choose_puzzle(self):
        """
        Prompt the user to select a puzzle.

        :return: None
        """

        prompts.LoadGamePrompt(
            self.load_game,
            on_dismiss=lambda i: self.get_keyboard()
        ).open()

    def load_game(self, game):
        """
        Load a game. See :func:`data_caching.export_game` for a
        description of game lists.

        :param game: A game list
        :type game: list
        :return: None
        """

        self.tie_resolved = False
        self.game = game
        if game:
            self.load_puzzle(self.game[0]['puzzle'])
        self.reset_scores()

    def load_puzzle(self, puzzle):
        """
        Load a puzzle dict.
        See :func:`data_caching.add_puzzle` for a description of
        puzzle dicts.

        :param puzzle: A puzzle dict
        :type puzzle: dict
        :return: None
        """

        if puzzle['puzzle'].strip():
            if self.game and self.game[0]['round_type'] in [
                    strings.round_type_tossup,
                    strings.round_type_triple_tossup,
                    strings.round_type_triple_tossup_final]:
                self.play_sound(values.file_sound_reveal_tossup)
            else:
                self.play_sound(values.file_sound_reveal_puzzle)

        if self.tossup_running:
            self.tossup()
        self.unavailable_letters = []
        self.puzzle_queue_out.put(('load', puzzle))
        self.letters_q.put(('reload', None, None))
        self.tossup_players_done = []
        self.consonants_remaining = True
        self.vowels_remaining = True
        self.speedup_consonants_remaining = True

        # consider revealed if the puzzleboard is clear
        self.revealed = True if not puzzle['puzzle'].split() else False

    def next_puzzle(self):
        """
        If there are still puzzles in the game list, load the next one.

        :return: None
        """

        try:
            self.game.pop(0)
            puzzle = self.game[0]

            if self.timer.final_spin_started:
                while puzzle['round_type'] == strings.round_type_speedup:
                    self.game.pop(0)
                    puzzle = self.game[0]
                self.timer.final_spin_started = False

            if (
                    self.game
                    and self.game[0]['round_type']
                    == strings.round_type_bonus):
                self.select_winner()
            else:
                self.load_puzzle(puzzle['puzzle'])
        except IndexError:
            pass

    def clear_puzzle(self):
        """
        Clear the puzzleboard.

        :return: None
        """

        self.load_puzzle({
            'category': '',
            'clue': '',
            'puzzle': ' ' * 52})

    def tossup(self, player=None):
        """
        If there is no tossup in progress, start one.
        If there is a tossup in progress, pause it.
        If `player` is 1, 2, or 3, select that player.

        :param player: A player's number, defaults to None
        :type player: int, optional
        :return: None
        """

        if player:
            if player in self.tossup_players_done:
                return
            self.tossup_players_done.append(player)

        if self.tossup_running:
            self.puzzle_queue_out.put(('pause_tossup', None))
            self.tossup_button.disabled = False

            if self.revealed:
                self.tossup_sound.stop()
                self.play_sound(values.file_sound_buzz_double)

            if player in [1, 2, 3]:
                self.select_player(player)
        else:
            self.tossup_button.disabled = True
            if not self.tossup_players_done:
                # start tossup
                self.puzzle_queue_out.put(('tossup', None))
            else:
                # tossup already started, resume
                self.puzzle_queue_out.put(('resume_tossup', None))
            self.select_player(0)
            if not self.tossup_sound.state == 'play':
                self.tossup_sound.play()

        self.tossup_running = not self.tossup_running

    def stop_all_flashing(self):
        """
        Make all of the scoreboards stop flashing.

        :return: None
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
        If `player_solved` is False, do not play the sounds indicating
        their success.

        :param player_solved: True if a player solved the puzzle,
                              defaults to True
        :type player_solved: bool, optional
        :return: None
        """

        self.tossup_sound.stop()

        if player_solved:
            if self.game:
                if self.tiebreaker_started:
                    self.tie_resolved = True
                    self.tiebreaker_started = False
                round_type = self.game[0]['round_type']
                if round_type == strings.round_type_bonus:
                    self.play_sound(values.file_sound_solve_bonus)
                elif round_type == strings.round_type_triple_tossup:
                    self.play_sound(values.file_sound_solve_triple_tossup)
                elif round_type in [
                        strings.round_type_tossup,
                        strings.round_type_triple_tossup_final]:
                    self.play_sound(values.file_sound_solve_tossup)
                else:
                    # not a tossup or bonus round,
                    # increase score if less than minimum prize
                    if self.get_score() < self.min_win:
                        self.set_score(self.min_win)

                    if self.game[0]['puzzle']['clue']:
                        self.play_sound(values.file_sound_solve_clue)
                    else:
                        self.play_sound(values.file_sound_solve)

                self.add_total(int(self.game[0]['round_reward']))
        self.puzzle_queue_out.put(('reveal', None))
        self.stop_all_flashing()

        self.revealed = True

    def solve_clue(self, player_solved):
        """
        If `player_solved` is True, add `clue_solve_reward` to the
        selected player's score, and play the 'clue correct' sound.
        Otherwise, play the buzzer sound.

        :param player_solved: True if the player solved the clue
        :type player_solved: bool
        :return: None
        """

        if player_solved:
            self.add_score(self.clue_solve_reward)
            self.play_sound(values.file_sound_clue_correct)
        else:
            self.play_sound(values.file_sound_buzz)

    def guess_letter(self):
        """
        Open a prompt to select a letter.

        :return: None
        """

        if (
                self.selected_player == 0
                or self.get_value() is None):
            return
        popup = prompts.ChooseLetterPrompt(
            self.guessed_letter,
            self.unavailable_letters,
            on_dismiss=lambda i: self.get_keyboard())
        popup.open()
        popup.get_keyboard()

    def guessed_letter(self, letter):
        """
        Pass the `letter` to the PuzzleLayout to check for matches.

        :param letter: A string consisting of a single letter
        :type letter: str
        :return: None
        """

        self.unavailable_letters.append(letter.lower())
        self.puzzle_queue_out.put(('letter', letter))
        self.letters_q.put(('remove_letter', None, letter))

    def buy_vowel(self):
        """
        If the player can afford a vowel, subtract `vowel_price` from
        their score.

        :return: None
        """

        if self.get_score() >= self.vowel_price:
            self.add_score(-self.vowel_price)

    def bonus_round_letters(self, letters):
        """
        Pass the list of selected letters to the puzzleboard,
        and remove them from the used letter board.

        :param letters: A list of single-character strings
        :type letters: list
        :return: None
        """

        self.unavailable_letters.extend(letters)
        self.puzzle_queue_out.put(('bonus_round_letters', letters))
        self.letters_q.put(('remove_letters', None, letters))

    def get_value(self):
        """
        Get the value indicated by the custom cash value input box.
        If the box is empty, get the value indicated by the cash value
        spinner.

        :return: The value, or None if no value is selected
        :rtype: int
        """

        custom_value = data_caching.str_to_int(self.custom_value.text, None)
        if custom_value is not None:
            return custom_value
        else:
            # if there is a '+' in the text, split by '+' and add
            add_values = []
            for number in self.dropdown.text.split('+'):
                value = data_caching.str_to_int(number, None)
                if value is not None:
                    add_values.append(value)
            if add_values:
                return sum(add_values)
            else:
                return None

    def correct_letter(self, match):
        """
        Indicate the number of matches in the manager.
        If there are no matches, play the buzzer sound.
        `match` is a tuple of the form (letter, number) indicating the
        letter and the number of matches.

        :param match: A letter and the number of matches
        :type match: tuple
        :return: None
        """

        letter, self.matches = match

        if not self.matches and not self.timer.final_spin_started:
            self.play_sound(values.file_sound_buzz)

        # show number of matches in puzzle_label
        self.puzzle_label.text = strings.label_matches.format(
            letter=letter.upper(), matches=self.matches)
        # schedule to show the puzzle again
        Clock.schedule_once(self.display_puzzle, values.time_show_matches)

    def increase_score(self):
        """
        Adjust the selected player's score based on the number of
        matches.

        :return: None
        """

        value = self.get_value()
        if value:
            self.add_score(self.matches * value)
        # reset the values, unless it is the speed-up round
        if not self.timer.final_spin_started:
            self.custom_value.text = ''
            self.dropdown.text = strings.dropdown_select_value

    def no_more_consonants(self):
        """
        Play a sound indicating no more consonants, and remove
        consonants from the used letters board.

        :return: None
        """

        # only do this once per round
        if self.consonants_remaining:
            self.consonants_remaining = False

            self.play_sound(values.file_sound_no_more_consonants)

            self.unavailable_letters.extend([
                c for c in strings.consonants
                if c not in self.unavailable_letters])
            self.letters_q.put(('no_more_consonants', None, None))

    def no_more_vowels(self):
        """
        Play a sound indicating no more vowels, and remove vowels from
        the used letters board.

        :return: None
        """

        # only do this once per round
        if self.vowels_remaining:
            self.vowels_remaining = False

            self.play_sound(values.file_sound_no_more_vowels)

            self.unavailable_letters.extend([
                c for c in strings.vowels
                if c not in self.unavailable_letters])
            self.letters_q.put(('no_more_vowels', None, None))

    def lose_turn(self):
        """
        Player has lost a turn; move to next player.

        :return: None
        """

        self.select_player((self.selected_player % 3) + 1)

    def bankrupt(self):
        """
        Bankrupt the selected player.

        :return: None
        """

        if self.selected_player:
            self.play_sound(values.file_sound_bankrupt)
            self.set_score(0)

    def bank_score(self):
        """
        Add the selected player's score to their game total, then set
        each player's score to 0.

        :return: None
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
        Open a Popup prompting the user to fill in some game settings.

        :return: None
        """

        popup = prompts.ManagerSettingsPrompt()
        popup.bind(on_dismiss=self.load_settings)
        popup.bind(on_dismiss=lambda i: self.get_keyboard())
        popup.open()

    def load_settings(self, _instance=None):
        """
        Load settings from file.

        :param _instance: The widget that called this function,
                          defaults to None
        :type _instance: kivy.uix.widget.Widget, optional
        :return: None
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
            hotkey['name']:
                settings.get('hotkeys', {}).get(
                    hotkey['name'], hotkey['default']).lower()
            for hotkey in values.hotkeys}

    @staticmethod
    def play_sound(filename):
        """
        Play the audio file specified by `filename`.

        :param filename: A filename
        :type filename: str
        :return: None
        """

        sound = SoundLoader.load(filename)
        if sound:
            sound.play()

    def speedup_buzz(self, _dt):
        """
        Play the buzz sound.
        Does nothing if the puzzle has already been solved.

        :param _dt: The time elapsed between scheduling and calling
        :return: None
        """

        if self.timer.final_spin_started:
            self.play_sound(values.file_sound_buzz)

    def update_dropdown(self):
        """
        Update the cash values dropdown so that it indicates if the
        final spin bonus is applied.

        :return: None
        """

        # this function will be called every time the text changes.
        # ignore_on_text is used to avoid recursion
        if not self.dropdown.ignore_on_text:
            self.dropdown.ignore_on_text = True

            text = self.dropdown.text
            vals = self.dropdown.values
            bonus = self.dropdown.bonus_values

            if self.timer.final_spin_started:
                # final spin started; bonus should be shown
                try:
                    self.dropdown.text = bonus[vals.index(text)]
                except ValueError:
                    # text not in values; bonus already shown
                    pass
            else:
                # final spin not started; bonus should not be shown
                try:
                    self.dropdown.text = vals[bonus.index(text)]
                except ValueError:
                    # text not in bonus; bonus already not shown
                    pass

            self.dropdown.ignore_on_text = False

    def exit_other_apps(self, _instance=None):
        """
        Tell all other apps to stop.

        :param _instance: App instance that called this method, defaults
                          to None
        :type _instance: kivy.app.App, optional
        :return: None
        """

        for q in [self.puzzle_queue_out, self.red_q, self.ylw_q, self.blu_q]:
            q.put(('exit', None))
        self.letters_q.put(('exit', None, None))


class BaseApp(App):
    """
    A Kivy App.

    The layout provided to __init__ will be used as the root of the App.
    """

    def __init__(self, layout_class, layout_args, title=None, **kwargs):
        """
        Create an App with an instance of `layout_class` as the root
        layout.

        If `title` is not specified, the string `strings.app_title` will
        be used as the title of the window.

        :param layout_class: A subclass of Widget (not an instance)
        :type layout_class: type
        :param layout_args: Arguments for initializing the layout
        :type layout_args: tuple
        :param title: The title of the app window, defaults to None
        :type title: str
        :param kwargs: Additional keyword arguments for the App
        """

        super(BaseApp, self).__init__(**kwargs)
        self.layout = layout_class
        self.args = layout_args
        if title is None:
            self.title = strings.app_title
        else:
            self.title = title

    def build(self):
        """
        Build the root layout of the app.

        :return: The root layout
        :rtype: kivy.uix.widget.Widget
        """

        return self.layout(*self.args)


def launch_app(root_layout_class, args=(), title=None, new_window=True):
    """
    Create and launch a :class:`BaseApp`\\, using an instance of
     `root_layout_class` as the root layout. Use the tuple `args` to
     specify arguments for the initialization of the layout.

    If `new_window` is True, the app will be launched in a separate
    process.

    :param root_layout_class: A subclass of Widget (not an instance)
    :type root_layout_class: type
    :param args: Arguments for initializing the layout, defaults to ()
    :type args: tuple, optional
    :param title: The title of the app window, defaults to None
    :type title: str, optional
    :param new_window: True if the app should be opened in a new
                       process, otherwise False, defaults to True
    :type new_window: bool, optional
    :return: None
    """

    if new_window:
        # `target=App().run` doesn't work
        # because the App instances cannot be pickled
        multiprocessing.Process(
            target=launch_app,
            args=(root_layout_class,),
            kwargs={'args': args, 'title': title, 'new_window': False}
        ).start()
    else:
        BaseApp(root_layout_class, args, title=title).run()


if __name__ == '__main__':
    puzzle_q1 = multiprocessing.Queue()
    puzzle_q2 = multiprocessing.Queue()
    red_queue = multiprocessing.Queue()
    yellow_queue = multiprocessing.Queue()
    blue_queue = multiprocessing.Queue()
    letters_queue = multiprocessing.Queue()

    launch_app(
        puzzleboard.PuzzleWithCategory,
        args=(puzzle_q1, puzzle_q2),
        title=strings.app_title_puzzleboard)
    launch_app(
        score.ScoreLayout,
        args=(values.color_red, red_queue),
        title=strings.app_title_score)
    launch_app(
        score.ScoreLayout,
        args=(values.color_yellow, yellow_queue),
        title=strings.app_title_score)
    launch_app(
        score.ScoreLayout,
        args=(values.color_blue, blue_queue),
        title=strings.app_title_score)
    launch_app(
        used_letters.LettersWithScore,
        args=(letters_queue,),
        title=strings.app_title_used_letters)
    launch_app(
        ManagerLayout,
        args=(
            puzzle_q1, puzzle_q2, red_queue, yellow_queue, blue_queue,
            letters_queue),
        title=strings.app_title_manager,
        new_window=False)
