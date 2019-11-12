from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import values

Builder.load_file(values.file_kv_my_widgets)


class KeyboardBindable(Widget):
    """
    A widget that can attempt to obtain keyboard focus with the function
    `get_keyboard()`.
    Classes that inherit from this class should override the method
    `_on_keyboard_down` to define what should happen when a key is
    pressed.
    """

    _keyboard = None

    def get_keyboard(self):
        """Get keyboard focus."""
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Override this method to define what should happen when a key is
        pressed.
        """

        pass

    def _keyboard_closed(self):
        """Remove keyboard binding when the keyboard is closed."""
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None


class FullscreenButton(ModalView):
    """
    A button that will toggle fullscreen mode
    when pressed.
    """

    def toggle_fullscreen(self):
        """Toggle fullscreen."""
        if Window.fullscreen != 'auto':
            Window.fullscreen = 'auto'
        else:
            Window.fullscreen = False
        self.dismiss()


class Fullscreenable(Widget):
    """
    A Widget that, when right-clicked,
    will open a ModalView with a button
    that will toggle fullscreen.
    """

    def on_touch_down(self, touch):
        """
        If a right click is detected,
        open a context menu
        with the option to make the app fullscreen.
        Otherwise, let the layout handle the touch.
        """

        if touch.button == 'right':
            pos_x, pos_y = touch.pos
            FullscreenButton(
                size_hint=(None, 0.1),
                pos_hint={
                    'x': pos_x / self.width,
                    'y': pos_y / self.height}
            ).open()
        else:
            super(Fullscreenable, self).on_touch_down(touch)


class TabCyclable(TextInput):
    """
    A TextInput with references to
    `prev_widget` and `next_widget`
    to enable tab cycling.
    """

    def __init__(self, prev_widget=None, next_widget=None, **kwargs):
        super(TabCyclable, self).__init__(**kwargs)
        self.prev_widget = prev_widget
        self.next_widget = next_widget

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if 'tab' in keycode:
            if 'shift' in modifiers:
                prev_widget = self.prev_widget
                # skip over the widget if it is disabled
                while prev_widget.disabled:
                    prev_widget = prev_widget.prev_widget
                prev_widget.focus = True
            else:
                next_widget = self.next_widget
                # skip over the widget if it is disabled
                while next_widget.disabled:
                    next_widget = next_widget.next_widget
                next_widget.focus = True
            return True
        else:
            super(TabCyclable, self).keyboard_on_key_down(
                window, keycode, text, modifiers)
            return False


class Hideable(Widget):
    """
    A Widget with an attribute `visible`.
    When `visible` is changed, the widget will animate itself
    to be hidden or shown appropriately.
    """

    visible = BooleanProperty(True)
    horizontal = BooleanProperty(True)

    def __init__(self, **kwargs):
        """Create the widget"""
        super(Hideable, self).__init__(**kwargs)

        self.start_size_hint = self.size_hint[:]
        self.start_size = self.size[:]

    def on_visible(self, _instance, value):
        """
        Hide or show the widget,
        depending on whether `visible`
        is True or False.
        """

        Animation.cancel_all(self)
        if value:
            self.show()
        else:
            self.hide()

    def show(self):
        """
        Return the widget to its original size.
        """
        self.opacity = 1
        if self.horizontal:
            if self.start_size_hint[0]:
                after = {'size_hint_x': self.start_size_hint[0]}
            else:
                after = {'width': self.start_size[0]}
        else:
            if self.start_size_hint[1]:
                after = {'size_hint_y': self.start_size_hint[1]}
            else:
                after = {'height': self.start_size[1]}

        Animation(**after, d=0.5).start(self)

    def hide(self):
        """
        Hide the widget.
        """

        def make_invisible(_obj, _value):
            """
            Set the object's opacity and size to 0.
            """

            if self.horizontal:
                self.width = 0
            else:
                self.height = 0

            self.opacity = 0

        if self.horizontal:
            if self.start_size_hint[0]:
                after = {'size_hint_x': 0}
            else:
                after = {'width': 0}
        else:
            if self.start_size_hint[1]:
                after = {'size_hint_y': 0}
            else:
                after = {'height': 0}

        animation = Animation(**after, d=0.5)
        animation.bind(on_complete=make_invisible)
        animation.start(self)


class FinalSpinTimer(ScreenManager, Hideable):
    """
    A ScreenManager with a timer,
    which changes buttons based on the state of the timer.
    """

    final_spin_started = BooleanProperty(False)
    running = BooleanProperty(False)
    seconds_left = NumericProperty(0)

    def start_stop_reset(self):
        """
        If the timer is paused, start the timer.
        If the timer is running, stop the timer.
        If the time has run out, reset the timer.
        """

        if self.seconds_left <= 0:
            self.reset()
            return

        self.final_spin_started = False

        self.running = not self.running

        if self.running:
            Clock.schedule_once(self.decrement, values.timer_accuracy)

    def decrement(self, _dt):
        """
        Reduce `seconds_left` by
        `values.timer_accuracy` seconds.
        Then schedule this function in another
        `values.timer_accuracy` seconds.
        """

        if self.seconds_left <= 0:
            self.running = False

        if self.running:
            self.seconds_left -= values.timer_accuracy
            Clock.schedule_once(self.decrement, values.timer_accuracy)

    def reset(self):
        """
        Reset the timer.
        """

        self.running = False
        self.seconds_left = self.start_time
