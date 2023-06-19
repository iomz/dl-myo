"""
    myo.profile
    ------------
    GATTProfile is deducted from the GATT profile
    while Handle is the cleaned-up version used in dl-myo
"""
import aenum


class GATTProfile:
    MYO_SERVICE = "d5060001-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 12): Device Information
    DEVICE_INFORMATION = "0000180a-0000-1000-8000-00805f9b34fb"
    #  [Characteristic] (Handle: 13): Manufacturer Name String (read)
    #                                 Value: bytearray(b'Thalmic Labs')
    MANUFACTURER_NAME_STRING = "00002a29-0000-1000-8000-00805f9b34fb"

    # [Service] (Handle: 15): Battery Service
    BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
    #  [Characteristic] (Handle: 16): Battery Level (read,notify)
    #                                 Value: bytearray(b'[')
    #   [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                (Handle: 18): Client Characteristic Configuration
    #                              Value: bytearray(b'')
    BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"

    # [Service] (Handle: 19): Control Service
    CONTROL_SERVICE = "d5060001-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 20): Firmware Info (read)
    #                                 Value: bytearray
    FIRMWARE_INFO = "d5060101-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 22): Firmware Version (read)
    #                                 Value: bytearray
    FIRMWARE_VERSION = "d5060201-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 24): Command (write)
    COMMAND = "d5060401-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 26): IMU Service
    IMU_SERVICE = "d5060002-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 27): IMU Data (notify)
    #    [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                 (Handle: 29): Client Characteristic Configuration
    #                               Value: bytearray(b'')
    IMU_DATA = "d5060402-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 30): Motion Event (indicate)
    #    [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                 (Handle: 32): Client Characteristic Configuration
    #                               Value: bytearray(b'')
    MOTION_EVENT = "d5060502-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 33): Classifier Service
    CLASSIFIER_SERVICE = "d5060003-a904-deb9-4748-2c7f4a124842"
    #  [Characteristic] (Handle: 34): Classifier Event (indicate)
    #    [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                 (Handle: 36): Client Characteristic Configuration
    #                               Value: bytearray(b'')
    CLASSIFIER_EVENT = "d5060103-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 37): FV Service
    FV_SERVICE = "d5060004-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 38): FV Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                  (Handle: 40): Client Characteristic Configuration
    #                                Value: bytearray(b'')
    FV_DATA = "d5060104-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 41): EMG Service
    EMG_SERVICE = "d5060005-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 42): EMG0 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                  (Handle: 44): Client Characteristic Configuration
    #                                Value: bytearray(b'')
    EMG0_DATA = "d5060105-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 45): EMG1 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                  (Handle: 47): Client Characteristic Configuration
    #                                Value: bytearray(b'')
    EMG1_DATA = "d5060205-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 48): EMG2 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                  (Handle: 50): Client Characteristic Configuration
    #                                Value: bytearray(b'')
    EMG2_DATA = "d5060305-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 51): EMG3 Data (notify)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                  (Handle: 53): Client Characteristic Configuration
    #                                Value: bytearray(b'')
    EMG3_DATA = "d5060405-a904-deb9-4748-2c7f4a124842"

    # [Service] (Handle: 54): Unknown Service
    UNKNOWN_SERVICE = "d5060006-a904-deb9-4748-2c7f4a124842"
    #   [Characteristic] (Handle: 55): Unknown Characteristic (indicate)
    #     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb
    #                  (Handle: 57): Client Characteristic Configuration
    #                                Value: bytearray(b'')
    UNKNOWN_CHAR = "d5060602-a904-deb9-4748-2c7f4a124842"


# fmt: off
class Handle(aenum.Enum):
    DEVICE_INFORMATION = 12  # 0x0c
    MANUFACTURER_NAME_STRING = 13  # 0x0d
    BATTERY_SERVICE = 15     # 0x0f
    BATTERY_LEVEL = 16       # 0x10
    CONTROL_SERVICE = 19     # 0x13
    FIRMWARE_INFO = 20       # 0x14
    FIRMWARE_VERSION = 22    # 0x16
    COMMAND = 24             # 0x18
    IMU_SERVICE = 26         # 0x1a
    IMU_DATA = 27            # 0x1b
    MOTION_EVENT = 30        # 0x1e
    CLASSIFIER_SERVICE = 33  # 0x21
    CLASSIFIER_EVENT = 34    # 0x22
    FV_SERVICE = 37          # 0x25: EMG Filtered Value Service
    FV_DATA = 38             # 0x26: EMG Filtered Value Data
    EMG_SERVICE = 41         # 0x29
    EMG0_DATA = 42           # 0x2a
    EMG1_DATA = 45           # 0x2d
    EMG2_DATA = 48           # 0x30
    EMG3_DATA = 51           # 0x33
    UNKNOWN_SERVICE = 54     # 0x36
    UNKNOWN_CHAR = 55        # 0x37
# fmt: on
