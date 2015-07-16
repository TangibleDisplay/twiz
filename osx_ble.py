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
        print "connecting"
        self.stop_scan()
        self.central.cancelPeripheralConnection_(peripheral)
        self.central.connectPeripheral_options_(peripheral, None, None)

    def disconnecte(self, peripheral):
        # XXX !
        print "Disconnect Not Implemented!"

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

    def stop_scan(self):
        print "stopping scan"
        self.central.stopScan()

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
        name = peripheral.name.cString()
        #name = data.objectForKey_(keys.objectAtIndex_(count - 2)).cString()
        values = data.objectForKey_(keys.objectAtIndex_(count - 1))

        sensor = c.get_from_ptr(values.bytes().arg_ref, 'c', values.length())
        uuid = peripheral.description().cString()
        if self.callback:
            self.callback(rssi.intValue(), name, sensor)
        else:
            print uuid, name, sensor, rssi
        if uuid not in self.peripherals:
            pass
            #self.connect(peripheral)
        self.peripherals[name] = (peripheral, rssi)

    @protocol('CBCentralManagerDelegate')
    def centralManager_didConnectPeripheral_(self, central, peripheral):
        if not peripheral.name.UTF8String():
            return
        peripheral.delegate = self
        CBUUID = autoclass('CBUUID')
        service = CBUUID.UUIDWithString_('1901')
        peripheral.discoverServices_([service])
        #peripheral.discoverServices_(None)
        #check = lambda *x: self.check_services(peripheral)
        #Clock.schedule_interval(check, 1)
        print "started discovery"

    # @protocol('CBCentralManagerDelegate')
    # def centralManager_didConnectPeripheral_(self, central, peripheral):
    #     print "1"
    #     print "known services: ", peripheral.services()
    #     print "2"
    #     if not peripheral.name().UTF8String():
    #         return
    #     CBUUID = autoclass('CBUUID')
    #     #service = CBUUID.UUIDWithString_('00001901-0000-1000-8000-00805f9b34fb')
    #     #peripheral.discoverServices_([service])
    #     peripheral.discoverServices_(None)
    #     check = lambda *x: self.check_services(peripheral)
    #     Clock.schedule_interval(check, 1)
    #     print "started discovery"

    @protocol('CBPeripheralDelegate')
    def peripheral_didDiscoverServices_(self, peripheral, error):
        print peripheral.services
        CBUUID = autoclass('CBUUID')

        for i in range(peripheral.services.count()):
            service = peripheral.services.objectAtIndex_(i)
            if service.UUID.UUIDString.cString() == '1901':
                break
        else:
            assert(0)

        #characteristic = CBUUID.UUIDWithString_('2b01')
        #print characteristic
        # peripheral.discoverCharacteristics_forService_([characteristic], service)
        peripheral.discoverCharacteristics_forService_([], service)

    @protocol('CBPeripheralDelegate')
    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        print "discovered characteristic: ", service, service.characteristics
        for i in range(service.characteristics.count()):
            ch = service.characteristics.objectAtIndex_(i)
            if ch.UUID.UUIDString.cString() == '2B01':
                peripheral.setNotifyValue_forCharacteristic_(True, ch)
                print "set notify for chr {}".format(i)

    @protocol('CBPeripheralDelegate')
    def peripheral_didUpdateNotificationStateForCharacteristic_error_(self, peripheral, characteristic, error):
        # probably needs to decode like for advertising
        # sensor = c.get_from_ptr(values.bytes().arg_ref, 'c', values.length())
        print "characteristic: {} notifying: {}".format(characteristic.UUID.UUIDString.cString(), characteristic.isNotifying)
        pass

    @protocol('CBPeripheralDelegate')
    def peripheral_didUpdateValueForCharacteristic_error_(self, peripheral, characteristic, error):
        # probably needs to decode like for advertising
        # sensor = c.get_from_ptr(values.bytes().arg_ref, 'c', values.length())
        data =  c.get_from_ptr(characteristic.value.bytes().arg_ref, 'c', characteristic.value.length())
        name = peripheral.name.cString()
        rssi = 0
        if self.callback:
            self.callback(rssi, name, data)
        else:
            print name, rsii, data

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
