from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

import values
from my_widgets import Fullscreenable

Builder.load_string("""
#:import strings strings
#:import values values
<ScoreLayout>:
    size: self.parent.size if self.parent else (100, 100)
    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: self.parent.name
        font_name: values.font_score
        font_size: self.size[1] * values.font_score_name_size
    Label:
        text: strings.currency_format.format(self.parent.score)
        font_name: values.font_score
        font_size: self.size[1] * values.font_score_size
    Label:
        text: strings.currency_format.format(self.parent.total)
        font_name: values.font_score
        font_size: self.size[1] * values.font_score_total_size
""")

class ScoreLayout(BoxLayout, Fullscreenable):
    """A layout displaying a player's score."""
    bg_color = ObjectProperty(values.color_red)
    name = StringProperty('')
    score = NumericProperty(0)
    total = NumericProperty(0)
    flashing = False
    
    def __init__(self, bg_color=values.color_red, queue=None, **kwargs):
        """Create the layout."""
        super(ScoreLayout, self).__init__(orientation='vertical', **kwargs)
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
        # TODO
        print("FLASH")
