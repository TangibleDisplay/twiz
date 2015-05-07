from pyobjus import autoclass, protocol, CArray
from pyobjus.dylib_manager import load_framework, INCLUDE
from kivy.clock import Clock
from pprint import pprint as pp

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
        if uuid not in self.peripherals:
            self.connect(peripheral)
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
        self.central.cancelPeripheralConnection_(peripheral)
        self.central.connectPeripheral_options_(peripheral, None, None)

    @protocol('CBCentralManagerDelegate')
    def centralManager_didConnectPeripheral_(self, central, peripheral):
        print "1"
        print "known services: ", peripheral.services()
        print "2"
        if not peripheral.name().UTF8String():
            return
        CBUUID = autoclass('CBUUID')
        #service = CBUUID.UUIDWithString_('00001901-0000-1000-8000-00805f9b34fb')
        #peripheral.discoverServices_([service])
        peripheral.discoverServices_(None)
        check = lambda *x: self.check_services(peripheral)
        Clock.schedule_interval(check, 1)
        print "started discovery"

    def check_services(self, peripheral):
        services = peripheral.services()
        print "check ", services
        if services:
            for s in range(services.count()):
                service = services.objectAtIndex_(s)
                if service in self.asked_services:
                    continue
                print service.UUID().data
                self.asked_services.append(service)
                CBUUID = autoclass('CBUUID')
                # characteristic = CBUUID.UUIDWithString_('00002b01-0000-1000-8000-00805f9b34fb')
                peripheral.discoverCharacteristics_forService_(None, service)
                check = lambda *x: self.check_characteristics(peripheral, service)
                Clock.schedule_interval(check, 1)
            return False

    def check_characteristics(self, peripheral, service):
        characteristics = service.characteristics()
        if characteristics:
            for c in range(characteristics.count()):
                print "setting notif for char %s of %s" % (c, service)
                characteristic = characteristics.objectAtIndex_(c)
                peripheral.setNotifyValue_forCharacteristic_(True, characteristic)
            check_value = lambda *x: self.check_value(peripheral, characteristic)
            Clock.schedule_interval(check_value, 0)
            return False

    def check_value(self, peripheral, characteristic):
        value = characteristic.value()
        if value:
            sensor = c.get_from_ptr(value.bytes().arg_ref, 'c', value.length())
            name = peripheral.name().cString()
            uuid = peripheral.description().cString()
            self.callback(uuid, 0, name, sensor)

    @protocol('CBPeripheralDelegate')
    def peripheral_didDiscoverServices_(self, peripheral, error):
        print peripheral.services
        CBUUID = autoclass('CBUUID')
        characteristic = CBUUID.UUIDWithString_('00002b01-0000-1000-00805f9')
        print characteristic
        peripheral.discoverCharacteristics_forService_([characteristic], service)

    @protocol('CBPeripheralDelegate')
    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        print "discovered characteristic: ", service, service.characteristics
        peripheral.setNotifyValue_forCharacteristic_(True, characteristic)

    @protocol('CBPeripheralDelegate')
    def peripheral_didUpdateNotificationStateForCharacteristic_error_(peripheral, characteristic):
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
        self.asked_services = []
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
