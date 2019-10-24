import multiprocessing

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import puzzleboard
from puzzleboard import prompts, strings

def bind_keyboard(widget):
    """Provide keyboard focus to a widget"""
    
    widget._keyboard = Window.request_keyboard(
        widget._keyboard_closed, widget)
    widget._keyboard.bind(on_key_down=widget._on_keyboard_down)

puzzleboard.bind_keyboard = bind_keyboard

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

class ManagerLayout(BoxLayout):
    """
    A BoxLayout for the ManagerApp.
    """
    
    queue = None
    puzzle_label = None
    
    def __init__(self, queue=None, **kwargs):
        super(ManagerLayout, self).__init__(orientation='vertical', **kwargs)
        self.queue = queue
        
        self.puzzle_label = Label()
        self.add_widget(self.puzzle_label)
        
        btn_select = Button(text=strings.title_select_puzzle)
        btn_select.bind(on_release=self.choose_puzzle)
        self.add_widget(btn_select)
        
        btn_reveal = Button(text=strings.mgr_btn_reveal)
        btn_reveal.bind(on_release=self.reveal_puzzle)
        self.add_widget(btn_reveal)
        
        if self.queue:
            Clock.schedule_once(self.check_queue, 5)
    
    def check_queue(self, instance):
        """
        Check the queue for incoming commands.
        """
        try:
            command, args = self.queue.b.get(block=False)
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
    
    def choose_puzzle(self, instance):
        """
        Prompt the user to select a puzzle.
        """
        prompts.load_puzzle_prompt(self.load_puzzle).open()
    
    def load_puzzle(self, puzzle):
        """
        Tell the layout to load `puzzle`.
        """
        self.queue.a.put(('load', puzzle))
    
    def reveal_puzzle(self, instance):
        """
        Tell the layout to reveal the puzzle.
        """
        self.queue.a.put(('reveal', None))

class ManagerApp(App):
    """
    An app to manage the PuzzleboardApp.
    """
    queue = None
    
    def __init__(self, queue=None, **kwargs):
        super(ManagerApp, self).__init__(**kwargs)
        self.queue = queue
    
    def build(self):
        return ManagerLayout(self.queue)

def launchManager(q):
    ManagerApp(q).run()

if __name__ == '__main__':
    q = CommQueue()
    b = multiprocessing.Process(target=launchManager, args=(q,))
    b.start()

    puzzleboard.PuzzleboardApp(q).run()