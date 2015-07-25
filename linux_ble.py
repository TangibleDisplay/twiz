from struct import pack, unpack

try:
    import bluetooth._bluetooth as bluez
except:
    raise ImportError("pybluez is needed on linux")


from threading import Thread

from bt_consts import (
    OGF_LE_CTL,
    OCF_LE_SET_SCAN_ENABLE,
    LE_META_EVENT,
    EVT_LE_ADVERTISING_REPORT,
    ADV_IND,
)


class LinuxBle(object):
    def __init__(self, callback=None):
        try:
            self.sock = sock = bluez.hci_open_dev()
        except:
            raise OSError("error accessing bluetooth device...")

        self.callback = callback or self._print_data

        # perform a device inquiry on bluetooth device #0
        # The inquiry should last 8 * 1.28 = 10.24 seconds
        # before the inquiry is performed, bluez should flush its cache of
        # previously discovered devices
        self.flt = bluez.hci_filter_new()
        bluez.hci_filter_all_events(self.flt)
        bluez.hci_filter_set_ptype(self.flt, bluez.HCI_EVENT_PKT)
        sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, self.flt)

        self.parser_thread = Thread(target=self.parse_events)
        self.parser_thread.daemon = True
        self.parser_thread.start()

    def _print_data(self, *args):
        print(args)

    def start(self):
        self.hci_toggle_le_scan(self.sock, 0x01)

    def stop(self):
        self.hci_toggle_le_scan(self.sock, 0x00)

    def hci_toggle_le_scan(self, sock, enable):
        print "toggle scan: ", enable
        cmd_pkt = pack("<BB", enable, 0x00)
        bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)
        print "sent toggle enable"

    def packed_bdaddr_to_string(self, bdaddr_packed):
        return ':'.join('%02x' % i for i in unpack(
            "<BBBBBB",
            bdaddr_packed[:: -1]))

    def parse_events(self, *args):
        while True:
            pkt = self.sock.recv(255)

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
                        addr = self.packed_bdaddr_to_string(
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
                                d = pkt[offset:]
                                dlen, dtype = unpack('BB', d[:2])
                                if dtype == 0xff and dlen == 17:
                                    sensor_data = unpack(
                                        '>' + 'h' * 7,
                                        d[4:dlen + 1])
                                    if len(sensor_data) == 7:
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

                        self.callback(data)

            elif event == bluez.EVT_CMD_STATUS:
                status, ncmd, opcode = unpack("<BBH", pkt[3:7])
                if status != 0:
                    print "uh oh...", status
