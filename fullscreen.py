from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget

import strings

Builder.load_file(strings.file_kv_fullscreen)

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
