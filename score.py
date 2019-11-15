import queue

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty, ListProperty, NumericProperty, StringProperty)
from kivy.uix.relativelayout import RelativeLayout

import values
from my_widgets import Fullscreenable

Builder.load_file(values.file_kv_score)


class ScoreLayout(RelativeLayout, Fullscreenable):
    """A layout displaying a player's score."""
    bg_color = ListProperty(values.color_red)
    name = StringProperty('')
    score = NumericProperty(0)
    total = NumericProperty(0)
    flash_visible = BooleanProperty(False)

    def __init__(self, bg_color=values.color_red, q=None, **kwargs):
        """
        Create the layout.

        :param bg_color: Background color as a tuple of rgba values
                         between 0 and 1, defaults to `values.color_red`
        :type bg_color: tuple, optional
        :param q: Queue to communicate with the manager app, defaults to
                  None
        :type q: multiprocessing.Queue, optional
        :param kwargs: Additional keyword arguments for the layout
        """

        super(ScoreLayout, self).__init__(**kwargs)

        self.flashing = False
        self.bg_color = bg_color
        self.queue = q
        if self.queue:
            Clock.schedule_once(self.check_queue, values.queue_start)

    def check_queue(self, _dt):
        """
        Check the queue for incoming commands to execute.

        Each command in the queue should be a tuple of the form:

        (command_string, args)

        Available commands are:

        'name':
            Set the player's name to *args*.
            *args* is a string.
        'score':
            Set the player's score to *args*.
            *args* is an integer.
        'total':
            Set the player's game total to *args*.
            *args* is an integer.
        'flash':
            Make the layout start flashing to indicate that it is the
            player's turn.
            *args* is ignored.
        'stop_flash':
            Make the layout stop flashing.
            *args* is ignored.
        'exit':
            Close the running app.
            *args* is ignored.

        :param _dt: The time elapsed between scheduling and calling
        :type _dt: float
        :return: None
        """

        try:
            command, args = self.queue.get(block=False)
            if command == 'name':
                self.name = args
            elif command == 'score':
                self.score = args
            elif command == 'total':
                self.total = args
            elif command == 'flash':
                self.flash()
            elif command == 'stop_flash':
                self.flash_visible = False
                self.flashing = False
            elif command == 'exit':
                App.get_running_app().stop()
        except queue.Empty:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)

    def flash(self):
        """
        Start a flashing effect to indicate that it is this player's
        turn.

        :return: None
        """

        def flash_off(_dt):
            """
            Hide the flashing effect.

            :param _dt: The time elapsed between scheduling and calling
            :type _dt: float
            :return: None
            """

            self.flash_visible = False

        def flash_on(_dt=None):
            """
            Show the flashing effect.

            :param _dt: The time elapsed between scheduling and calling,
                        defaults to None
            :type _dt: float, optional
            :return: None
            """

            if self.flashing:
                self.flash_visible = True
                Clock.schedule_once(
                    flash_off, values.interval_score_flash)
                Clock.schedule_once(
                    flash_on, values.interval_score_flash * 2)

        self.flashing = True
        flash_on()
