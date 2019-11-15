import queue

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import strings
import values
from my_widgets import Fullscreenable

Builder.load_file(values.file_kv_used_letters)


class LettersWithScore(BoxLayout, Fullscreenable):
    """
    A layout containing three :class:`score.ScoreLayout`\\s and a
    :class:`LetterboardLayout`.
    """

    def __init__(self, q=None, **kwargs):
        """
        Create the layout.

        :param q: A Queue to communicate with the manager app,
                  defaults to None
        :type q: multiprocessing.Queue, optional
        :param kwargs: Additional keyword arguments for the layout
        """

        super(LettersWithScore, self).__init__(**kwargs)

        self.queue = q
        if self.queue:
            Clock.schedule_once(self.check_queue, values.queue_start)

    def check_queue(self, _dt):
        """
        Check the queue for incoming commands to execute.

        Commands should be a tuple of the form:

        (command_string, color_string, args)

        Available commands are:

        'remove_letter':
            Remove the letter *args* from the layout.
            *args* is a single-character string.
            *color_string* is ignored.
        'remove_letters':
            Remove multiple letters from the layout.
            *args* is a list of single-character strings.
            *color_string* is ignored.
        'reload':
            Refill the layout with all letters.
            *color_string* and *args* are ignored.
        'name':
            Change the name of the player specified by *color_string*
            to *args*.
            *args* is a string.
        'score':
            Change the score of the player specified by *color_string*
            to *args*.
            *args* is an integer.
        'total':
            Change the total of the player specified by *color_string*
            to *args*.
            *args is an integer.
        'flash':
            Start the flashing effect for the player specified by
            *color_string*.
            *args* is ignored.
        'stop_flash':
            Stop the flashing effect for the player specified by
            *color_string*.
            *args* is ignored.
        'no_more_consonants':
            Remove all consonants from the layout.
            *color_string* and *args* are ignored.
        'no_more_vowels':
            Remove all vowels from the layout.
            *color_string* and *args* are ignored.
        'exit':
            Close the running App.
            *color_string* and *args* are ignored.

        :param _dt: The time elapsed between scheduling and calling
        :type _dt: float
        :return: None
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
                    c for c in strings.consonants
                    if c not in self.letterboard.unavailable])
            elif command == 'no_more_vowels':
                self.letterboard.unavailable.extend([
                    c for c in strings.vowels
                    if c not in self.letterboard.unavailable])
            elif command == 'exit':
                App.get_running_app().stop()
        except queue.Empty:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)


class LetterboardLayout(GridLayout):
    """
    A layout showing available letters.
    """

    unavailable = ListProperty([])

    def __init__(self, callback=None, unavailable=None, **kwargs):
        """
        Create the layout.
        If a letter is clicked, its text will be sent to `callback`.
        `callback` should be a function accepting a single-character
        string.
        Letters in `unavailable` will not be included in the layout.

        :param callback: Callback function accepting a string, defaults
                         to None
        :type callback: function, optional
        :param unavailable: A list of single-character strings, defaults
                            to None
        :type unavailable: list, optional
        :param kwargs: Additional keyword arguments for the layout
        """

        super(LetterboardLayout, self).__init__(
            rows=len(values.used_letters_layout),
            cols=max(len(row) for row in values.used_letters_layout),
            **kwargs)

        self.callback = callback
        self.unavailable = (
            unavailable if unavailable is not None else [])

        for row in values.used_letters_layout:
            for letter in row:
                if letter.isspace():
                    self.add_widget(Widget())
                else:
                    self.add_widget(LetterboardLetter(text=letter))
            # if rows are not all the same length, fill in with empty space
            for i in range(self.cols - len(row)):
                self.add_widget(Widget())


class LetterboardLetter(ButtonBehavior, Label):
    """
    A single letter in the :class:`LetterboardLayout`.
    """

    pass
