from pyobjus import autoclass, protocol, CArray
from pyobjus.dylib_manager import load_framework, INCLUDE
from kivy.clock import Clock

NSData = autoclass('NSData')

(CBCentralManagerStateUnknown,
 CBCentralManagerStateResetting,
 CBCentralManagerStateUnsupported,
 CBCentralManagerStateUnauthorized,
 CBCentralManagerStatePoweredOff,
 CBCentralManagerStatePoweredOn) = range(6)

c = CArray()


class Ble(object):
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

    @protocol('CBCentralManagerDelegate')
    def centralManagerDidUpdateState_(self, central):
        print 'central state', central.state
        self.check_le(central)
        self.start_scan()

    @protocol('CBCentralManagerDelegate')
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(
            self, central, peripheral, data, rssi):
        keys = data.allKeys()
        count = keys.count()
        if count < 2:
            return
        name = data.objectForKey_(keys.objectAtIndex_(count - 2)).cString()
        values = data.objectForKey_(keys.objectAtIndex_(count - 1))

        sensor = c.get_from_ptr(values.bytes().arg_ref, 'c', values.length())
        uuid = peripheral.description().cString()
        if self.callback:
            self.callback(uuid, rssi.intValue(), name, sensor)
        else:
            print uuid, name, sensor, rssi
        if uuid not in self.peripherals:
            print "connecting"
            self.connect(peripheral)
        self.peripherals[uuid] = (peripheral, rssi)

    @protocol('CBCentralManagerDelegate')
    def centralManager_didConnectPeripheral_(self, central, peripheral):
        if not peripheral.name.UTF8String():
            return
        peripheral.delegate = self
        CBUUID = autoclass('CBUUID')
        #service = CBUUID.UUIDWithString_('00001901-0000-1000-8000-00805f9b34fb')
        #peripheral.discoverServices_([service])
        peripheral.discoverServices_(None)
        #check = lambda *x: self.check_services(peripheral)
        #Clock.schedule_interval(check, 1)
        print "started discovery"

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


if __name__ == '__main__':

    from kivy.app import App
    from kivy.uix.listview import ListView
    from kivy.clock import Clock

    class BleApp(App):
        def build(self):
            self.ble = Ble()
            self.ble.create()
            return ListView()

    BleApp().run()
