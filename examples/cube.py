from kivy.app import App
from kivy.lib.osc import listen, bind, readQueue
from kivy.clock import Clock
from kivy.garden import ddd  # noqa
from kivy.lang import Builder

KV = '''
View:
    scene: 'cube.obj'
    display_all: True
    cam_translation: (0, 0, -5)
    scene_scale: 5
    obj_scale: 5
    light_sources:
        {
        1: (0, 0, 1, 1.0),
        2: (0, 1, 0, 1.0),
        3: (0, 1, 1, 1.0),
        4: (1, 0, 0, 1.0),
        5: (1, 0, 1, 1.0),
        6: (1, 1, 0, 1.0),
        7: (1, 0, 1, 1.0),
        7: (1, 1, 1, 1.0),
        }
'''


class CubeApp(App):
    def build(self):
        self.oscid = oscid = listen('0.0.0.0', 8000)
        bind(oscid, self.update_view, '/update')
        Clock.schedule_interval(lambda *x: readQueue(oscid), 0)
        self.root = Builder.load_string(KV)
        return self.root

    def update_view(self, *args):
        self.root.cam_rotation = (x * 180 for x in args[0][2:])


if __name__ == '__main__':
    CubeApp().run()
