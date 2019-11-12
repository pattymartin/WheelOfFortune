import queue
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

import prompts
import strings
import values
from my_widgets import Fullscreenable, KeyboardBindable

Builder.load_file(values.file_kv_puzzleboard)


class PuzzleWithCategory(BoxLayout, Fullscreenable):
    """BoxLayout containing the puzzleboard and category strip."""

    def __init__(self, q=None, **kwargs):
        """Create the layout."""
        super(PuzzleWithCategory, self).__init__(**kwargs)
        self.puzzle_layout = PuzzleLayout(self.category, q)


class PuzzleLayout(GridLayout, KeyboardBindable):
    """GridLayout containing all Panels."""

    category_label = ObjectProperty(None)
    queue = ObjectProperty(None)
    tossup_running = False

    def __init__(self, category_label=None, q=None, **kwargs):
        """Create the layout and bind the keyboard."""
        super(PuzzleLayout, self).__init__(**kwargs)

        self.category_label = category_label
        self.queue = q

        for i in range(self.rows):
            for j in range(self.cols):

                if (i, j) in [
                        (0, 0), (0, self.cols - 1),
                        (self.rows - 1, 0), (self.rows - 1, self.cols - 1)]:
                    self.add_widget(Widget())
                else:
                    # create panels
                    panel = Panel()
                    self.add_widget(panel)
                    self.reference_layout = panel.layout

        self.get_keyboard()

        if self.queue:
            Clock.schedule_once(self.check_queue, values.queue_start)

    def check_queue(self, _dt):
        """
        Check the queue for incoming commands to execute.
        """
        try:
            command, args = self.queue.a.get(block=False)
            if command == 'letter':
                # args is a guessed letter
                self.check_all(args)
            elif command == 'bonus_round_letters':
                # args is multiple letters
                self.check_all_by_list(args, bonus_round=True)
            elif command == 'load':
                # args is a puzzle to be loaded
                self.load_puzzle(args)
            elif command == 'tossup':
                self.start_tossup()
            elif command == 'pause_tossup':
                self.pause_tossup()
            elif command == 'reveal':
                self.reveal_all()
            elif command == 'exit':
                App.get_running_app().stop()
        except queue.Empty:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)

    def check_all_by_list(self, letters, bonus_round=False):
        """
        Check all Panels for a list of letters
        and reveal matches.
        """

        letters = [letter for letter in letters
                   if letter.lower() in strings.alphabet]

        if bonus_round:
            # indices in order from top to bottom, left to right
            indices = [
                          i + (j * self.cols)
                          for i in range(self.cols)
                          for j in range(self.rows)
                      ][::-1]
        else:
            # indices in order from top to bottom, right to left
            indices = [
                          i + (j * self.cols)
                          for i in range(self.cols - 1, -1, -1)
                          for j in range(self.rows)
                      ][::-1]

        # the number of matches found so far,
        # used to offset the scheduled time to change the panel
        matches = 0
        remaining_letters = []

        for i in indices:
            try:
                layout = self.children[i].layout
                if layout.hidden():
                    if any(layout.check_letter(letter) for letter in letters):
                        # match found
                        # schedule panel to turn blue
                        Clock.schedule_once(
                            layout.blue,
                            values.interval_blue * matches)
                        # schedule "ding" sound
                        Clock.schedule_once(
                            lambda i: self.queue.b.put(('ding', None)),
                            values.interval_blue * matches)
                        # schedule panel to be revealed
                        Clock.schedule_once(
                            layout.show_letter,
                            values.interval_reveal * (matches + 1))
                        matches += 1
                    else:
                        panel_text = layout.text_label.text
                        if panel_text:
                            remaining_letters.append(panel_text)
            except AttributeError:
                # empty widget
                pass

        no_more_vowels = matches and not any(
            letter.lower() in strings.vowels
            for letter in remaining_letters)
        no_more_consonants = matches and not any(
            letter.lower() in strings.consonants
            for letter in remaining_letters)
        if self.queue and len(letters) == 1:
            self.queue.b.put(('matches', (letters[0], matches)))
            Clock.schedule_once(
                lambda i: self.queue.b.put(('reveal_finished', None)),
                values.interval_reveal * matches)
            if no_more_vowels:
                # indicate no more vowels in the middle of letter reveals
                Clock.schedule_once(
                    lambda i: self.queue.b.put(('no_more_vowels', None)),
                    values.interval_reveal * matches / 2)
            if no_more_consonants:
                # indicate no more consonants after all letters revealed
                Clock.schedule_once(
                    lambda i: self.queue.b.put(('no_more_consonants', None)),
                    values.interval_reveal * matches)

    def check_all(self, letter):
        """Check all Panels for a given letter and reveal matches."""

        self.check_all_by_list([letter])

    def reveal_all(self):
        """Reveal the entire puzzle."""
        # indices in order from top to bottom, left to right
        indices = [
                      i + (j * self.cols)
                      for i in range(self.cols)
                      for j in range(self.rows)
                  ][::-1]
        matches = 0
        for i in indices:
            try:
                layout = self.children[i].layout
                if layout.hidden() and layout.text_label.text:
                    # schedule panel reveal
                    Clock.schedule_once(
                        layout.show_letter,
                        values.interval_solve_reveal * matches)
                    matches += 1
            except AttributeError:
                # empty widget
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
        prompt = prompts.SavePuzzlePrompt(
            puzzle, on_dismiss=lambda instance: self.get_keyboard())
        prompt.open()

    def choose_puzzle(self):
        """
        Prompt the user to select a puzzle,
        then load that puzzle.
        """
        prompts.LoadPuzzlePrompt(self.selected_puzzles).open()

    def selected_puzzles(self, puzzles):
        """
        Get selected puzzles from a LoadPuzzlePrompt,
        and load the first one.
        """

        self.load_puzzle(puzzles[0])

    def load_puzzle(self, puzzle):
        """
        Load a puzzle into the puzzleboard.
        """
        self.tossup_running = False
        puzzle_string = list(puzzle['puzzle'])

        self.category_label.text = puzzle['category'].upper()

        if self.queue:
            self.queue.b.put(('puzzle_loaded', puzzle))

        # set letters
        for widget in self.children[::-1]:
            try:
                layout = widget.layout
                letter = puzzle_string.pop(0)
                layout.text_label.color = [0, 0, 0, 0]
                layout.text_label.text = '' if letter == ' ' else letter
                layout.green()
            except AttributeError:
                # empty widget
                pass

        # turn letter panels white
        # indices in order from top to bottom, left to right
        indices = [
                      i + (j * self.cols)
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
                        values.interval_load * letters)
                    letters += 1
            except AttributeError:
                # empty widget
                pass
        self.get_keyboard()

    def start_tossup(self):
        """
        Start a tossup by revealing the
        bottom-rightmost letter,
        then revealing random letters.
        """
        self.tossup_running = True

        # indices in order from bottom to top, right to left
        indices = [
                      i + (j * self.cols)
                      for i in range(self.cols - 1, -1, -1)
                      for j in range(self.rows - 1, -1, -1)
                  ][::-1]

        # look for the bottom-rightmost letter
        for i in indices:
            try:
                layout = self.children[i].layout
                if layout.text_label.text:
                    # letter found, reveal
                    layout.show_letter()
                    break
            except AttributeError:
                # empty widget
                pass

        next_letter = self.get_random_letter()
        if next_letter:
            # schedule to start revealing letters
            Clock.schedule_once(
                lambda i: self.tossup_random_letter(next_letter),
                values.interval_tossup)
        else:
            # no more letters on board, end tossup
            self.queue.b.put(('tossup_timeout', None))
            self.tossup_running = False

    def get_random_letter(self):
        """
        Randomly select a LetterLayout
        containing hidden text.
        If none are found, return None.
        """

        shuffled_children = random.sample(
            self.children, len(self.children))
        for child in shuffled_children:
            try:
                if child.layout.hidden() and child.layout.text_label.text:
                    return child.layout
            except AttributeError:
                # empty widget
                pass
        return None

    def tossup_random_letter(self, letter):
        """
        Reveal a random letter,
        then schedule this method to run again.
        """
        if not self.tossup_running:
            return

        # show the letter, choose another
        letter.show_letter()
        letter = self.get_random_letter()

        if letter:
            Clock.schedule_once(
                lambda i: self.tossup_random_letter(letter),
                values.interval_tossup)
        else:
            # no more letters, end tossup
            self.queue.b.put(('tossup_timeout', None))
            self.tossup_running = False

    def pause_tossup(self):
        """
        Pause a tossup.
        """
        self.tossup_running = False

    def _on_keyboard_down(self, _keyboard, keycode, _text, modifiers):
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
    blue_state = BooleanProperty(False)
    white_state = BooleanProperty(False)

    def blue(self, _dt=None):
        """Turn this panel blue."""
        self.blue_state = True
        self.white_state = False

    def white(self):
        """Turn this panel white."""
        self.white_state = True
        self.blue_state = False

    def green(self):
        """Turn this panel to show the WOF logo."""
        self.blue_state = False
        self.white_state = False

    def show_letter(self, _dt=None):
        """Turn the panel white and reveal the letter."""
        self.white()
        opacity = self.text_label.color[3] + values.opacity_adjustment
        if opacity <= 1:
            self.text_label.color = [0, 0, 0, opacity]
        if opacity < 1:
            Clock.schedule_once(self.show_letter, values.opacity_interval)

    def hide(self, _dt=None):
        """Hide the letter on this panel."""
        text = self.text_label.text.lower()
        if text:
            if text not in strings.alphabet:
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

        if self.text_label.text.lower() == letter.lower():
            return True
        else:
            return False


class Panel(Button, KeyboardBindable):
    """A single panel that may contain a letter."""

    layout = ObjectProperty(None)  # a LetterLayout object

    def __init__(self, **kwargs):
        """Create the Panel and bind the click function."""
        super(Panel, self).__init__(**kwargs)

    def click(self):
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
        self.get_keyboard()

    def _on_keyboard_down(self, _keyboard, keycode, _text, modifiers):
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
        elif letter in strings.alphabet + '1234567890-=[]\\;\',./':
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
            self.parent.get_keyboard()
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
                children[i].click()
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
                children[i].click()
                children[i].layout.text_label.text = ''
                break
            except AttributeError:
                # empty panel
                i += 1
        # panel was hidden at the start of this function.
        # if this is the first panel, run click() to show it again:
        if i >= len(children):
            self.click()

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


class PuzzleboardApp(App):
    """Puzzleboard Kivy App"""

    queue = None

    def __init__(self, q=None, **kwargs):
        """
        Create the App.
        `queue` is a CommQueue instance from `manager`.
        """
        super(PuzzleboardApp, self).__init__(**kwargs)
        self.queue = q

    def build(self):
        """Build the app."""

        return PuzzleWithCategory(self.queue)
