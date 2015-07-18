# http://stackoverflow.com/questions/25434320/windows-8-1-bluetooth-le-cant-get-device-interface
# http://stackoverflow.com/questions/19808624/how-to-connect-to-the-bluetooth-low-energy-device
# http://doxygen.reactos.org/d0/de4/devguid_8h_source.html
# http://pinvoke.net/default.aspx/setupapi.setupdigetclassdevs

from ctypes import CDLL, windll, Structure, Union, POINTER, byref, sizeof, create_unicode_buffer
from ctypes.wintypes import DWORD, WORD, BOOL, BYTE, WCHAR, HANDLE, c_ulong, c_ulonglong, c_int, c_char, TCHAR

BTH_ADDR = c_ulonglong
HDEVINFO = c_int
LPTSTR = POINTER(c_char)

PBYTE = POINTER(BYTE)

SPDRP_DEVICEDESC = DWORD(0x00000000)
SPDRP_HARDWAREID = DWORD(0x00000001)
SPDRP_COMPATIBLEIDS = DWORD(0x00000002)
SPDRP_UNUSED0 = DWORD(0x00000003)
SPDRP_SERVICE = DWORD(0x00000004)
SPDRP_UNUSED1 = DWORD(0x00000005)
SPDRP_UNUSED2 = DWORD(0x00000006)
SPDRP_CLASS = DWORD(0x00000007)
SPDRP_CLASSGUID = DWORD(0x00000008)
SPDRP_DRIVER = DWORD(0x00000009)
SPDRP_CONFIGFLAGS = DWORD(0x0000000A)
SPDRP_MFG = DWORD(0x0000000B)
SPDRP_FRIENDLYNAME = DWORD(0x0000000C)
SPDRP_LOCATION_INFORMATION = DWORD(0x0000000D)
SPDRP_PHYSICAL_DEVICE_OBJECT_NAME = DWORD(0x0000000E)
SPDRP_CAPABILITIES = DWORD(0x0000000F)
SPDRP_UI_NUMBER = DWORD(0x00000010)
SPDRP_UPPERFILTERS = DWORD(0x00000011)
SPDRP_LOWERFILTERS = DWORD(0x00000012)
SPDRP_BUSTYPEGUID = DWORD(0x00000013)
SPDRP_LEGACYBUSTYPE = DWORD(0x00000014)
SPDRP_BUSNUMBER = DWORD(0x00000015)
SPDRP_ENUMERATOR_NAME = DWORD(0x00000016)
SPDRP_SECURITY = DWORD(0x00000017)
SPDRP_SECURITY_SDS = DWORD(0x00000018)
SPDRP_DEVTYPE = DWORD(0x00000019)
SPDRP_EXCLUSIVE = DWORD(0x0000001A)
SPDRP_CHARACTERISTICS = DWORD(0x0000001B)
SPDRP_ADDRESS = DWORD(0x0000001C)
SPDRP_UI_NUMBER_DESC_FORMAT = DWORD(0x0000001D)
SPDRP_DEVICE_POWER_DATA = DWORD(0x0000001E)
SPDRP_REMOVAL_POLICY = DWORD(0x0000001F)
SPDRP_REMOVAL_POLICY_HW_DEFAULT = DWORD(0x00000020)
SPDRP_REMOVAL_POLICY_OVERRIDE = DWORD(0x00000021)
SPDRP_INSTALL_STATE = DWORD(0x00000022)
SPDRP_LOCATION_PATHS = DWORD(0x00000023)

ERROR_INSUFFICIENT_BUFFER = 0x7A
ERROR_INVALID_DATA = 0xD

def new(structure, **kwargs):
    s = structure()
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


class GUID(Structure):
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8)
        ]

GUID_DEVCLASS_BLUETOOTH = new(GUID,
                              Data1=0xE0CBF06C,
                              Data2=0xCD8B,
                              Data3=0x4647,
                              Data4=(BYTE * 8).from_buffer_copy(
                                  bytearray([0xBB, 0x8A, 0x26, 0x3B, 0x43, 0xF0, 0xF9, 0x74])))

DIGCF_DEFAULT = 0x01
DIGCF_PRESENT = 0x02
DIGCF_ALLCLASSES = 0x04
DIGCF_PROFILE = 0x08
DIGCF_DEVINTERFACE = 0x10

class SP_DEVINFO_DATA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("ClassGUID", GUID),
        ("DevInst", DWORD),
        ("Reserved", POINTER(c_ulong))]

class SP_DEVICE_INTERFACE_DATA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", DWORD),
        ("Reserved", POINTER(c_ulong))]

class SP_INTERFACE_DEVICE_DETAIL_DATA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("DevicePath", TCHAR)]

class SYSTEMTIME(Structure):
    _fields_ = [
        ("wYear", WORD),
        ("wMonth", WORD),
        ("wDayOfWeek", WORD),
        ("wDay", WORD),
        ("wHour", WORD),
        ("wMinute", WORD),
        ("wSecond", WORD),
        ("wMilliseconds", WORD)]

class BLUETOOTH_ADDRESS(Union):
    _fields_ = [
        ("ullLong", BTH_ADDR),
        ("rgBytes", BYTE * 6)]

class BLUETOOTH_FIND_RADIO_PARAMS(Structure):
    _fields_ = [
        ("dwSize", DWORD)]

class BLUETOOTH_DEVICE_SEARCH_PARAMS(Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("fReturnAuthenticated", BOOL),
        ("fReturnRemembered", BOOL),
        ("fReturnUnknown", BOOL),
        ("fReturnConnected", BOOL),
        ("fIssueInquiry", BOOL),
        ("cTimeoutMultiplier", c_ulong),
        ("hRadio", HANDLE)]

class BLUETOOTH_DEVICE_INFO(Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("Address", BLUETOOTH_ADDRESS),
        ("ulClassofDevice", c_ulong),
        ("fConnected", BOOL),
        ("fRemembered", BOOL),
        ("fAuthenticated", BOOL),
        ("stLastSeen", SYSTEMTIME),
        ("stLastUsed", SYSTEMTIME),
        ("szName", WCHAR * 248)]


BT = windll.BluetoothAPIs
SAPI = windll.Setupapi
WBAse = windll.Kernel32

GetLastError = WBAse.GetLastError

def list_devices():
    hdi = SAPI.SetupDiGetClassDevsW(
        byref(GUID_DEVCLASS_BLUETOOTH),
        0, 0, DIGCF_PRESENT)

    devinfo_data = new(SP_DEVINFO_DATA, cbSize=sizeof(SP_DEVINFO_DATA))
    i = 0

    while SAPI.SetupDiEnumDeviceInfo(hdi, i, byref(devinfo_data)):
        i += 1
        name = get_device_info(hdi, i, devinfo_data, SPDRP_FRIENDLYNAME)
        if not name.strip().startswith('Twiz'):
            continue

        desc = get_device_info(hdi, i, devinfo_data, SPDRP_DEVICEDESC)
        service = get_device_info(hdi, i, devinfo_data, SPDRP_SERVICE)
        enumerator = get_device_info(hdi, i, devinfo_data, SPDRP_ENUMERATOR_NAME)
        device_class = get_device_info(hdi, i, devinfo_data, SPDRP_CLASS)
        device_class_guid = get_device_info(hdi, i, devinfo_data, SPDRP_CLASSGUID)
        address = get_device_info(hdi, i, devinfo_data, SPDRP_ADDRESS)
        hwid = get_device_info(hdi, i, devinfo_data, SPDRP_HARDWAREID)
        power = get_device_info(hdi, i, devinfo_data, SPDRP_DEVICE_POWER_DATA)

        print '''
             name: {name}
             desc: {desc}
             service: {service}
             enumerator: {enumerator}
             device_class: {device_class}
             device_class_guid: {device_class_guid}
             address: {address}
             hwid: {hwid}
             power: {power}\
            '''.format(
            name=name, desc=desc, service=service,
            enumerator=enumerator, device_class=device_class,
            device_class_guid=device_class_guid, address=address,
            hwid=hwid, power=power)


    gattServiceGUID = GUID('00001901-0000-1000-8000-00805f9b34fb')

    # while SAPI.SetupDiEnumDeviceInterfaes(hdi, None, byref(gattServiceGUID), 
    #     bytesneeded = DWORD()
    #     # first time just to get the needed size, sigh
    #     SAPI.SetupDiGetDeviceInterfaceDetails(
    #         hdi, byref(devinfo_data), None, 0, byref(bytesneeded), None)

    #     class STRUCT(Structure):
    #         _fields_ = [
    #             ("cbSize", DWORD),
    #             ("DevicePath", TCHAR * bytesneeded)]

    #     details = new(STRUCT, cbSize=sizeof(STRUCT))

    #     SAPI.SetupDiGetDeviceInterfaceDetails(
    #         hdi,
    #         byref(devinfo_data),
    #         byref(details),
    #         bytesneeded,
    #         None,
    #         byref(devinfo_data))

    SAPI.SetupDiDestroyDeviceInfoList(hdi)


def get_device_info(hdi, i, devinfo_data, propertyname):
    data_t = DWORD()
    buffer = LPTSTR()
    buffersize = DWORD(0)

    while (
        not SAPI.SetupDiGetDeviceRegistryPropertyW(
            hdi,
            byref(devinfo_data),
            propertyname,
            data_t,
            byref(buffer), # may need a cast (PBYTE)
            # PBYTE(buffer),
            buffersize,
            byref(buffersize)
        )
    ):
        err = GetLastError()
        if err == ERROR_INSUFFICIENT_BUFFER:
            # print buffersize
            # buffer = (c_char * buffersize.value)()
            buffer = create_unicode_buffer(buffersize.value)

        elif err == ERROR_INVALID_DATA:
            break
        else:
            break

    try:
        return buffer.value.decode('utf-8')
    except:
        return ''

list_devices()
