from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.relativelayout import RelativeLayout

import values
from my_widgets import Fullscreenable

Builder.load_string("""
#:import strings strings
#:import values values
<ScoreLayout>:
    flash_visible: False
    size: self.parent.size if self.parent else (100, 100)
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: root.bg_color
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: root.name
            font_name: values.font_score
            font_size: self.size[1] * values.font_score_name_size
        Label:
            text: strings.currency_format.format(root.score)
            font_name: values.font_score
            font_size: self.size[1] * values.font_score_size
        Label:
            text: strings.currency_format.format(root.total)
            font_name: values.font_score
            font_size: self.size[1] * values.font_score_total_size
    Label:
        id: left_bar
        pos_hint: {'x': 0}
        size_hint_x: 0.15
        opacity: 1 if root.flash_visible else 0
        canvas:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
    Label:
        id: right_bar
        pos_hint: {'right': 1}
        size_hint_x: left_bar.size_hint_x
        opacity: left_bar.opacity
        canvas:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
""")

class ScoreLayout(RelativeLayout, Fullscreenable):
    """A layout displaying a player's score."""
    bg_color = ObjectProperty(values.color_red)
    name = StringProperty('')
    score = NumericProperty(0)
    total = NumericProperty(0)
    flashing = False
    
    def __init__(self, bg_color=values.color_red, queue=None, **kwargs):
        """Create the layout."""
        super(ScoreLayout, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.queue = queue
        if self.queue:
            Clock.schedule_once(self.check_queue, values.queue_start)
    
    def check_queue(self, instance):
        """
        Check the queue for incoming commands to execute.
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
        except:
            pass
        Clock.schedule_once(self.check_queue, values.queue_interval)
    
    def flash(self):
        """
        Start a flashing effect
        to indicate that it is this player's turn.
        """
        
        def flash_off(instance):
            """Hide the flashing effect."""
            self.flash_visible = False
        
        def flash_on(instance=None):
            """Show the flashing effect."""
            if self.flashing:
                self.flash_visible = True
                Clock.schedule_once(
                    flash_off, values.score_flash_interval)
                Clock.schedule_once(
                    flash_on, values.score_flash_interval * 2)
        
        self.flashing = True
        flash_on()
