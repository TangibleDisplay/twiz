from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import DictProperty, StringProperty, \
    NumericProperty, ListProperty, BooleanProperty, ObjectProperty,\
    ConfigParserProperty
from kivy.clock import Clock, mainthread
from kivy.animation import Animation
import ddd  # noqa
from kivy.lib.osc.OSC import OSCMessage
from kivy.utils import platform
from kivy.core.window import Window
Window.softinput_mode = 'resize'

from socket import socket, AF_INET, SOCK_DGRAM
from uuid import uuid4 as uuid
from random import random, randint, gauss
import sys
try:
    import rtmidi2
except:
    rtmidi2 = None

from time import time
from struct import pack, unpack
import gc

if platform == 'android':
    from androidhelpers import AndroidScanner, start_scanning, stop_scanning
elif platform == 'macosx':
    from osx_ble import Ble
elif platform == 'linux':
    from linux_ble import LinuxBle

__version__ = '1.0'

MIDI_SIGNALS = {
    176: 'Control',
    128: 'Note Off',
    144: 'Note On',
    224: 'Note Aftertouch',
    'Control': 176,
    'Note Off': 128,
    'Note On': 144,
    'Note Aftertouch': 224,
}

def configbool(value):
    if isinstance(value, basestring):
        return value.lower() not in ('false', 'no', '')
    return bool(value)


class ObjectView(GridLayout):
    device = ObjectProperty(None, rebind=True)


class GraphZone(GridLayout):
    device = ObjectProperty(None, rebind=True)
    focus = StringProperty('accelero')


class MidiSensorLine(BoxLayout):
    sensor = StringProperty('')
    device = ObjectProperty(None, rebind=True)
    active = BooleanProperty(False)
    signal = StringProperty('')
    chan = StringProperty('')
    event_id = StringProperty('')
    event_value = StringProperty('')

    def __init__(self, **kwargs):
        super(MidiSensorLine, self).__init__(**kwargs)
        self.bind(
            active=self.update,
            chan=self.update,
            signal=self.update,
            event_id=self.update,
            event_value=self.update
        )
        self.load_values()

    def update(self, *args):
        app.config.set(
            self.device.name + '-midi',
            self.sensor,
            '%s,%s,%s,%s,%s' % (
                1 if self.active else 0,
                MIDI_SIGNALS.get(self.signal, ''),
                self.chan,
                self.event_id,
                self.event_value
            )
        )

    def load_values(self, *args):
        if self.device and self.sensor:
            section = self.device.name + '-midi'
            values = app.config.get(section, self.sensor)
            active, signal, chan, event_id, event_value = values.split(',')
            self.active = True if active == '1' else False
            self.signal = MIDI_SIGNALS.get(int(signal), 'Note On')
            self.chan = chan
            self.event_id = event_id
            self.event_value = event_value


class OscConfigLine(BoxLayout):
    key = StringProperty('')
    ip = StringProperty('localhost')
    port = StringProperty('')
    address = StringProperty('/')
    content = StringProperty('')
    config = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(OscConfigLine, self).__init__(**kwargs)
        self.bind(ip=self.update,
                  port=self.update,
                  address=self.update,
                  content=self.update)

    def update(self, *args):
        app.config.set(
            self.config.device.name + '-osc', self.key,
            '%s,%s,%s,%s' %
            (self.ip, self.port, self.address, self.content.replace(',', ' ')))


class ConfigPanel(GridLayout):
    device = ObjectProperty(None)


class MidiConfig(ConfigPanel):
    def on_device(self, *args):
        if self.device:
            self.ids.content.clear_widgets()
            for s in app.sensor_list:
                self.ids.content.add_widget(
                    MidiSensorLine(sensor=s, device=self.device))


class OscConfig(ConfigPanel):
    device = ObjectProperty(None, rebind=True)

    def on_device(self, *args):
        if self.device:
            self.load_config(self.device)

    def load_config(self, device):
        for k, v in app.config.items(self.device.name + '-osc'):
            ip, port, address, content = v.split(',')
            self.add_line(
                key=k, ip=ip, port=port, address=address,
                content=content.replace(' ', ','))

    def add_line(self, **kwargs):
        kwargs.setdefault('key', str(uuid()))
        self.ids.content.add_widget(OscConfigLine(config=self, **kwargs))

    def remove_line(self, line):
        self.ids.content.remove_widget(line)
        app.config.remove_option(self.device.name + '-osc', line.key)

    def check_osc_values(self, *args):
        return self.device.check_osc_values(*args)


class TwizDevice(FloatLayout):
    active = BooleanProperty(False)
    name = StringProperty('')
    power = NumericProperty(0)
    last_update = NumericProperty(0)
    display = BooleanProperty(False)
    rx = ListProperty([0, ])
    ry = ListProperty([0, ])
    rz = ListProperty([0, ])
    cx = ListProperty([0, ])
    cy = ListProperty([0, ])
    cz = ListProperty([0, ])
    ax = ListProperty([0, ])
    ay = ListProperty([0, ])
    az = ListProperty([0, ])

    def update_data(self, data):
        for d in data:
            if d in ('name', 'power'):
                setattr(self, d, data[d])

            elif d == 'sensor':
                d = data['sensor']
                self.ax = (self.ax + [d[0]])[-100:]
                self.ay = (self.ay + [d[1]])[-100:]
                self.az = (self.az + [d[2]])[-100:]

                self.rx = (self.rx + [d[5]])[-100:]
                self.ry = (self.ry + [d[4]])[-100:]
                self.rz = (self.rz + [d[3]])[-100:]

        self.last_update = time()

        self.send_updates()

    def on_active(self, *args):
        if self.active:
            app.ensure_sections(self)

    def send_updates(self):
        if not self.active:
            return

        self.send_osc_updates()
        self.send_midi_updates()

    def check_osc_values(self, ip, port, address, content):
        try:
            int(port)
        except ValueError:
            print "invalid port", port
            return False
        if not address.startswith('/'):
            print "invalid address", address
            return False
        for c in content.split(' '):
            if c.isdigit() or c.startswith("'") and c.endswith("'"):
                continue
            if c.split('_')[0] not in app.sensor_list + ['id']:
                print "invalid sensor", c
                return False
        return True

    def send_osc_updates(self):
        sendto = app.osc_socket.sendto
        # XXX potential performances killer, maybe cache these somewhere
        app.ensure_sections(self)

        for k, v in app.config.items(self.name + '-osc'):
            ip, port, address, content = v.split(',')
            if not self.check_osc_values(ip, port, address, content):
                continue
            data = OSCMessage()
            data.setAddress(address)
            for i in content.split(' '):
                i = i.strip()
                if i.isdigit():
                    data.append(int(i))
                elif i.startswith("'"):
                    data.append(i.strip("'"))
                else:
                    if '_' in i:
                        d, t = i.split('_')
                        i = d
                        if t == 'd':
                            func = lambda x: float(x) / 0xffff
                        else:
                            func = lambda x: x
                    else:
                        func = lambda x: x

                    if i in app.sensor_list:
                        data.append(func(getattr(self, i)[-1]))

                    elif i == 'id':
                        data.append(self.name)

            # print "osc sending data", data
            sendto(data.getBinary(), (ip, int(port)))

    def send_midi_updates(self):
        if not rtmidi2:
            return
        port = app.midi_out
        items = app.config.items(self.name + '-midi')
        for k, v in items:
            active, signal, chan, ev_id, ev_value = v.split(',')
            if not active == '1':
                continue
            value = getattr(self, k)[-1] >> 9
            message = (int(x) for x in (
                signal, chan, ev_id.replace('v', '') or value,
                ev_value.replace('v', '') or value))
            message = tuple(message)
            # print "sending message %s" % (message,)
            port.send_message(message)

    def on_display(self, *args):
        if not self.display:
            app.remove_visu(self)
            app.scanner.disconnect(app.scanner.peripherals[self.name][0])

        else:
            app.add_visu(self)
            app.scanner.connect(app.scanner.peripherals[self.name][0])


class TwizSimulator(TwizDevice):
    values = ListProperty([0, 0, 0, 0, 0, 0])

    def __init__(self, **kwargs):
        super(TwizSimulator, self).__init__(**kwargs)
        self.simulate_values()

    def simulate_values(self, *args):
        a = Animation(
            values=[randint(0, 0xffff) for x in app.sensor_list],
            d=random() * 3,
            t='in_out_sine')
        a.bind(on_complete=self.simulate_values)
        a.start(self)

    def on_values(self, *args):
        self.update_data(
            {
                'name': 'simulator',
                'power': int(gauss(80, 5)),
                'sensor': self.values
            }
        )


class Graph(Widget):
    device = ObjectProperty(None, rebind=True)
    line_x = ListProperty([], rebind=True)
    line_y = ListProperty([], rebind=True)
    line_z = ListProperty([], rebind=True)
    data_len = NumericProperty(0)


class BLEApp(App):
    scan_results = DictProperty({})
    visus = DictProperty({})
    error_log = StringProperty('')
    sensor_list = ListProperty(
        ['rx', 'ry', 'rz', 'ax', 'ay', 'az'])
    auto_activate = ConfigParserProperty(
        0, 'general', 'auto_activate', 'app', val_type=int)
    auto_display = ConfigParserProperty(
        0, 'general', 'auto_display', 'app', val_type=int)
    device_filter = ConfigParserProperty(
        '', 'general', 'device_filter', 'app', val_type=str)
    nexus4_fix = ConfigParserProperty(
        False, 'android', 'nexus4_fix', 'app', val_type=configbool)

    def build(self):
        self.init_ble()
        self.set_scanning(True)
        self.osc_socket = socket(AF_INET, SOCK_DGRAM)
        if rtmidi2:
            self.midi_out = rtmidi2.MidiOut().open_virtual_port(':0')
        Clock.schedule_interval(self.clean_results, 1)
        if '--simulate' in sys.argv:
            Clock.schedule_once(self.simulate_twiz, 0)
        return super(BLEApp, self).build()

    def on_pause(self, *args):
        return True

    def build_config(self, config):
        config.setdefaults('general', {
            'auto_activate': 0,
            'auto_display': 0
            })
        config.setdefaults('android', {
            'nexus4_fix': 0,
            })

    def build_settings(self, settings):
        settings.add_json_panel(
            'Twiz-manager',
            self.config,
            'twiz_manager.json'
            )

    def on_stop(self, *args):
        print "writing config"
        self.config.write()
        print "config written"

    def open_content_dropdown(self, text_input):
        options = {
            'euler angles (0-0xffff)': 'rx,ry,rz',
            'euler angles (0-1.0)': 'rx_d,ry_d,rz_d',
            'accelerations (0-0xffff)': 'ax,ay,az',
            'accelerations (0-1.0)': 'ax_d,ay_d,az_d',
            'accelerations + euler (0-0xffff)': 'ax,ay,az,rx,ry,rz',
            'accelerations + euler (0-1.0)': 'ax_d,ay_d,az_d,rx_d,ry_d,rz_d',
        }

        #d = DropDown(width=text_input.width)
        #for o in options:
        #    b = Button(text=o, size_hint_y=None)
        #    b.bind(texture_size=b.setter('size'))
        #    b.bind(on_press=lambda x: text_input.setter('text')(options[o]))
        #    d.add_widget(b)

        #d.open(text_input)

        p = Popup(title='message content', size_hint=(.9, .9))

        def callback(option):
            text_input.text = options.get(option, option)
            p.dismiss()

        content = GridLayout(spacing=10, cols=1)
        for o in options:
            b = Button(text=o)
            b.bind(on_press=lambda x: callback(x.text))
            content.add_widget(b)

        instructions = Label(
            text='custom content:\n two types of sensors are '
            'proposed, rotation (euler angles) and acceleration, each '
            'in 3 axis: rx, ry and rz represent rotation values, ax, '
            'ay and az represent acceleration values, any value can '
            'take a "_d" suffix, to be casted to a value between 0 '
            'and 1 instead of the default (from 0 to 0xffff', size_hint_y=None)
        instructions.bind(
            size=instructions.setter('text_size'),
            texture_size=instructions.setter('size'))
        content.add_widget(instructions)
        ti = TextInput(
            text=text_input.text,
            multiline=False,
            input_type='text',
            keyboard_suggestions=False)
        content.add_widget(ti)
        b = Button(text='set custom')
        b.bind(on_press=lambda x: callback(ti.text))
        content.add_widget(b)

        p.add_widget(content)
        p.open()

    def clean_results(self, dt):
        t = time() - 10  # forget devices after 10 seconds without any update
        for k, v in self.scan_results.items():
            if v.last_update < t:
                self.scan_results.pop(k)
                self.root.ids.scan.ids.results.remove_widget(v)
                self.remove_visu(v)

    def init_ble(self):
        if platform == 'android':
            self.scanner = AndroidScanner()
            self.scanner.callback = self.android_parse_event

        elif platform == 'macosx':
            self.scanner = Ble()
            self.scanner.create()
            self.scanner.callback = self.osx_parse_event
            self.scanner.queue = []

        else:
            self.scanner = LinuxBle(callback=self.update_device)

    def simulate_twiz(self, dt):
        self.root.ids.scan.add_widget(TwizSimulator())

    def filter_scan_result(self, result):
        return self.device_filter.strip().lower() in result.lower()

    def restart_scanning(self, dt):
        self.scanning_active = not self.scanning_active
        if self.scanning_active:
            stop_scanning(self.scanner)
        else:
            start_scanning(self.scanner)

    def set_scanning(self, value):
        if platform == 'android':
            if value:
                start_scanning(self.scanner)
                if app.nexus4_fix:
                    self.scanning_active = True
                    Clock.schedule_interval(self.restart_scanning, .05)
            else:
                stop_scanning(self.scanner)
                Clock.unschedule(self.restart_scanning)

        elif platform == 'macosx':
            self.scanner.start_scan()

        else:
            if value:
                # hci_le_set_scan_parameters(sock)
                self.scanner.start()
            else:
                self.scanner.stop()

    def ensure_sections(self, device):
        section = device.name + '-osc'
        if not self.config.has_section(section):
            app.config.add_section(section)
            app.config.setdefaults(section, {
            })

        section = device.name + '-midi'
        if not self.config.has_section(section):
            app.config.add_section(section)
            app.config.setdefaults(section, {
                k: '0,0,0,0,v'
                for k in app.sensor_list
            })

    def add_visu(self, device):
        self.ensure_sections(device)
        w = ObjectView(device=device)
        self.visus[device] = w
        self.root.ids.visu.ids.content.add_widget(w)

    def remove_visu(self, device):
        w = self.visus.get(device)
        if w and w in self.root.ids.visu.ids.content.children:
            self.root.ids.visu.ids.content.remove_widget(w)
            del(self.visus[device])
            gc.collect()

    @mainthread
    def update_device(self, data):
        pd = self.scan_results.get(data.get('name', ''),
                                   TwizDevice(active=app.auto_activate))
        pd.update_data(data)
        results = self.root.ids.scan.ids.results
        if app.auto_display:
            pd.display = True

        if pd.name not in self.scan_results:
            self.scan_results[pd.name] = pd
            results.add_widget(pd)

    def decode_data(self, pkt):
        pkt = pack('<' + 'b' * len(pkt), *pkt.tolist())
        local_name_len, = unpack("B", pkt[0])

        dtype = 0
        offset = 1 + local_name_len
        sensor_data = None
        while offset < len(pkt):
            dlen, dtype = unpack(
                'BB', pkt[offset:offset + 2])
            if dtype == 0xff:
                sensor_data = unpack(
                    '>' + 'h' * ((dlen - 3) // 2),
                    pkt[offset + 4:offset + dlen + 1])
                break
            offset += dlen + 1
        return sensor_data

    def android_parse_event(self, name, address, irssi, data):
        if not name or not self.filter_scan_result(name):
            return

        device_data = {
            'name': name,
            'power': irssi,
            }
        try:
            sensor = self.decode_data(data)
        except:
            self.error_log += 'error decoding data from %s:%s\n' % (
                name,
                unpack('<' + 'B' * len(data),
                       pack('<' + 'b' * len(data), data)))

        if sensor:
            device_data['sensor'] = sensor

        self.update_device(device_data)

    def osx_parse_event(self, rssi, name, values):
        if len(values) > 12:
            values = values[2:]
        device_data = {
            'name': name,
            'power': rssi,
            'sensor': unpack('>' + 'h' * (len(values) / 2), ''.join(values)),
        }

        self.update_device(device_data)


if __name__ == '__main__':
    app = BLEApp()
    import cProfile
    cProfile.run('app.run()', 'ble.profile')
