from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import DictProperty, StringProperty, \
    NumericProperty, ListProperty, BooleanProperty, ObjectProperty,\
    ConfigParserProperty
from kivy.clock import Clock, mainthread
import kivy.garden.ddd  # noqa
from kivy.lib.osc.OSC import OSCMessage

from socket import socket, AF_INET, SOCK_DGRAM
from uuid import uuid4 as uuid
from random import gauss
import sys
import rtmidi2
import bluetooth._bluetooth as bluez
from time import time
from struct import pack, unpack
from threading import Thread
import gc

from bt_consts import (
    OGF_LE_CTL,
    OCF_LE_SET_SCAN_ENABLE,
    LE_META_EVENT,
    EVT_LE_ADVERTISING_REPORT,
    ADV_IND,
)

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

try:
    sock = bluez.hci_open_dev()
except:
    print "error accessing bluetooth device..."
    sys.exit(1)


def hci_enable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x01)


def hci_disable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x00)


def hci_toggle_le_scan(sock, enable):
    print "toggle scan: ", enable
    cmd_pkt = pack("<BB", enable, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)
    print "sent toggle enable"


def packed_bdaddr_to_string(bdaddr_packed):
    return ':'.join('%02x' % i for i in unpack(
        "<BBBBBB",
        bdaddr_packed[:: -1]))


class ObjectView(GridLayout):
    device = ObjectProperty(None, rebind=True)


class GraphZone(GridLayout):
    device = ObjectProperty(None, rebind=True)
    focus = StringProperty('accelero')


class DevicesPanel(BoxLayout):
    pass


class ScanPanel(BoxLayout):
    pass


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
            self.device.address + '-midi',
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
            section = self.device.address + '-midi'
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
            self.config.device.address + '-osc', self.key,
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
        for k, v in app.config.items(self.device.address + '-osc'):
            ip, port, address, content = v.split(',')
            self.add_line(
                key=k, ip=ip, port=port, address=address,
                content=content.replace(' ', ','))

    def add_line(self, **kwargs):
        kwargs.setdefault('key', str(uuid()))
        self.ids.content.add_widget(OscConfigLine(config=self, **kwargs))

    def remove_line(self, line):
        self.ids.content.remove_widget(line)
        app.config.remove_option(self.device.address + '-osc', line.key)

    def check_osc_values(self, *args):
        return self.device.check_osc_values(*args)


class PloogDevice(FloatLayout):
    active = BooleanProperty(False)
    name = StringProperty('')
    address = StringProperty('')
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
            if d in ('name', 'address', 'power'):
                setattr(self, d, data[d])

            elif d == 'sensor':
                d = data['sensor']
                self.ax.append(d[0])
                self.ay.append(d[1])
                self.az.append(d[2])

                self.rx.append(d[5])
                self.ry.append(d[4])
                self.rz.append(d[3])

        self.last_update = time()

        self.send_updates()

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
            if c.split('_')[0] not in app.sensor_list:
                print "invalid sensor", c
                return False
        return True

    def send_osc_updates(self):
        sendto = app.osc_socket.sendto
        # XXX potential performances killer, maybe cache these somewhere
        for k, v in app.config.items(self.address + '-osc'):
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
            # print "osc sending data", data
            sendto(data.getBinary(), (ip, int(port)))

    def send_midi_updates(self):
        port = app.midi_out
        items = app.config.items(self.address + '-midi')
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

        else:
            app.add_visu(self)


class PloogSimulator(PloogDevice):
    def __init__(self, **kwargs):
        super(PloogSimulator, self).__init__(**kwargs)
        Clock.schedule_interval(self.simulate_values, .1)

    def simulate_values(self, dt):
        self.update_data(
            {
                'name': 'simulator',
                'address': '00:00:00:00',
                'power': int(gauss(80, 5)),
                'sensor':
                    [
                        gauss(getattr(self, attr)[-1], 1) % 0xffff
                        for attr in app.sensor_list
                    ]
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
    sensor_list = ListProperty(
        ['rx', 'ry', 'rz', 'ax', 'ay', 'az'])
    auto_activate = ConfigParserProperty(
        0, 'general', 'auto_activate', 'app', val_type=int)
    auto_display = ConfigParserProperty(
        0, 'general', 'auto_display', 'app', val_type=int)

    def build(self):
        self.init_ble()
        self.parser_thread = Thread(target=self.parse_events)
        self.parser_thread.daemon = True
        self.parser_thread.start()
        self.set_scanning(True)
        self.osc_socket = socket(AF_INET, SOCK_DGRAM)
        self.midi_out = rtmidi2.MidiOut().open_virtual_port(':0')
        Clock.schedule_interval(self.clean_results, 1)
        if '--simulate' in sys.argv:
            Clock.schedule_once(self.simulate_ploogin, 0)
        return super(BLEApp, self).build()

    def build_config(self, config):
        config.setdefaults('general', {
            'auto_activate': 0,
            'auto_display': 0
            })

    def on_stop(self, *args):
        print "writing config"
        self.config.write()
        print "config written"

    def clean_results(self, dt):
        t = time() - 10  # forget devices after 10 seconds without any update
        for k, v in self.scan_results.items():
            if v.last_update < t:
                self.scan_results.pop(k)
                self.root.ids.scan.ids.results.remove_widget(v)
                self.remove_visu(v)

    def init_ble(self):
        self.old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)

        # perform a device inquiry on bluetooth device #0
        # The inquiry should last 8 * 1.28 = 10.24 seconds
        # before the inquiry is performed, bluez should flush its cache of
        # previously discovered devices
        self.flt = bluez.hci_filter_new()
        bluez.hci_filter_all_events(self.flt)
        bluez.hci_filter_set_ptype(self.flt, bluez.HCI_EVENT_PKT)
        sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, self.flt)

    def simulate_ploogin(self, dt):
        self.root.ids.scan.add_widget(PloogSimulator())

    def set_scanning(self, value):
        if value:
            # hci_le_set_scan_parameters(sock)
            hci_enable_le_scan(sock)
        else:
            hci_disable_le_scan(sock)

    def ensure_sections(self, device):
        section = device.address + '-osc'
        if not self.config.has_section(section):
            app.config.add_section(section)
            app.config.setdefaults(section, {
            })

        section = device.address + '-midi'
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
        pd = self.scan_results.get(data['address'],
                                   PloogDevice(active=app.auto_activate))
        pd.update_data(data)
        results = self.root.ids.scan.ids.results
        if app.auto_display:
            pd.display = True

        if pd.address not in self.scan_results:
            self.scan_results[pd.address] = pd
            results.add_widget(pd)

    def parse_events(self, *args):
        while True:
            pkt = sock.recv(255)

            ptype, event, plen = unpack("BBB", pkt[:3])

            if event == LE_META_EVENT:
                subevent, = unpack("B", pkt[3])
                pkt = pkt[4:]
                # print "LE META EVENT subevent: 0x%02x" %(subevent,)

                if subevent == EVT_LE_ADVERTISING_REPORT:
                    # print "advertising report"
                    num_reports = unpack("B", pkt[0])[0]
                    report_pkt_offset = 0
                    for i in range(0, num_reports):
                        data = {}
                        report_event_type = unpack(
                            "B", pkt[report_pkt_offset + 1])[0]
                        addr = packed_bdaddr_to_string(
                            pkt[report_pkt_offset + 3:report_pkt_offset + 9])
                        report_data_length, = unpack(
                            "B", pkt[report_pkt_offset + 9])
                        data['address'] = addr

                        if report_event_type == ADV_IND:
                            local_name_len, = unpack(
                                "B", pkt[report_pkt_offset + 10])
                            name = pkt[
                                report_pkt_offset + 11 + 1:
                                report_pkt_offset + 11 + local_name_len]
                            data['name'] = name

                            dtype = 0
                            offset = report_pkt_offset + 11 + local_name_len
                            while offset < report_data_length:
                                dlen, dtype = unpack(
                                    'BB', pkt[offset:offset + 2])
                                if dtype == 0xff:
                                    sensor_data = unpack(
                                        '>' + 'h' * ((dlen - 3) // 2),
                                        pkt[offset + 4:offset + dlen + 1])
                                    if len(sensor_data) == 6:
                                        data['sensor'] = sensor_data
                                    break
                                offset += dlen + 1
                        else:
                            pass
                            # print "\tUnknown or reserved event type"

                        # each report is 2 (event type, bdaddr type) + 6
                        # (the address) + 1 (data length field) + data
                        # length + 1 (rssi)
                        report_pkt_offset = \
                            report_pkt_offset + 10 + report_data_length + 1
                        rssi, = unpack("b", pkt[report_pkt_offset - 1])
                        # print "\tRSSI:", rssi
                        data['power'] = rssi

                        self.update_device(data)

            elif event == bluez.EVT_CMD_STATUS:
                status, ncmd, opcode = unpack("<BBH", pkt[3:7])
                if status != 0:
                    print "uh oh...", status

if __name__ == '__main__':
    app = BLEApp()
    app.run()
