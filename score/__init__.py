from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_string("""
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
        font_name: 'Gotham_Black_Regular'
        font_size: self.size[1] / 2
    Label:
        text: '${:,}'.format(self.parent.score)
        font_name: 'Gotham_Black_Regular'
        font_size: self.size[1]
    Label:
        text: '${:,}'.format(self.parent.total)
        font_name: 'Gotham_Black_Regular'
        font_size: self.size[1] / 2
""")

class ScoreLayout(BoxLayout):
    bg_color = ObjectProperty((0, 0, 0, 1))
    name = StringProperty('')
    score = NumericProperty(0)
    total = NumericProperty(0)
    
    def __init__(self, bg_color=(0, 0, 0, 1), queue=None, **kwargs):
        super(ScoreLayout, self).__init__(orientation='vertical', **kwargs)
        self.bg_color = bg_color
        self.queue = queue
        if self.queue:
            Clock.schedule_once(self.check_queue, 5)
    
    def check_queue(self, instance):
        try:
            command, args = self.queue.get(block=False)
            if command == 'name':
                self.name = args
            elif command == 'score':
                self.score = args
            elif command == 'total':
                self.total = args
        except:
            pass
        Clock.schedule_once(self.check_queue, 1)
