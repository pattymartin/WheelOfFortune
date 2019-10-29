from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import score, strings, values
from my_widgets import Fullscreenable

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
        super(LettersWithScore, self).__init__(
            orientation='vertical', **kwargs)
        
        score_box = BoxLayout(orientation='horizontal')
        red_score = score.ScoreLayout(bg_color=values.color_red)
        ylw_score = score.ScoreLayout(bg_color=values.color_yellow)
        blu_score = score.ScoreLayout(bg_color=values.color_blue)
        score_box.add_widget(red_score)
        score_box.add_widget(ylw_score)
        score_box.add_widget(blu_score)
        score_box.size_hint_y = 0.25
        self.add_widget(score_box)
        
        self.scores = {
            'red': red_score,
            'blue': blu_score,
            'yellow': ylw_score}
        
        self.letterboard = LetterboardLayout()
        self.add_widget(self.letterboard)
        
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
                self.letterboard.fill_layout()
            elif command == 'reload':
                self.letterboard.unavailable = []
                self.letterboard.fill_layout()
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
            elif command == 'exit':
                App.get_running_app().stop()
        except:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)

class LetterboardLayout(GridLayout):
    """
    A layout showing available letters.
    """
    
    def __init__(self, callback=None, unavailable=[], queue=None,
                 rows=4, cols=7, **kwargs):
        """Create the layout."""
        super(LetterboardLayout, self).__init__(rows=rows, cols=cols, **kwargs)
        self.callback = callback
        self.unavailable = unavailable
        self.fill_layout()
    
    def fill_layout(self):
        """Fill in the layout."""
        self.clear_widgets()
        vowels = 'aeiou'
        consonants = [c for c in strings.alphabet if not c in vowels]
        
        def add_letter(letter):
            """
            Add a LetterboardLetter containing the specified `letter`.
            """
            if letter.lower() in self.unavailable:
                self.add_widget(Widget())
                return
            ll = LetterboardLetter(text=letter.upper())
            if self.callback:
                ll.bind(on_release=lambda i: self.callback(ll.text))
            self.add_widget(ll)
        
        for c in consonants:
            add_letter(c)
        
        self.add_widget(Widget())
        for v in vowels:
            add_letter(v)
        
        self.add_widget(Widget())

class LetterboardLetter(ButtonBehavior, Label):
    """
    A single letter on the LetterboardLayout.
    """
    pass