from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import values

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
        self.queue = queue
        self.fill_layout()
        if self.queue:
            Clock.schedule_once(self.check_queue, values.queue_start)
    
    def fill_layout(self):
        """Fill in the layout."""
        self.clear_widgets()
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        vowels = 'aeiou'
        consonants = [c for c in alphabet if not c in vowels]
        
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
    
    def check_queue(self, instance):
        """
        Check the queue for incoming commands to execute.
        """
        try:
            command, args = self.queue.get(block=False)
            if command == 'remove_letter':
                self.unavailable.append(args.lower())
                self.fill_layout()
            elif command == 'reload':
                self.unavailable = []
                self.fill_layout()
            elif command == 'exit':
                App.get_running_app().stop()
        except:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)

class LetterboardLetter(ButtonBehavior, Label):
    """
    A single letter on the LetterboardLayout.
    """
    pass