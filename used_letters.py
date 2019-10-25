from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

class LetterboardLayout(GridLayout):
    """
    A layout showing available letters.
    """
    
    def __init__(self, callback, unavailable=[], rows=4, cols=7, **kwargs):
        """Create the layout."""
        super(LetterboardLayout, self).__init__(rows=rows, cols=cols, **kwargs)
        
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        vowels = 'aeiou'
        consonants = [c for c in alphabet if not c in vowels]
        
        def add_letter(letter):
            """
            Add a LetterboardLetter containing the specified `letter`.
            """
            if letter.lower() in unavailable:
                self.add_widget(Widget())
                return
            ll = LetterboardLetter(text=letter.upper())
            ll.bind(on_release=lambda i: callback(ll.text))
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