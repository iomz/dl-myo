# -*- coding: utf-8 -*-
"""
# myo/handle.py
#
# reflection from myo-bluetooth/myohw.h
# the names are slightly different in dl-myo
Services = {
    # core service
    0x0001: "ControlService",
    0x0101: "MyoInfoCharacteristic",
    0x0201: "FirmwareVersionCharacteristic ",
    0x0401: "CommandCharacteristic",
    # imu service
    0x0002: "ImuDataService",
    0x0402: "ImuDataCharacteristic",
    0x0502: "MotionEventCharacteristic",
    0x0003: "ClassifierService",
    0x0103: "ClassifierEventCharacteristic",
    # emg service
    0x0005: "EmgDataService",
    0x0105: "EmgData0Characteristic",
    0x0205: "EmgData1Characteristic",
    0x0305: "EmgData2Characteristic",
    0x0405: "EmgData3Characteristic",
    # standard bluetooh device service
    0x180F: "BatteryService",
    0x2A19: "BatteryLevelCharacteristic",
    0x2A00: "DeviceName",
}
"""
import aenum


class Handle(aenum.Enum):
    DEVICE_INFORMATION = 12
    MANUFACTURER_NAME_STRING = 13
    BATTERY_SERVICE = 15
    BATTERY_LEVEL = 16
    CONTROL_SERVICE = 19
    FIRMWARE_INFO = 20
    FIRMWARE_VERSION = 22
    COMMAND = 24
    IMU_SERVICE = 26
    IMU_DATA = 27
    MOTION_EVENT = 30
    CLASSIFIER_SERVICE = 33
    CLASSIFIER_EVENT = 34
    FV_SERVICE = 37
    FV_DATA = 38
    EMG_SERVICE = 41
    EMG0_DATA = 42
    EMG1_DATA = 45
    EMG2_DATA = 48
    EMG3_DATA = 51
    UNKNOWN_SERVICE = 54
    UNKNOWN_CHAR = 55


class UUID:
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
    #   [Characteristic] (Handle: 55): Unknown Characteristic (indicate)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 57): Client Characteristic Configuration, Value: bytearray(b'')
    UNKNOWN_CHAR = "d5060602-a904-deb9-4748-2c7f4a124842"
