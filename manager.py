import multiprocessing

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button

import puzzleboard
from puzzleboard import prompts, strings

def bind_keyboard(widget):
    """Provide keyboard focus to a widget"""
    
    widget._keyboard = Window.request_keyboard(
        widget._keyboard_closed, widget)
    widget._keyboard.bind(on_key_down=widget._on_keyboard_down)

puzzleboard.bind_keyboard = bind_keyboard

class ManagerApp(App):
    """
    An app to manage the PuzzleboardApp.
    """
    queue = None
    
    def __init__(self, queue=None, **kwargs):
        super(ManagerApp, self).__init__(**kwargs)
        self.queue = queue
    
    def build(self):
        # TODO more controls
        btn = Button(text=strings.title_select_puzzle)
        btn.bind(on_release=self.choose_puzzle)
        return btn
    
    def choose_puzzle(self, instance):
        prompts.load_puzzle_prompt(self.load_puzzle).open()
    
    def load_puzzle(self, puzzle):
        self.queue.put(('load', puzzle))

def launchManager(q):
    ManagerApp(q).run()

if __name__ == '__main__':
    q = multiprocessing.Queue()
    b = multiprocessing.Process(target=launchManager, args=(q,))
    b.start()

    puzzleboard.PuzzleboardApp(q).run()