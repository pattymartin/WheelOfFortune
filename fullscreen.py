from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget

import strings

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
            pos_hint = {'x': pos_x / self.width, 'y': pos_y / self.height}
            view = ModalView(size_hint=(None, 0.1), pos_hint=pos_hint)
            
            def toggle_fullscreen(instance):
                """Toggle fullscreen."""
                if Window.fullscreen != 'auto':
                    Window.fullscreen = 'auto'
                else:
                    Window.fullscreen = False
                view.dismiss()
            
            button = Button(text=strings.button_fullscreen)
            button.bind(
                on_release=toggle_fullscreen)
            view.add_widget(button)
            view.open()
        else:
            super(Fullscreenable, self).on_touch_down(touch)