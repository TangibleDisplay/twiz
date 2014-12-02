from jnius import PythonJavaClass, java_method, autoclass
print "jnius imports!"

# SERVICE = Autoclass('org.renpy.PythonService').mService
SERVICE = autoclass('org.renpy.android.PythonActivity').mActivity
print "get activity"

Context = autoclass('android.content.Context')
print "get Context"

Intent = autoclass('android.content.Intent')
print "get Intent class"

BluetoothManager = SERVICE.getSystemService(Context.BLUETOOTH_SERVICE)
print "get BluetoothManager"

ADAPTER = BluetoothManager.getAdapter()
print "get ADAPTER"

REQUEST_ENABLE_BT = 0x100

devices = []


def activity_result(request_code, result_code, data):
    print("get result: %s, %s, %s" % (
        request_code == REQUEST_ENABLE_BT, result_code, data))


def start_scanning(callback):
    print "start scanning"
    if not ADAPTER.isEnabled():
        print "not enabled!"
        SERVICE.startActivityForResult(
            Intent(ADAPTER.ACTION_REQUEST_ENABLE), REQUEST_ENABLE_BT)
        print "started activity for result"
        SERVICE.bind(on_activity_result=activity_result)
        print "binded on_activity_result"
    else:
        print "enabled! start leScan"
        ADAPTER.startLeScan(callback)
        print "scan enabled!"


def stop_scanning(callback):
    print "stop leScan"
    ADAPTER.stopLeScan(callback)


def restart_scanning(callback):
    stop_scanning(callback)
    start_scanning(callback)


def update_results(dt):
    for d in devices:
        print d.getName(), d.getUuids(), d.hashCode(), d.getAddress()


class AndroidScanner(PythonJavaClass):
    __javainterfaces__ = ['android.bluetooth.BluetoothAdapter$LeScanCallback']

    @java_method("(Landroid/bluetooth/BluetoothDevice;I[B)V")
    def onLeScan(self, device, irssi, scan_record):
        print "onLeScan"
        print device.getName()
        print irssi
        print len(scan_record), scan_record
        devices.append(device)
