from pyobjus import autoclass, protocol, CArray
from pyobjus.dylib_manager import load_framework, INCLUDE

NSData = autoclass('NSData')

(CBCentralManagerStateUnknown,
 CBCentralManagerStateResetting,
 CBCentralManagerStateUnsupported,
 CBCentralManagerStateUnauthorized,
 CBCentralManagerStatePoweredOff,
 CBCentralManagerStatePoweredOn) = range(6)

c = CArray()


class Ble(object):
    @protocol('CBCentralManagerDelegate')
    def centralManagerDidUpdateState_(self, central):
        print 'central state', central.state
        self.check_le(central)
        self.start_scan()

    @protocol('CBCentralManagerDelegate')
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(
            self, central, peripheral, data, rssi):
        keys = data.allKeys()
        if keys.count() < 2:
            return
        name = data.objectForKey_(keys.objectAtIndex_(0)).cString()
        values = data.objectForKey_(keys.objectAtIndex_(1))

        sensor = c.get_from_ptr(values.bytes().arg_ref, 'c', values.length())
        uuid = peripheral.description().cString()
        if self.callback:
            self.callback(uuid, rssi.intValue(), name, sensor)
        else:
            print uuid, name, sensor, rssi
        self.peripherals[uuid] = (peripheral, rssi)

    def check_le(self, central):
        state = central.state
        if state == CBCentralManagerStateUnknown:
            print 'CentralManager: Unknown state'
        elif state == CBCentralManagerStatePoweredOn:
            print 'CentralManager: Ready to go!'
            return True
        elif state == CBCentralManagerStatePoweredOff:
            print 'CentralManager: Bluetooth is powered off'
        elif state == CBCentralManagerStateUnauthorized:
            print 'CentralManager: The application is not authorized to use BLE'
        elif state == CBCentralManagerStateUnsupported:
            print 'CentralManager: This hardware doesnt support BLE'

    def connect(self, peripheral):
        self.central.connectPeripheral_options(peripheral, None, None)

    @protocol('CBCentralManagerDelegate')
    def centralManager_didConnectPeripheral(self, central, peripheral):
        value = NSData.dataWithBytes(0b100, 1)
        characteristic = 0x0014
        # 0 = with_response, 1 = without_response
        write_type = 1

        peripheral.writeValue_forCharacteristic_type_(
            value, characteristic, write_type)

        peripheral.setNotifyValue(True, characteristic)

    @protocol('CBPeripheralDelegate')
    def peripheral_didUpdateNotificationStateForCharacteristic_(peripheral, characteristic):
        # probably needs to decode like for advertising
        # sensor = c.get_from_ptr(values.bytes().arg_ref, 'c', values.length())
        print "received new value for characteristic!", characteristic.value
        pass

    def create(self):
        self.callback = None
        self.peripherals = {}
        load_framework(INCLUDE.IOBluetooth)
        CBCentralManager = autoclass('CBCentralManager')
        self.central = CBCentralManager.alloc().initWithDelegate_queue_(
            self, None)

    def start_scan(self):
        print 'Scanning started'
        self.central.scanForPeripheralsWithServices_options_(None, None)


if __name__ == '__main__':

    from kivy.app import App
    from kivy.uix.listview import ListView
    from kivy.clock import Clock

    class BleApp(App):
        def build(self):
            self.ble = Ble()
            self.ble.create()
            #Clock.schedule_interval(self.update_peripherals, 1)
            return ListView()

        def update_peripherals(self, *args):
            items = []
            for uuid, infos in self.ble.peripherals.items():
                peripheral, rssi = infos
                states = ('Disconnected', 'Connecting', 'Connected')
                state = states[peripheral.state]
                name = ''
                if peripheral.name:
                    name = peripheral.name.cString()
                desc = '{} | State={} | Name={} | RSSI={}db'.format(
                    uuid,
                    state,
                    name,
                    peripheral.readRSSI() if state == 'Connected' else rssi)
                items += [desc]
            self.root.item_strings = items

    BleApp().run()
