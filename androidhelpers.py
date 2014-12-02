from jnius import PythonJavaClass, java_method, autoclass

# SERVICE = Autoclass('org.renpy.PythonService').mService
SERVICE = autoclass('org.renpy.PythonActivity').mActivity

Intent = autoclass('android.content.Intent')

BluetoothManager = SERVICE.getSystemService(SERVICE.BLUETOOTH_SERVICE)

ADAPTER = BluetoothManager.getAdapter()

REQUEST_ENABLE_BT = 0x100


def activity_result(request_code, result_code, data):
    print("get result: %s, %s, %s" % (
        request_code == REQUEST_ENABLE_BT, result_code, data))


def start_scanning(callback):
    if not ADAPTER.isEnabled():
        SERVICE.startActivityForResult(
            Intent(ADAPTER.ACTION_REQUEST_ENABLE), REQUEST_ENABLE_BT)
        SERVICE.bind(on_activity_result=activity_result)
    else:
        ADAPTER.startLeScan(callback)


def stop_scanning(callback):
    ADAPTER.stopLeScan(callback)


class AndroidScanner(PythonJavaClass):
    __javainterfaces__ = ['android.bluetooth.BluetoothAdapter$LeScanCallback']

    @java_method('Landroid.bluetooth.BluetoothDevice,I,[B')
    def onLeScan(device, irssi, scan_record):
        print device.getName()
        print irssi
        print scan_record
