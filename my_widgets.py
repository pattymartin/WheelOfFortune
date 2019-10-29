from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import strings

Builder.load_file(strings.file_kv_my_widgets)

def bind_keyboard(widget):
    """Provide keyboard focus to a widget"""
    
    widget._keyboard = Window.request_keyboard(
        widget._keyboard_closed, widget)
    widget._keyboard.bind(on_key_down=widget._on_keyboard_down)

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
        Otherwise, pass the touch to `super(ManagerLayout, self)`.
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
                self.prev_widget.focus = True
            else:
                self.next_widget.focus = True
            return True
        else:
            super(TabCyclable, self).keyboard_on_key_down(
                window, keycode, text, modifiers)
            return False
