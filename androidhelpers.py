from jnius import PythonJavaClass, java_method, autoclass

# SERVICE = Autoclass('org.renpy.PythonService').mService
SERVICE = autoclass('org.renpy.android.PythonActivity').mActivity

Context = autoclass('android.content.Context')

Intent = autoclass('android.content.Intent')

BluetoothManager = SERVICE.getSystemService(Context.BLUETOOTH_SERVICE)

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


def restart_scanning(callback):
    stop_scanning(callback)
    start_scanning(callback)


class AndroidScanner(PythonJavaClass):
    __javainterfaces__ = ['android.bluetooth.BluetoothAdapter$LeScanCallback']
    callback = None

    @java_method("(Landroid/bluetooth/BluetoothDevice;I[B)V")
    def onLeScan(self, device, irssi, scan_record):
        if self.callback:
            self.callback(device.getName(), device.getAddress(), irssi, scan_record)
        else:
            print "no callback set"
            print "onLeScan"
            print device.getName()
            print irssi
            print len(scan_record), scan_record
