# -*- coding: utf-8 -*-
# myo/types.py
# based on myo-bluetooth/myohw.h
import aenum
import json
import struct


class Constant(aenum.NamedConstant):
    ACCELEROMETER_SCALE = 2048.0
    DEFAULT_IMU_SAMPLE_RATE = 50
    EMG_DEFAULT_STREAMING_RATE = 200
    GYROSCOPE_SCALE = 16.0
    ORIENTATION_SCALE = 16384.0


# -> myohw_arm_t
class Arm(aenum.Enum):
    RIGHT = 0x01
    LEFT = 0x02
    UNKNOWN = 0xFF


# -> myohw_classifier_event_t
class ClassifierEvent:
    def __init__(self, data):
        # TODO: fix union
        u = struct.unpack("3B", data)
        self.t = ClassifierEventType(u[0])
        if self.t is ClassifierEventType.ARM_SYNCED:
            self.arm = Arm(u[1])
            self.x_direction = XDirection(u[2])
        elif self.t is ClassifierEventType.POSE:
            u = struct.unpack("1B2H", data)
            self.pose = Pose(u[1])
        elif self.t is ClassifierEventType.SYNC_FAILED:
            self.sync_result = SyncResult(u[1])


# -> myohw_classifier_event_type_t
class ClassifierEventType(aenum.Enum):
    ARM_SYNCED = 0x01
    ARM_UNSYNCED = 0x02
    POSE = 0x03
    UNLOCKED = 0x04
    LOCKED = 0x05
    SYNC_FAILED = 0x06


# -> myohw_classifier_mode_t
class ClassifierMode(aenum.Enum):
    DISABLED = 0x00
    ENABLED = 0x01


# -> myohw_classifier_model_type_t
class ClassifierModelType(aenum.Enum):
    BUILTIN = 0
    CUSTOM = 1


# -> myohw_emg_data_t
class EMGData:
    def __init__(self, data):
        # TODO: check the endian
        # u = struct.unpack("<16b", data)
        u = struct.unpack("16b", data)
        self.sample1 = u[:8]
        self.sample2 = u[8:]

    def __str__(self):
        return str(self.sample1 + self.sample2)

    def json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {"sample1": self.sample1, "sample2": self.sample2}


# -> myohw_emg_mode_t
class EMGMode(aenum.Enum):
    NONE = 0x00
    SEND_EMG = 0x02
    SEND_RAW = 0x03


# -> myohw_fw_info_t
class FirmwareInfo:
    def __init__(self, data):
        u = struct.unpack("6BH12B", data)  # 20 bytes
        assert len(u) == 19
        ser = list(u[:6])
        ser.reverse()
        ser = [hex(i)[-2:] for i in ser]
        self._serial_number = ":".join(ser).upper()
        self._unlock_pose = Pose(u[6]).name  # pyright: ignore
        self._active_classifier_type = ClassifierModelType(u[7]).name  # pyright: ignore
        self._active_classifier_index = u[8]
        self._has_custom_classifier = bool(u[9])
        self._stream_indicating = bool(u[10])
        self._sku = SKU(u[11]).name  # pyright: ignore
        self._reserved = u[12:]

    def to_dict(self):
        return {
            "serial_number": self._serial_number,
            "unlock_pose": self._has_custom_classifier,
            "active_classifier_type": self._active_classifier_type,
            "active_classifier_index": self._active_classifier_index,
            "has_custom_classifier": self._has_custom_classifier,
            "stream_indicating": self._stream_indicating,
            "sku": self._sku,
        }


# -> myohw_fw_version_t
class FirmwareVersion:
    def __init__(self, data):
        u = struct.unpack("4H", data)  # 4x uint16_t
        self._major = u[0]
        self._minor = u[1]
        self._patch = u[2]
        self._hardware_rev = HardwareRev(u[3])

    def __str__(self):
        return f"{self._major}.{self._minor}.{self._patch}.{self._hardware_rev.name}"  # pyright: ignore


# -> myohw_hardware_rev_t
class HardwareRev(aenum.Enum):
    UNKNOWN = 0
    REVC = 1
    REVD = 2
    REVS = 3


# -> myohw_imu_data_t
class IMUData:
    class Orientation:
        def __init__(self, w, x, y, z):
            self.w = w
            self.x = x
            self.y = y
            self.z = z

        def __dict__(self):
            return {"w": self.w, "x": self.x, "y": self.y, "z": self.z}

    def __init__(self, data):
        u = struct.unpack("<10h", data)
        self.orientation = self.Orientation(u[0], u[1], u[2], u[3])
        self.accelerometer = u[4:7]
        self.gyroscope = u[7:10]
        # self.accel = Vector(*[i / float(self.Scale.ACCELEROMETER) for i in data[4:7]])
        # self.gyro = Vector(*[i / float(self.Scale.GYROSCOPE) for i in data[7:]])
        # self.quat = Quaternion(*[i / float(self.Scale.ORIENTATION) for i in data[:4]])

    def json(self):
        return json.dumps(
            {
                "orientation": self.orientation.__dict__(),
                "accelerometer": self.accelerometer,
                "gyroscope": self.gyroscope,
            }
        )


# -> myohw_imu_mode_t
class IMUMode(aenum.Enum):
    NONE = 0x00
    SEND_DATA = 0x01
    SEND_EVENTS = 0x02
    SEND_ALL = 0x03
    SEND_RAW = 0x04


# -> myohw_motion_event_t
class MotionEvent:
    def __init__(self, data):
        # TODO: fix union?
        u = struct.unpack("3b", data)
        self.t = MotionEventType(u[0])
        self.tap_direction = u[1]
        self.tap_count = u[2]


# -> myohw_motion_event_type_t
class MotionEventType(aenum.Enum):
    TAP = 0x00


# -> myohw_pose_t
class Pose(aenum.Enum):
    REST = 0x0000
    FIST = 0x0001
    WAVE_IN = 0x0002
    WAVE_OUT = 0x003
    FINGERS_SPREAD = 0x0004
    DOUBLE_TAP = 0x0005
    UNKNOWN = 0xFFFF


# -> myohw_sku_t
class SKU(aenum.Enum):
    UNKNOWN = 0
    BLACK = 1
    WHITE = 2


# -> myohw_sleep_mode_t
class SleepMode(aenum.Enum):
    NORMAL = 0
    NEVER_SLEEP = 1


# -> myohw_sync_result_t
class SyncResult(aenum.Enum):
    FAILED_TOO_HARD = 0x01


# -> myohw_unlock_type_t
class UnlockType(aenum.Enum):
    LOCK = 0x00
    TIMED = 0x01
    HOLD = 0x02


# -> myohw_user_action_type_t
class UserActionType(aenum.Enum):
    SINGLE = 0


# -> myohw_vibration_type_t
class VibrationType(aenum.Enum):
    NONE = 0x00
    SHORT = 0x01
    MEDIUM = 0x02
    LONG = 0x03


# -> myohw_x_direction_t
class XDirection(aenum.Enum):
    TOWARD_WRIST = 0x01
    TOWARD_ELBOW = 0x02
    DIRECTION_UNKNOWN = 0xFF
