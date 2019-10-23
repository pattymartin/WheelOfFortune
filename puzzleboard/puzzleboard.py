import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, ObjectProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .prompts import save_puzzle_prompt, load_puzzle_prompt

panels_dir = os.path.join(os.path.dirname(__file__), r'panels')
panel_file = r'panel.png'
panel_file_blue = r'panel_blue.png'
panel_file_white = r'panel_white.png'

Builder.load_string(r"""
<Panel>:
    layout: ll
    LetterLayout:
        id: ll
        source_image: src_im
        text_label: txt
        anchor_x: 'center'
        anchor_y: 'center'
        pos: self.parent.pos
        size: self.parent.size
        Image:
            id: src_im
            source: r'{}'
        Label:
            id: txt
            color: 0, 0, 0, 0
            font_size: self.size[0]
            bold: True
            halign: 'center'
            valign: 'center'
""".format(os.path.join(panels_dir, panel_file)))

def bind_keyboard(widget):
    """Provide keyboard focus to a widget"""
    
    widget._keyboard = Window.request_keyboard(
        widget._keyboard_closed, widget)
    widget._keyboard.bind(on_key_down=widget._on_keyboard_down)

class PuzzleLayout(GridLayout):
    """GridLayout containing all Panels."""
    panel_size = ListProperty([]) # [width, height] from an Image object
    
    def __init__(self, rows=6, cols=16, **kwargs):
        """Create the layout and bind the keyboard."""
        super(PuzzleLayout, self).__init__(rows=rows, cols=cols, **kwargs)
        for i in range(rows):
            for j in range(cols):
                if (
                        i in (0, rows-1)
                        or j in (0, cols-1)
                        or (i, j) in [
                            (1, 1), (1, cols-2),
                            (rows-2, 1), (rows-2, cols-2)]):
                    # create blank widgets for the corners and borders.
                    # there are hidden widgets along the top, bottom,
                    # left, and right, that are resized to push the panels
                    # into the proper alignment
                    widget = Widget()
                    self.add_widget(widget)
                else:
                    # create panels
                    panel = Panel()
                    self.add_widget(panel)
                    self.panel_size = panel.layout.source_image.texture.size
        bind_keyboard(self)
    
    def do_layout(self, *args):
        super(PuzzleLayout, self).do_layout(*args)
        width = self.panel_size[0] * (self.cols - 2)
        height = self.panel_size[1] * (self.rows - 2)
        ratio = width / height
        
        w, h = self.size # current layout size
        if w / h > ratio:
            # too wide
            for i, x in enumerate(list(self.children)):
                # remove first and last row
                if i < self.cols or (len(self.children) - i) <= self.cols:
                    x.size_hint_y = None
                    x.height = 0
                # space out first and last column
                if (i % self.cols) in (0, self.cols-1):
                    x.size_hint_x = None
                    board_width = h * ratio
                    extra_width = w - board_width
                    x.width = extra_width / 2
                else:
                    x.size_hint_x = 1
        elif w / h < ratio:
            # too tall
            for i, x in enumerate(list(self.children)):
                # remove first and last column
                if (i % self.cols) in (0, self.cols-1):
                    x.size_hint_x = None
                    x.width = 0
                # space out first and last row
                if i < self.cols or (len(self.children) - i) <= self.cols:
                    x.size_hint_y = None
                    board_height = w / ratio
                    extra_height = h - board_height
                    x.height = extra_height / 2
                else:
                    x.size_hint_y = 1
    
    def check_all(self, letter):
        """Check all Panels for a given letter and reveal matches."""
        reveal_interval = 0.9 # seconds before letter is revealed
        blue_interval = 0.3 # seconds the panel should be blue
        
        if letter in 'abcdefghijklmnopqrstuvwxyz':
            # indices in order from top to bottom, left to right
            indices = [
                    i + (j*self.cols)
                    for i in range(self.cols)
                        for j in range(self.rows)
                ][::-1]
            # the number of matches found so far,
            # used to offset the scheduled time to change the panel
            matches = 0
            for i in indices:
                try:
                    layout = self.children[i].layout
                    if layout.hidden() and layout.check_letter(letter):
                        # match found
                        # schedule panel to turn blue
                        Clock.schedule_once(
                            layout.blue,
                            blue_interval * (matches + 1))
                        # schedule panel to be revealed
                        Clock.schedule_once(
                            layout.show_letter,
                            reveal_interval * (matches + 1))
                        matches += 1
                except AttributeError:
                    # empty widget
                    pass
    
    def reveal_all(self):
        """Reveal the entire puzzle."""
        for widget in self.children:
            try:
                if widget.layout.text_label.text:
                    widget.layout.show_letter()
            except AttributeError:
                pass
    
    def save_puzzle(self):
        """Prompt the user to save the puzzle."""
        puzzle = ''
        for widget in self.children[::-1]:
            try:
                letter = widget.layout.text_label.text
                puzzle += letter if letter else ' '
            except AttributeError:
                # empty widget
                pass
        save_puzzle_prompt(puzzle, lambda: bind_keyboard(self))
    
    def choose_puzzle(self):
        """
        Prompt the user to select a puzzle,
        then load that puzzle.
        """
        load_puzzle_prompt(self.load_puzzle)
    
    def load_puzzle(self, puzzle):
        """
        Load a puzzle into the puzzleboard.
        """
        interval = 0.1 # seconds between letters loading
        puzzle = list(puzzle)
        
        # set letters
        for widget in self.children[::-1]:
            try:
                layout = widget.layout
                letter = puzzle.pop(0)
                layout.text_label.color = [0, 0, 0, 0]
                layout.text_label.text = '' if letter == ' ' else letter
                layout.green()
            except AttributeError:
                # empty widget
                pass
        
        # turn letter panels white
        # indices in order from top to bottom, left to right
        indices = [
                i + (j*self.cols)
                for i in range(self.cols)
                    for j in range(self.rows)
            ][::-1]
        # the number of non-space characters encountered,
        # used to offset the scheduled time to change the panel
        letters = 0
        for i in indices:
            try:
                layout = self.children[i].layout
                if layout.text_label.text:
                    # schedule panel to turn white
                    Clock.schedule_once(
                        layout.hide,
                        interval * (letters + 1))
                    letters += 1
            except AttributeError:
                # empty widget
                pass
        bind_keyboard(self)
    
    def _keyboard_closed(self):
        """Remove keyboard binding when the keyboard is closed."""
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Reveal the puzzle when the Enter key is pressed."""
        letter = keycode[1]
        if 'ctrl' in modifiers:
            if letter == 's':
                self.save_puzzle()
            elif letter == 'o':
                self.choose_puzzle()
        elif keycode[1] == 'enter':
            self.reveal_all()
        else:
            self.check_all(letter)

class LetterLayout(AnchorLayout):
    """Defines the layout of a Panel object."""
    source_image = ObjectProperty(None) # an Image object
    text_label = ObjectProperty(None) # a Label object
    
    def blue(self, td=None):
        """Turn this panel blue."""
        self.source_image.source = os.path.join(panels_dir, panel_file_blue)
    
    def white(self):
        """Turn this panel white."""
        self.source_image.source = os.path.join(panels_dir, panel_file_white)
    
    def green(self):
        """Turn this panel to show the WOF logo."""
        self.source_image.source = os.path.join(panels_dir, panel_file)
    
    def show_letter(self, td=None):
        """Turn the panel white and reveal the letter."""
        self.white()
        self.text_label.color = [0, 0, 0, 1]
    
    def hide(self, td=None):
        """Hide the letter on this panel."""
        text = self.text_label.text.lower()
        if text:
            if not text in 'abcdefghijklmnopqrstuvwxyz':
                # don't hide punctuation
                self.show_letter()
                return
            self.white()
        else:
            # turn panel green if there's no letter
            self.green()
        self.text_label.color = [0, 0, 0, 0]
    
    def hidden(self):
        """Returns True if this panel's letter is currently hidden."""
        return self.text_label.color == [0, 0, 0, 0]

    def check_letter(self, letter):
        """
        Check whether this panel's letter is the same as the given letter.
        """
        
        if self.text_label.text.lower() == letter:
            return True
        else:
            return False

class Panel(Button):
    """A single panel that may contain a letter."""
    
    layout = ObjectProperty(None) # a LetterLayout object
    
    def __init__(self, **kwargs):
        """Create the Panel and bind the click function."""
        super(Panel, self).__init__(**kwargs)
        self.bind(on_release=self.click)
    
    def click(self, instance):
        """
        Show this panel's letter and set keyboard focus to this Panel.
        Also turns all other panels green if they don't have letters.
        This function will be called when the Panel is clicked.
        """
        
        # turn widgets green if they don't have text
        for widget in self.parent.children:
            try:
                if not widget.layout.text_label.text:
                    widget.layout.hide()
            except AttributeError:
                # empty widget
                pass
        self.layout.show_letter()
        bind_keyboard(self)
    
    def _keyboard_closed(self):
        """Remove keyboard binding when the keyboard is closed."""
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Receive a pressed key, and put the letter in the text label.
        Then, move focus to the next panel
        (or previous if backspace is pressed).
        """
        
        letter = keycode[1]
        # map non-alphabetic characters to their shift symbols
        # on a standard US keyboard
        shifts = {'1': '!', '2': '@', '3': '#',
                  '4': '$', '5': '%', '6': '^',
                  '7': '&', '8': '*', '9': '(',
                  '0': ')', '-': '_', '=': '+',
                  '[': '{', ']': '}', '\\': '|',
                  ';': ':', '\'': '"', ',': '<',
                  '.': '>', '/': '?'}
        if 'ctrl' in modifiers:
            if letter == 's':
                self.parent.save_puzzle()
            elif letter == 'o':
                self.parent.choose_puzzle()
        elif 'shift' in modifiers and letter in shifts.keys():
            # shift is held, get shift symbol
            self.layout.text_label.text = shifts[letter]
            self.select_next()
        elif letter in 'abcdefghijklmnopqrstuvwxyz1234567890-=[]\\;\',./':
            # set text and move to next panel
            self.layout.text_label.text = letter.upper()
            self.select_next()
        elif letter == 'backspace':
            # remove this panel's text, select previous panel
            self.layout.text_label.text = ''
            self.select_prev()
        elif letter == 'enter':
            # entry finished, hide all letters
            # and bind keyboard to main PuzzleLayout
            self.hide_all()
            bind_keyboard(self.parent)
        elif letter == 'spacebar':
            # move to next panel
            self.select_next()
    
    def select_next(self):
        """Select the next panel."""
        # hide panel if there's no text
        if not self.layout.text_label.text:
            self.layout.hide()
        children = list(self.parent.children)
        # list of panels is in reverse order
        i = children.index(self) - 1
        while i >= 0:
            try:
                children[i].click(None)
                break
            except AttributeError:
                # empty panel
                i -= 1
    
    def select_prev(self):
        """Select the previous panel and remove its text."""
        # hide panel if there's no text
        if not self.layout.text_label.text:
            self.layout.hide()
        children = list(self.parent.children)
        # list of panels is in reverse order
        i = children.index(self) + 1
        while i < len(children):
            try:
                children[i].click(None)
                children[i].layout.text_label.text = ''
                break
            except AttributeError:
                # empty panel
                i += 1
        # panel was hidden at the start of this function.
        # if this is the first panel, run click() to show it again:
        if i >= len(children):
            self.click(None)
    
    def hide_all(self):
        """
        Hide all panels in the parent PuzzleLayout.
        """
        
        children = list(self.parent.children)
        for c in children:
            try:
                c.layout.hide()
            except AttributeError:
                # empty widget
                pass

class PuzzleBoardApp(App):
    """Puzzleboard Kivy App"""
    
    def build(self):
        """Build the app."""
        
        return PuzzleLayout()
