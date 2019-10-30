import multiprocessing

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty
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

class SettingsButton(ButtonBehavior, Label):
    """
    A square button with a settings icon
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
    def __init__(self, bg_color=(0, 0, 0, 1), **kwargs):
        super(PlayerButton, self).__init__(**kwargs)
        self.bg_color = bg_color

class ManagerLayout(BoxLayout, Fullscreenable):
    """
    A BoxLayout for the ManagerApp.
    """
    
    seconds_left = NumericProperty(0)
    
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
        self.timer_running = False
        self.tossup_running = False
        self.tossup_players_done = []
        self.puzzle_string = ''
        self.puzzle_clue = ''
    
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
                and self.get_value() != 0):
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
        elif combination == self.hotkeys.get('start_tossup'):
            self.tossup()
        elif combination == self.hotkeys.get('bonus_round'):
            self.bonus_round()
        elif combination == self.hotkeys.get('solve'):
            self.reveal_puzzle()
        elif combination == self.hotkeys.get('lose_turn'):
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
            elif command == 'matches':
                self.correct_letter(args)
            elif command == 'tossup_timeout':
                self.tossup()
            elif command == 'no_more_consonants':
                # TODO
                print("NO MORE CONSONANTS")
            elif command == 'no_more_vowels':
                # TODO
                print("NO MORE VOWELS")
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
        prompts.LoadPuzzlePrompt(
                self.load_puzzle,
                on_dismiss=self.bind_keyboard_self
            ).open()
    
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
    
    def reveal_puzzle(self):
        """
        Tell the layout to reveal the puzzle.
        """
        self.puzzle_queue.a.put(('reveal', None))
        self.stop_all_flashing()
    
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
        popup.bind(on_dismiss=lambda i: popup._keyboard.release())
    
    def guessed_letter(self, letter):
        """
        Pass the `letter` to the PuzzleLayout to check for matches.
        This runs after `guess_letter()` is called
        and a letter is chosen.
        """
        if letter.lower() in 'aeiou':
            # do nothing if not enough money for a vowel
            if self.get_score() < self.vowel_price:
                return
            # subtract vowel price from score
            self.add_score(-self.vowel_price)
        self.unavailable_letters.append(letter.lower())
        self.puzzle_queue.a.put(('letter', letter))
        self.letters_q.put(('remove_letter', None, letter))
    
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
            return data_caching.str_to_int(self.dropdown.text)
    
    def correct_letter(self, match):
        """
        Adjust the selected player's score based on the number of matches.
        `match` is an tuple of the form (letter, number)
        indicating the letter and the number of matches.
        """
        letter, matches = match
        if letter.lower() not in 'aeiou':
            self.add_score(matches * self.get_value())
        self.custom_value.text = ''
        
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
    
    def timer(self):
        """
        Start the final spin timer.
        If the timer is already running,
        stop the timer.
        """
        
        if not self.seconds_left:
            self.seconds_left = self.timer_seconds
        
        if not self.timer_running:
            Clock.schedule_once(self.decrement_timer, values.timer_accuracy)
        
        self.timer_running = not self.timer_running
    
    def decrement_timer(self, instance):
        """
        Reduce `seconds_left` by
        `values.timer_accuracy` seconds.
        Then schedule this function in another
        `values.timer_accuracy` seconds.
        """
        
        if self.timer_running:
            self.seconds_left -= values.timer_accuracy
            Clock.schedule_once(self.decrement_timer, values.timer_accuracy)
    
    def reset_timer(self):
        """
        Reset the final spin timer.
        """
        
        self.timer_running = False
        self.seconds_left = self.timer_seconds
    
    def on_seconds_left(self, instance, value):
        """
        Keep the `timer_label` updated with the current
        time remaining.
        """
        
        if self.seconds_left == self.timer_seconds:
            self.timer_label.text = ''
        elif self.seconds_left <= 0:
            self.timer_label.text = strings.label_time_out
            self.timer_running = False
            self.timer_layout_manager.current = 'timeout'
        else:
            self.timer_label.text = strings.label_timer.format(
                int(self.seconds_left / 60), int(self.seconds_left % 60))
    
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
            self.vowel_price = int(settings.get('vowel_price', ''))
        except ValueError:
            self.vowel_price = values.default_vowel_price
        self.min_win = settings.get('min_win', values.default_min_win)
        self.dropdown.values = [strings.currency_format.format(value)
            for value in settings.get('cash_values', [])]
        
        try:
            minutes, seconds = settings.get('timer_time', ':').split(':')
        except ValueError:
            minutes, seconds = (0, 0)
        minutes = data_caching.str_to_int(minutes)
        seconds = data_caching.str_to_int(seconds)
        self.timer_seconds = (minutes * 60) + seconds
        self.seconds_left = self.timer_seconds
        self.timer_layout_manager.disabled = not bool(self.timer_seconds)
        
        self.hotkeys = {
            name: settings.get(name, default).lower()
            for name, default
            in zip(values.hotkey_names, values.hotkey_defaults)}
    
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
