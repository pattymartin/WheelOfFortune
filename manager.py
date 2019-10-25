import multiprocessing
import os

from kivy.app import App
from kivy.clock import Clock
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

import prompts, puzzleboard, score, strings

assets_dir = os.path.join(os.path.dirname(__file__), r'assets')
settings_icon_file = 'settings.png'

Builder.load_string("""
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
            source: r'{}'
""".format(
    os.path.join(assets_dir, settings_icon_file)))

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
    
    def __init__(self, puzzle_queue, red_q, ylw_q, blu_q, **kwargs):
        """Create the layout."""
        super(ManagerLayout, self).__init__(orientation='vertical', **kwargs)
        self.puzzle_queue = puzzle_queue
        self.red_q = red_q
        self.ylw_q = ylw_q
        self.blu_q = blu_q
        
        self.add_widget(self._exit_layout())
        self.add_widget(self._puzzle_label())
        self.add_widget(self._main_buttons())
        self.add_widget(self._player_bar())
        self.add_widget(self._player_control())
        
        if self.puzzle_queue:
            Clock.schedule_once(self.check_queue, 5)
    
    def _exit_layout(self):
        """
        Create a layout containing an exit button
        """
        layout = BoxLayout(orientation='horizontal')
        layout.size_hint_y = 0.15
        layout.add_widget(Widget())
        
        btn_exit = SquareButton(text='X')
        btn_exit.bind(on_release=self.exit_app)
        layout.add_widget(btn_exit)
        
        return layout
    
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
        self.btn_red = self._player_button([1, 0, 0, 1], self.select_red)
        self.btn_ylw = self._player_button([1, 1, 0, 1], self.select_yellow)
        self.btn_blu = self._player_button([0, 0, 1, 1], self.select_blue)
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
            btn_minus = SquareButton(text='-')
            btn_plus = SquareButton(text='+')
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
            dropdown = Spinner(
                text='Select cash value',
                values=self.get_cash_values()
                )
            dropdown_layout.add_widget(dropdown)
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
            btn_solve = Button(text=strings.mgr_btn_solve)
            btn_v.bind(on_release=self.buy_vowel)
            btn_lose_turn.bind(on_release=self.lose_turn)
            btn_bankrupt.bind(on_release=self.bankrupt)
            btn_solve.bind(on_release=self.solve)
            button_box.add_widget(btn_v)
            button_box.add_widget(btn_lose_turn)
            button_box.add_widget(btn_bankrupt)
            button_box.add_widget(btn_solve)
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
        except:
            pass
        Clock.schedule_once(self.check_queue, 1)
    
    def select_red(self, instance):
        """
        Change the colors of TextInput boxes
        to indicate that the red player has been selected.
        """
        self.selected_player = 1
        self.selection_color((1, 0.75, 0.75, 1))
    
    def select_yellow(self, instance):
        """
        Change the colors of TextInput boxes
        to indicate that the yellow player has been selected.
        """
        self.selected_player = 2
        self.selection_color((1, 1, 0.75, 1))
    
    def select_blue(self, instance):
        """
        Change the colors of TextInput boxes
        to indicate that the blue player has been selected.
        """
        self.selected_player = 3
        self.selection_color((0.75, 0.75, 1, 1))
    
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
    
    def choose_puzzle(self, instance):
        """
        Prompt the user to select a puzzle.
        """
        prompts.load_puzzle_prompt(self.load_puzzle).open()
    
    def load_puzzle(self, puzzle):
        """
        Tell the layout to load `puzzle`.
        """
        self.puzzle_queue.a.put(('load', puzzle))
    
    def tossup(self, instance):
        # TODO
        print("TOSSUP")
    
    def reveal_puzzle(self, instance):
        """
        Tell the layout to reveal the puzzle.
        """
        self.puzzle_queue.a.put(('reveal', None))
    
    def guess_consonant(self, instance):
        # TODO
        print("GUESS CONSONANT")
    
    def buy_vowel(self, instance):
        # TODO
        print("BUY VOWEL")
    
    def lose_turn(self, instance):
        # TODO
        print("LOSE A TURN")
    
    def bankrupt(self, instance):
        # TODO
        print("BANKRUPT")
    
    def solve(self, instance):
        # TODO
        print("SOLVE")
    
    def get_cash_values(self):
        # TODO
        return ('$200', '$300', '$400')
    
    def cash_settings(self, instance):
        # TODO
        print("SETTINGS")
    
    def exit_app(self, instance):
        """
        Tell all apps to stop, then stop this app.
        """
        for q in [self.puzzle_queue.a, self.red_q, self.ylw_q, self.blu_q]:
            q.put(('exit', None))
        App.get_running_app().stop()

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
        args=((1, 0, 0, 1), red_q))
    ylw = multiprocessing.Process(
        target=launchScore,
        args=((1, 1, 0, 1), ylw_q))
    blu = multiprocessing.Process(
        target=launchScore,
        args=((0, 0, 1, 1), blu_q))
    
    manager_process.start()
    red.start()
    ylw.start()
    blu.start()

    puzzleboard.PuzzleboardApp(puzzle_q).run()
