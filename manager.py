import multiprocessing

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import data_caching, prompts, puzzleboard, score, strings, values

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Builder.load_string("""
#:import strings strings
<Button>:
    halign: 'center'
<SquareButton>:
    size_hint_x: None
    width:self.height
<SettingsButton>:
    size_hint_x: None
    width:self.height
    canvas.before:
        Rectangle:
            pos: self.pos
            size: self.size
            source: strings.file_settings_icon
""")

def bind_keyboard(widget):
    """Provide keyboard focus to a widget"""
    
    widget._keyboard = Window.request_keyboard(
        widget._keyboard_closed, widget)
    widget._keyboard.bind(on_key_down=widget._on_keyboard_down)

puzzleboard.bind_keyboard = bind_keyboard

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
    def __init__(self, bg_color=(0, 0, 0, 1), queue=None, **kwargs):
        super(PlayerButton, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.queue = queue

class ManagerLayout(BoxLayout):
    """
    A BoxLayout for the ManagerApp.
    """
    
    selected_player = 0
    unavailable_letters = []
    
    def __init__(self, puzzle_queue, red_q, ylw_q, blu_q, **kwargs):
        """Create the layout."""
        super(ManagerLayout, self).__init__(orientation='vertical', **kwargs)
        self.puzzle_queue = puzzle_queue
        self.red_q = red_q
        self.ylw_q = ylw_q
        self.blu_q = blu_q
        
        self.add_widget(self._puzzle_label())
        self.add_widget(self._main_buttons())
        self.add_widget(self._player_bar())
        self.add_widget(self._player_control())
        
        self.load_settings()
        
        if self.puzzle_queue:
            Clock.schedule_once(self.check_queue, values.queue_start)
    
    def _puzzle_label(self):
        """
        Create a label to display the current puzzle.
        """
        self.puzzle_label = Label()
        self.puzzle_label.size_hint_y = 0.5
        return self.puzzle_label
    
    def _main_buttons(self):
        """
        Create a layout containing the main manager buttons.
        """
        layout = BoxLayout(orientation='horizontal')
        layout.size_hint_y = 0.5
        
        btn_select = Button(text=strings.title_select_puzzle)
        btn_select.bind(on_release=self.choose_puzzle)
        layout.add_widget(btn_select)
        
        btn_clear = Button(text=strings.mgr_btn_clear)
        btn_clear.bind(on_release=self.clear_puzzle)
        layout.add_widget(btn_clear)
        
        btn_tossup = Button(text=strings.mgr_btn_tossup)
        btn_tossup.bind(on_release=self.tossup)
        layout.add_widget(btn_tossup)
        
        btn_reveal = Button(text=strings.mgr_btn_reveal)
        btn_reveal.bind(on_release=self.reveal_puzzle)
        layout.add_widget(btn_reveal)
        
        return layout
    
    def _player_bar(self):
        """
        Create a layout with a button to select each player.
        """
        
        player_bar = BoxLayout(orientation='horizontal')
        self.btn_red = self._player_button(
            values.color_red, self.select_red)
        self.btn_ylw = self._player_button(
            values.color_yellow, self.select_yellow)
        self.btn_blu = self._player_button(
            values.color_blue, self.select_blue)
        player_bar.add_widget(self.btn_red)
        player_bar.add_widget(self.btn_ylw)
        player_bar.add_widget(self.btn_blu)
        return player_bar
    
    def _player_button(self, color, callback):
        """
        Create a button to select a character.
        """
        btn = PlayerButton(color)
        btn.bind(on_release=callback)
        return btn
    
    def _player_control(self):
        def name_edit():
            name_edit_box = BoxLayout(orientation='horizontal')
            self.name_input = TextInput(hint_text=strings.input_name)
            confirm = SquareButton(text='OK')
            self.name_input.bind(
                on_enter=lambda i: self.update_name(self.name_input.text))
            confirm.bind(
                on_release=lambda i: self.update_name(self.name_input.text))
            name_edit_box.add_widget(self.name_input)
            name_edit_box.add_widget(confirm)
            return name_edit_box
        
        def score_control():
            score_ctrl_box = BoxLayout(orientation='horizontal')
            btn_minus = Button(text='-')
            btn_plus = Button(text='+')
            btn_minus.size_hint_x = 0.5
            btn_plus.size_hint_x = 0.5
            self.score_edit = TextInput(hint_text=strings.input_adjust_score)
            score_ctrl_box.add_widget(btn_minus)
            score_ctrl_box.add_widget(self.score_edit)
            score_ctrl_box.add_widget(btn_plus)
            return score_ctrl_box
        
        def value_select():
            value_box = BoxLayout(orientation='horizontal')
            select_box = BoxLayout(orientation='vertical')
            
            self.custom_value = TextInput(hint_text=strings.input_custom)
            dropdown_layout = BoxLayout(orientation='horizontal')
            btn_settings = SettingsButton()
            btn_settings.bind(on_release=self.cash_settings)
            self.dropdown = Spinner(
                text=strings.mgr_select_value
                )
            dropdown_layout.add_widget(self.dropdown)
            dropdown_layout.add_widget(btn_settings)
            select_box.add_widget(self.custom_value)
            select_box.add_widget(dropdown_layout)
            value_box.add_widget(select_box)
            
            button_c = SquareButton(text='C')
            button_c.bind(on_release=self.guess_consonant)
            value_box.add_widget(button_c)
            return value_box
        
        def player_buttons():
            button_box = BoxLayout(orientation='horizontal')
            btn_v = Button(text='V')
            btn_lose_turn = Button(text=strings.mgr_btn_lose_turn)
            btn_bankrupt = Button(text=strings.mgr_btn_bankrupt)
            btn_bank = Button(text=strings.mgr_btn_bank)
            btn_v.bind(on_release=self.buy_vowel)
            btn_lose_turn.bind(on_release=self.lose_turn)
            btn_bankrupt.bind(on_release=self.bankrupt)
            btn_bank.bind(on_release=self.bank_score)
            button_box.add_widget(btn_v)
            button_box.add_widget(btn_lose_turn)
            button_box.add_widget(btn_bankrupt)
            button_box.add_widget(btn_bank)
            return button_box
            
        player_ctrl = GridLayout(rows=2, cols=2)
        player_ctrl.add_widget(name_edit())
        player_ctrl.add_widget(score_control())
        player_ctrl.add_widget(value_select())
        player_ctrl.add_widget(player_buttons())
        return player_ctrl
    
    def check_queue(self, instance):
        """
        Check the queue for incoming commands.
        """
        try:
            command, args = self.puzzle_queue.b.get(block=False)
            if command == 'puzzle_loaded':
                puzzle_string = ' '.join(args['puzzle'].split())
                puzzle_clue = args['clue']
                self.puzzle_label.text = (
                    strings.mgr_label_puzzle + puzzle_string)
                if args['clue']:
                    self.puzzle_label.text += ('\n' +
                        strings.mgr_label_clue + puzzle_clue)
            elif command == 'matches':
                self.correct_letter(args)
        except:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)
    
    def select_red(self, instance):
        """
        Change the colors of TextInput boxes
        to indicate that the red player has been selected.
        """
        self.selected_player = 1
        self.selection_color(values.color_light_red)
    
    def select_yellow(self, instance):
        """
        Change the colors of TextInput boxes
        to indicate that the yellow player has been selected.
        """
        self.selected_player = 2
        self.selection_color(values.color_light_yellow)
    
    def select_blue(self, instance):
        """
        Change the colors of TextInput boxes
        to indicate that the blue player has been selected.
        """
        self.selected_player = 3
        self.selection_color(values.color_light_blue)
    
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
        elif self.selected_player == 2:
            self.btn_ylw.name = text
            self.ylw_q.put(('name', text))
        elif self.selected_player == 3:
            self.btn_blu.name = text
            self.blu_q.put(('name', text))
    
    def get_score(self):
        """
        Get the score of the current player.
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
        Set the score of the current player.
        """
        if self.selected_player == 1:
            self.btn_red.score = score
            self.red_q.put(('score', score))
        elif self.selected_player == 2:
            self.btn_ylw.score = score
            self.ylw_q.put(('score', score))
        elif self.selected_player == 3:
            self.btn_blu.score = score
            self.blu_q.put(('score', score))
    
    def add_score(self, score):
        """
        Add `score` to the selected player's score.
        """
        self.set_score(self.get_score() + score)
    
    def choose_puzzle(self, instance):
        """
        Prompt the user to select a puzzle.
        """
        prompts.LoadPuzzlePrompt(self.load_puzzle).open()
    
    def load_puzzle(self, puzzle):
        """
        Tell the layout to load `puzzle`.
        """
        self.unavailable_letters = []
        self.puzzle_queue.a.put(('load', puzzle))
    
    def clear_puzzle(self, instance):
        """
        Clear the puzzleboard.
        """
        self.load_puzzle({
            'category': '',
            'clue': '',
            'puzzle': ' ' * 52})
    
    def tossup(self, instance):
        # TODO
        print("TOSSUP")
    
    def reveal_puzzle(self, instance):
        """
        Tell the layout to reveal the puzzle.
        """
        self.puzzle_queue.a.put(('reveal', None))
    
    def guess_consonant(self, instance):
        """
        Open a prompt to select a letter.
        """
        if (
                self.selected_player == 0
                or self.get_value() == 0):
            return
        popup = prompts.ChooseLetterPrompt(
            self.guessed_letter, self.unavailable_letters)
        popup.open()
        bind_keyboard(popup)
    
    def guessed_letter(self, letter):
        """
        Pass the `letter` to the PuzzleLayout to check for matches.
        """
        self.unavailable_letters.append(letter.lower())
        self.puzzle_queue.a.put(('letter', letter))
    
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
    
    def correct_letter(self, matches):
        """
        Adjust the selected player's score based on the number of `matches`.
        `matches` is an int indicating the number of matched letters.
        """
        self.add_score(matches * self.get_value())
        self.custom_value.text = ''
    
    def buy_vowel(self, instance):
        # TODO
        print("BUY VOWEL")
    
    def lose_turn(self, instance):
        # TODO
        print("LOSE A TURN")
    
    def bankrupt(self, instance):
        # TODO
        print("BANKRUPT")
    
    def bank_score(self, instance):
        # TODO
        print("BANK SCORE")
    
    def cash_settings(self, instance):
        """
        Open a Popup prompting the user
        to fill in some game settings.
        """
        popup = prompts.ManagerSettingsPrompt()
        popup.bind(on_dismiss=self.load_settings)
        popup.open()
    
    def load_settings(self, instance=None):
        """
        Load settings from file.
        """
        settings = data_caching.get_variables()
        self.vowel_price = settings.get('vowel_price',
            values.default_vowel_price)
        self.min_win = settings.get('min_win', values.default_min_win)
        self.dropdown.values = ['${:,}'.format(value)
            for value in settings.get('cash_values', [])]
    
    def exit_app(self, instance):
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

def launchManager(*args):
    """
    Launch a ManagerApp.
    """
    ManagerApp(*args).run()

def launchScore(color, q):
    """
    Launch a ScoreApp.
    """
    ScoreApp(color, queue=q).run()

if __name__ == '__main__':
    puzzle_q = CommQueue()
    red_q = multiprocessing.Queue()
    ylw_q = multiprocessing.Queue()
    blu_q = multiprocessing.Queue()
    
    manager_process = multiprocessing.Process(
        target=launchManager,
        args=(puzzle_q, red_q, ylw_q, blu_q))
    red = multiprocessing.Process(
        target=launchScore,
        args=(values.color_red, red_q))
    ylw = multiprocessing.Process(
        target=launchScore,
        args=(values.color_yellow, ylw_q))
    blu = multiprocessing.Process(
        target=launchScore,
        args=((values.color_blue, blu_q)))
    
    manager_process.start()
    red.start()
    ylw.start()
    blu.start()

    puzzleboard.PuzzleboardApp(puzzle_q).run()
