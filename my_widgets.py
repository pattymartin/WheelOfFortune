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
    A widget that can attempt to obtain keyboard focus with the method
    :meth:`get_keyboard`.
    Classes that inherit from this class should override the method
    :meth:`_on_keyboard_down` to define what should happen when a key
    is pressed.
    """

    _keyboard = None

    def get_keyboard(self):
        """
        Get keyboard focus.

        :return: None
        """

        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Override this method to define what should happen when a key is
        pressed.

        :param keyboard: A Keyboard
        :type keyboard: kivy.core.window.Keyboard
        :param keycode: An integer and a string representing the keycode
        :type keycode: tuple
        :param text: The text of the pressed key
        :type text: str
        :param modifiers: A list of modifiers
        :type modifiers: list
        :return: True to consume the key, otherwise False
        :rtype: bool
        """

        return False

    def _keyboard_closed(self):
        """
        Remove keyboard binding when the keyboard is closed.

        :return: None
        """

        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None


class FullscreenButton(ModalView):
    """
    A ModalView with a button that will toggle fullscreen mode when
    pressed.
    """

    def toggle_fullscreen(self):
        """
        Toggle fullscreen.

        :return: None
        """

        if Window.fullscreen != 'auto':
            Window.fullscreen = 'auto'
        else:
            Window.fullscreen = False
        self.dismiss()


class Fullscreenable(Widget):
    """
    A Widget that, when right-clicked, will display a
    :class:`FullscreenButton`.
    """

    def on_touch_down(self, touch):
        """
        If a right click is detected, open a context menu with the
        option to make the app fullscreen.
        Otherwise, let the layout handle the touch.

        :param touch: A touch down event
        :type touch: kivy.input.motionevent.MotionEvent
        :return: True if the touch was consumed, otherwise False
        :rtype: bool
        """

        if touch.button == 'right':
            pos_x, pos_y = touch.pos
            FullscreenButton(
                size_hint=(None, 0.1),
                pos_hint={
                    'x': pos_x / self.width,
                    'y': pos_y / self.height}
            ).open()
            return True
        else:
            return super(Fullscreenable, self).on_touch_down(touch)


class TabCyclable(TextInput):
    """
    A TextInput with the attributes `prev_widget` and `next_widget`
    to enable tab cycling.
    """

    def __init__(self, prev_widget=None, next_widget=None, **kwargs):
        """
        Create the widget.
        Keyboard focus will be transferred to `next_widget` if the tab
        key is pressed, or to `prev_widget` if shift+tab is pressed.

        If `prev_widget` or `next_widget` is None, tab cycling will be
        disabled in the backward or forward direction respectively.

        :param prev_widget: The previous widget, defaults to None
        :type prev_widget: kivy.uix.widget.Widget, optional
        :param next_widget: The next widget, defaults to None
        :type next_widget: kivy.uix.widget.Widget, optional
        :param kwargs: Additional keyword arguments for the TextInput
        """

        super(TabCyclable, self).__init__(**kwargs)
        self.prev_widget = prev_widget
        self.next_widget = next_widget

    def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
        """
        If tab or shift+tab is pressed, focus `next_widget` or
        `prev_widget` respectively, and return True.
        Otherwise, let the TextInput handle the key event and return
        False.

        :param keyboard: A Keyboard
        :type keyboard: kivy.core.window.Keyboard
        :param keycode: An integer and a string representing the keycode
        :type keycode: tuple
        :param text: The text of the pressed key
        :type text: str
        :param modifiers: A list of modifiers
        :type modifiers: list
        :return: True if tab is pressed, otherwise False
        """

        if 'tab' in keycode:
            if 'shift' in modifiers and self.prev_widget:
                prev_widget = self.prev_widget
                # skip over the widget if it is disabled
                while prev_widget.disabled:
                    prev_widget = prev_widget.prev_widget
                prev_widget.focus = True
            elif self.next_widget:
                next_widget = self.next_widget
                # skip over the widget if it is disabled
                while next_widget.disabled:
                    next_widget = next_widget.next_widget
                next_widget.focus = True
            return True
        else:
            super(TabCyclable, self).keyboard_on_key_down(
                keyboard, keycode, text, modifiers)
            return False


class Hideable(Widget):
    """
    A Widget with an attribute `visible`.
    When `visible` is changed, the widget will animate itself to be
    hidden or shown appropriately, by changing its width if `horizontal`
    is True, or its height otherwise.
    """

    visible = BooleanProperty(True)

    def __init__(self, horizontal=True, **kwargs):
        """
        Create the widget.

        :param horizontal: True if the widget should be hidden
                           horizontally, False otherwise, defaults to
                           True
        :type horizontal: bool, optional
        :param kwargs: Additional keyword arguments for the widget
        """

        super(Hideable, self).__init__(**kwargs)

        self.start_size_hint = self.size_hint[:]
        self.start_size = self.size[:]
        self.horizontal = horizontal

    def on_visible(self, _instance, value):
        """
        Hide or show the widget, depending on whether `visible` is True
        or False.

        :param _instance: The Hideable instance
        :type _instance: Hideable
        :param value: The new value of `visible`
        :type value: bool
        :return: None
        """

        Animation.cancel_all(self)
        if value:
            self.show()
        else:
            self.hide()

    def show(self):
        """
        Return the widget to its original size.

        :return: None
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

        :return: None
        """

        def make_invisible(_animation, _widget):
            """
            Set the object's opacity and size to 0.
            This is called at the completion of the animation.

            :param _animation: The animation that called this function
            :type _animation: kivy.animation.Animation
            :param _widget: The widget that was animated
            :type _widget: kivy.uix.widget.Widget
            :return: None
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
    A ScreenManager that functions as a timer.
    Buttons in the layout are changed based on the state of the timer.

    The boolean property `final_spin_started` indicates whether the
    final spin button has been clicked.

    The boolean property `running` indicates whether the timer is
    currently running.

    The numeric property `seconds_left` indicates the number of seconds
    left on the timer.

    The numeric property `start_time` indicates the number of seconds
    on the timer before it is started.
    """

    final_spin_started = BooleanProperty(False)
    running = BooleanProperty(False)
    seconds_left = NumericProperty(0)

    def start_stop_reset(self):
        """
        If the timer is paused, start the timer.
        If the timer is running, stop the timer.
        If the time has run out, reset the timer.

        :return: None
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
        Reduce `seconds_left` by `values.timer_accuracy` seconds.
        Then schedule this function in another `values.timer_accuracy`
        seconds.

        :param _dt: The time elapsed between scheduling and calling
        :return: None
        """

        if self.seconds_left <= 0:
            self.running = False

        if self.running:
            self.seconds_left -= values.timer_accuracy
            Clock.schedule_once(self.decrement, values.timer_accuracy)

    def reset(self):
        """
        Reset the timer.

        :return: None
        """

        self.running = False
        self.seconds_left = self.start_time
