from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import DictProperty, StringProperty, \
    NumericProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock, mainthread
import kivy.garden.ddd  # noqa

from random import randint
import bluetooth._bluetooth as bluez
import sys
from time import time
from struct import pack, unpack
from threading import Thread

from bt_consts import (
    OGF_LE_CTL,
    OCF_LE_SET_SCAN_ENABLE,
    LE_META_EVENT,
    EVT_LE_ADVERTISING_REPORT,
    ADV_SCAN_RSP,
    ADV_IND,
)

dev_id = 0
try:
    sock = bluez.hci_open_dev(dev_id)
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
    focus = StringProperty('giro')


class MidiSensorLine(BoxLayout):
    sensor = StringProperty('')


class OscConfigLine(BoxLayout):
    sensor = StringProperty('')
    ip = StringProperty('')
    port = StringProperty('')
    address = StringProperty('/')
    content = StringProperty('')
    config = ObjectProperty(None)


class ConfigPanel(GridLayout):
    device = ObjectProperty(None)


class MidiConfig(ConfigPanel):
    pass


class OscConfig(ConfigPanel):
    def add_line(self):
        self.ids.content.add_widget(OscConfigLine(config=self))

    def remove_line(self, line):
        self.ids.content.remove_widget(line)


class PloogDevice(FloatLayout):
    active = BooleanProperty(False)
    name = StringProperty('')
    address = StringProperty('')
    power = NumericProperty(0)
    last_update = NumericProperty(0)
    send_osc = BooleanProperty(False)
    send_midi = BooleanProperty(False)
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
            elif False:
                # TODO assign values
                pass
        self.last_update = time()
        self.rx.append((self.rx[-1] + randint(-0xfff, 0xfff)) % 0xffff)
        self.ry.append((self.ry[-1] + randint(-0xfff, 0xfff)) % 0xffff)
        self.rz.append((self.rz[-1] + randint(-0xfff, 0xfff)) % 0xffff)
        self.ax.append((self.ax[-1] + randint(-0xfff, 0xfff)) % 0xffff)
        self.ay.append((self.ay[-1] + randint(-0xfff, 0xfff)) % 0xffff)
        self.az.append((self.az[-1] + randint(-0xfff, 0xfff)) % 0xffff)

        self.rx = self.rx[-100:]
        self.ry = self.ry[-100:]
        self.rz = self.rz[-100:]
        self.ax = self.ax[-100:]
        self.ay = self.ay[-100:]
        self.az = self.az[-100:]

    def on_display(self, *args):
        if not self.display:
            app.remove_visu(self)

        else:
            app.add_visu(self)


class Graph(Widget):
    device = ObjectProperty(None, rebind=True)


class BLEApp(App):
    scan_results = DictProperty({})
    visus = DictProperty({})

    def build(self):
        self.init_ble()
        self.parser_thread = Thread(target=self.parse_events)
        self.parser_thread.daemon = True
        self.parser_thread.start()
        self.set_scanning(True)
        Clock.schedule_interval(self.clean_results, 1)
        return super(BLEApp, self).build()

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

    def set_scanning(self, value):
        if value:
            # hci_le_set_scan_parameters(sock)
            hci_enable_le_scan(sock)
        else:
            hci_disable_le_scan(sock)

    def add_visu(self, device):
        w = ObjectView(device=device)
        self.visus[device] = w
        self.root.ids.visu.ids.content.add_widget(w)

    def remove_visu(self, device):
        w = self.visus.get(device)
        if w and w in self.root.ids.visu.ids.content.children:
            self.root.ids.visu.ids.content.remove_widget(w)

    @mainthread
    def update_device(self, data):
        pd = self.scan_results.get(data['address'], PloogDevice())
        pd.update_data(data)
        results = self.root.ids.scan.ids.results
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
                                report_pkt_offset + 11:
                                report_pkt_offset + 11 + local_name_len]
                            data['name'] = name

                        # elif report_event_type == ADV_DIRECT_IND:
                        #     # print "\tADV_DIRECT_IND"
                        #     pass

                        # elif report_event_type == ADV_SCAN_IND:
                        #     # print "\tADV_SCAN_IND"
                        #     pass

                        # elif report_event_type == ADV_NONCONN_IND:
                        #     # print "\tADV_NONCONN_IND"
                        #     pass

                        elif report_event_type == ADV_SCAN_RSP:
                            # print "\tADV_SCAN_RSP"
                            # print hexlify(pkt)
                            # import pudb; pudb.set_trace()
                            # print r''.join(pkt)
                            if not report_data_length:
                                continue

                            # XXX is this the used one? seems weird it's
                            # different from ADV_IND managed
                            local_name_len, = unpack(
                                "B", pkt[report_pkt_offset + 11])
                            name = pkt[
                                report_pkt_offset + 12:
                                report_pkt_offset + 12 + local_name_len]
                            data['name'] = name
                        else:
                            pass
                            print "\tUnknown or reserved event type"

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
