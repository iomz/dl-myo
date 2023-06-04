# -*- coding: utf-8 -*-

from aenum import Enum

Services = {
    0x1800: "InfoService",
    0x2A00: "Name",
    0x2A01: "Info1",
    0x2A04: "Info2",
    0x180F: "BatteryService",
    0x2A19: "BatteryLevel",
    0x0001: "ControlService",  # < Myo info service
    0x0101: "HardwareInfo",  # < Serial number for this Myo and various parameters which
    # < are specific to this firmware. Read-only attribute.
    # < See myohw_fw_info_t.
    0x0201: "FirmwareVersion",  # < Current firmware version. Read-only characteristic.
    # < See myohw_fw_version_t.
    0x0401: "Command",  # < Issue commands to the Myo. Write-only characteristic.
    # < See myohw_command_t.
    0x0002: "IMUService",  # < IMU service
    0x0402: "IMUData",  # < See myohw_imu_data_t. Notify-only characteristic. /*
    0x0502: "MotionEvent",  # < Motion event data. Indicate-only characteristic. /*
    0x0003: "ClassifierService",  # < Classifier event service.
    0x0103: "ClassifierEvent",  # < Classifier event data. Indicate-only characteristic. See myohw_pose_t. /***
    0x0005: "EmgDataService",  # < Raw EMG data service.
    0x0105: "EmgData1",  # < Raw EMG data. Notify-only characteristic.
    0x0205: "EmgData2",  # < Raw EMG data. Notify-only characteristic.
    0x0305: "EmgData3",  # < Raw EMG data. Notify-only characteristic.
    0x0405: "EmgData4",  # < Raw EMG data. Notify-only characteristic.
    0x180A: "DeviceInformation",
    0x2A29: "ManufacturerNameString",
}


class UUID(Enum):
    MYO_SERVICE = "d5060001-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 12): Device Information
    DEVICE_INFORMATION = "0000180a-0000-1000-8000-00805f9b34fb"
    #  [Characteristic] (Handle: 13): Manufacturer Name String (read), Value: bytearray(b'Thalmic Labs')
    MANUFACTURER_NAME_STRING = "00002a29-0000-1000-8000-00805f9b34fb"

    # [Service] (Handle: 15): Battery Service
    BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
    #  [Characteristic] (Handle: 16): Battery Level (read,notify), Value: bytearray(b'[')
    #   [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 18): Client Characteristic Configuration, Value: bytearray(b'')
    BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"

    # [Service] (Handle: 19): Control Service
    CONTROL_SERVICE = "d5060001-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 20): Firmware Info (read), Value: bytearray(b'\x8e2\x94\x85;\xd2\x05\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    FIRMWARE_INFO = "d5060101-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 22): Firmware Version (read), Value: bytearray(b'\x01\x00\x05\x00\xb2\x07\x02\x00')
    FIRMWARE_VERSION = "d5060201-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 24): Command (write)
    COMMAND = "d5060401-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 26): IMU Service
    IMU_SERVICE = "d5060002-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 27): IMU Data (notify)
    #    [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 29): Client Characteristic Configuration, Value: bytearray(b'')
    IMU_DATA = "d5060402-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 30): Motion Event (indicate)
    #    [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 32): Client Characteristic Configuration, Value: bytearray(b'')
    MOTION_EVENT = "d5060502-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 33): Classifier Service
    CLASSIFIER_SERVICE = "d5060003-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 34): Classifier Event (indicate)
    #    [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 36): Client Characteristic Configuration, Value: bytearray(b'')
    CLASSIFIER_EVENT = "d5060103-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 37): FV Service
    FV_SERVICE = "d5060004-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 38): FV Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 40): Client Characteristic Configuration, Value: bytearray(b'')
    FV_DATA = "d5060104-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 41): EMG Service
    EMG_SERVICE = "d5060005-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 42): EMG0 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 44): Client Characteristic Configuration, Value: bytearray(b'')
    EMG0_DATA = "d5060105-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 45): EMG1 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 47): Client Characteristic Configuration, Value: bytearray(b'')
    EMG1_DATA = "d5060205-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 48): EMG2 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 50): Client Characteristic Configuration, Value: bytearray(b'')
    EMG2_DATA = "d5060305-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 51): EMG3 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 53): Client Characteristic Configuration, Value: bytearray(b'')
    EMG3_DATA = "d5060405-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 54): Unknown Service
    UNKNOWN_SERVICE = "d5060006-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 55): Unknown Data (indicate)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 57): Client Characteristic Configuration, Value: bytearray(b'')
    UNKNOWN_DATA = "d5060602-a904-deb9-4748-2c7f4a124842"

    def __str__(self):
        return str(self.value)  # pyright: ignore


class Handle(Enum):
    BATTERY = 16
    COMMAND = 24
    NAME = 55
    FIRMWARE_INFO = 20
    FIRMWARE_VERSION = 22
    IMU = 0x1C
    EMG = 0x27
    CLASSIFIER = 0x23


class Arm(Enum):
    UNKNOWN = 0
    RIGHT = 1
    LEFT = 2
    UNSYNC = -1


class ClassifierEvent(Enum):
    SYNC = 1
    UNSYNC = 2
    POSE = 3
    UNLOCK = 4
    LOCK = 5
    SYNCFAIL = 6
    WARMUP = 7


class ClassifierMode(Enum):
    OFF = 0x00
    ON = 0x01


class ClassifierModelType(Enum):
    BUILTIN = 0
    CUSTOM = 1


class EMGMode(Enum):
    OFF = 0x00
    ON = 0x01
    SEND = 0x02
    SEND_RAW = 0x03


class HardwareRev(Enum):
    C = 1
    D = 2


class IMUMode(Enum):
    OFF = 0x00
    DATA = 0x01
    EVENTS = 0x02
    ALL = 0x03
    RAW = 0x04


class MotionEventType(Enum):
    TAP = 0


class Pose(Enum):
    REST = 0
    FIST = 1
    IN = 2
    OUT = 3
    SPREAD = 4
    TAP = 5
    UNSYNC = -1


class SKU(Enum):
    BLACK = 1
    WHITE = 2
    UNKNOWN = 0


class SyncResult(Enum):
    SYNC_FAILED_TOO_HARD = 1


class XDirection(Enum):
    UNKNOWN = 0
    WRIST = 1
    ELBOW = 2
    UNSYNC = -1
