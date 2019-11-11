from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import score, strings, values
from my_widgets import Fullscreenable

Builder.load_file(strings.file_kv_used_letters)

class LettersWithScore(BoxLayout, Fullscreenable):
    """
    A layout containing three ScoreLayouts
    and a LetterboardLayout.
    """
    
    def __init__(self, queue=None, **kwargs):
        """
        Create the layout.
        `queue` is a Queue from multiprocessing,
        used to accept commands sent to this layout.
        Commands should be a tuple of the form:
        (command, color, args)
        Available commands are:
        (remove_letter, reload, name, score,
        total, flash, stop_flash, exit)
        
        remove_letter:
            remove the letter `args` from the LetterboardLayout.
            `color` and `args` are ignored.
        reload:
            refill the LetterboardLayout with all letters.
            `color` and `args` are ignored.
        name:
            change the name of the player
            specified by `color` to `name`.
        score:
            change the score of the player
            specified by `color` to `score`.
        total:
            change the total of the player
            specified by `color` to `total`.
        flash:
            start the flashing effect
            for the player specified by `color`.
            `args` is ignored.
        stop_flash:
            stop the flashing effect
            for the player specified by `color`.
            `args` is ignored.
        exit:
            close the current App.
        """
        super(LettersWithScore, self).__init__(**kwargs)
        
        self.queue = queue
        if self.queue:
            Clock.schedule_once(self.check_queue, values.queue_start)
    
    def check_queue(self, instance):
        """
        Check the queue for incoming commands to execute.
        """
        try:
            command, color, args = self.queue.get(block=False)
            if command == 'remove_letter':
                self.letterboard.unavailable.append(args.lower())
            elif command == 'remove_letters':
                self.letterboard.unavailable.extend([c.lower() for c in args])
            elif command == 'reload':
                self.letterboard.unavailable = []
            elif command == 'name':
                self.scores[color].name = args
            elif command == 'score':
                self.scores[color].score = args
            elif command == 'total':
                self.scores[color].total = args
            elif command == 'flash':
                self.scores[color].flash()
            elif command == 'stop_flash':
                self.scores[color].flashing = False
                self.scores[color].flash_visible = False
            elif command == 'no_more_consonants':
                self.letterboard.unavailable.extend([
                    c for c in strings.alphabet if not c in 'aeiou'
                    and not c in self.letterboard.unavailable])
            elif command == 'no_more_vowels':
                self.letterboard.unavailable.extend([
                    c for c in strings.alphabet if c in 'aeiou'
                    and not c in self.letterboard.unavailable])
            elif command == 'exit':
                App.get_running_app().stop()
        except:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)

class LetterboardLayout(GridLayout):
    """
    A layout showing available letters.
    """
    
    unavailable = ListProperty([])
    
    def __init__(self, callback=None, unavailable=[], **kwargs):
        """
        Create the layout.
        If a letter is clicked, its text will be sent to
        `callback`.
        `unavailable` is a list of letters to be
        excluded from the layout.
        """
        super(LetterboardLayout, self).__init__(
            rows=len(values.used_letters_layout),
            cols=max(len(row) for row in values.used_letters_layout),
            **kwargs)
        self.callback = callback
        self.unavailable = unavailable
        
        for row in values.used_letters_layout:
            for letter in row:
                if letter.isspace():
                    self.add_widget(Widget())
                else:
                    self.add_widget(LetterboardLetter(text=letter))
            # if rows are not all the same length, fill in with empty space
            for i in range(self.cols-len(row)):
                self.add_widget(Widget())

class LetterboardLetter(ButtonBehavior, Label):
    """
    A single letter on the LetterboardLayout.
    """
    
    pass