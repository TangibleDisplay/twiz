from pyobjus import autoclass, protocol, dereference, CArray
from pyobjus.dylib_manager import load_framework, INCLUDE
NSString = autoclass('NSString')
NSNumber = autoclass('NSNumber')
NSDictionary = autoclass('NSDictionary')

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
            self.callback(uuid, rssi, name, sensor)
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

    def create(self):
        self.callback = None
        self.peripherals = {}
        load_framework(INCLUDE.IOBluetooth)
        CBCentralManager = autoclass('CBCentralManager')
        self.central = CBCentralManager.alloc().initWithDelegate_queue_(
                self, None)

    def start_scan(self):
        print 'Scanning started'
        key = NSString.alloc().initWithUTF8String_(
            'kCBScanOptionAllowDuplicates')
        value = NSNumber.numberWithInt_(1)
        options = NSDictionary.alloc().initWithObjectsAndKeys_(
            value, key, None) 
        self.central.scanForPeripheralsWithServices_options_(None, options)


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
