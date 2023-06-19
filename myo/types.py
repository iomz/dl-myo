"""
    myo.types
    ------------
    Type reflections from myo-bluetooth/myohw.h
"""


import json
import struct

import aenum

from .constants import (
    ACCELEROMETER_SCALE,
    GYROSCOPE_SCALE,
    ORIENTATION_SCALE,
)


class Arm(aenum.Enum):
    RIGHT = 0x01
    LEFT = 0x02
    UNKNOWN = 0xFF


# -> myohw_classifier_event_t
class ClassifierEvent:
    def __init__(self, data):
        # ClassifierEvent is a union
        t = struct.unpack('<6B', data)[0]
        self.t = ClassifierEventType(t)
        if self.t == ClassifierEventType.ARM_SYNCED:
            _, a, x, _, _, _ = struct.unpack("<6B", data)
            self.arm = Arm(a)
            self.x_direction = XDirection(x)
        elif self.t == ClassifierEventType.POSE:
            _, p, _, _, _ = struct.unpack("<BH3B", data)
            self.pose = Pose(p)
        elif self.t == ClassifierEventType.SYNC_FAILED:
            _, s, _, _, _, _ = struct.unpack("<6B", data)
            self.sync_result = SyncResult(s)

    def __repr__(self):
        if self.t == ClassifierEventType.ARM_SYNCED:
            return str((self.t.value, self.arm.value + self.x_direction.value))
        elif self.t == ClassifierEventType.POSE:
            return str((self.t.value, self.pose.value))
        elif self.t == ClassifierEventType.SYNC_FAILED:
            return str((self.t.value, self.sync_result.value))
        return str((self.t.value,))

    def json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        if self.t == ClassifierEventType.ARM_SYNCED:
            return {
                "type": self.t.name,
                "arm": self.arm.name,
                "x-diraction": self.x_direction.name,
            }
        elif self.t == ClassifierEventType.POSE:
            return {"type": self.t.name, "pose": self.pose.name}
        elif self.t == ClassifierEventType.SYNC_FAILED:
            return {"type": self.t.name, "sync-result": self.sync_result.name}
        return {"type": self.t.name}


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
# fmt: off
class ClassifierModelType(aenum.Enum):
    BUILTIN = 0  # Model built into the classifier package.
    CUSTOM = 1   # Model based on personalized user data.
# fmt: on


# -> myohw_emg_data_t (Raw EMG data received in a myohw_att_handle_emg_data_#)
class EMGData:
    def __init__(self, data):
        self.sample1 = struct.unpack("<8b", data[:8])
        self.sample2 = struct.unpack("<8b", data[8:])

    def __str__(self):
        return str(self.sample1 + self.sample2)

    def json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {"sample1": self.sample1, "sample2": self.sample2}


# for the FV_DATA in the old firmware versions (?)
# cf. https://github.com/dzhu/myo-raw/blob/6873d04d647702b304b0592ee25994d196659bb0/myo_raw.py#LL276C11-L276C11
class FVData:
    def __init__(self, data):
        u = struct.unpack('<8Hb', data)
        self.fv = u[:8]
        self.mask = u[8]

    def __repr__(self):
        return str(self.fv + (self.mask,))

    def json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {"fv": self.fv, "mask": self.mask}


# -> myohw_emg_mode_t
# cf. https://github.com/dzhu/myo-raw/issues/17#issuecomment-913140042
# fmt: off
class EMGMode(aenum.Enum):
    NONE = 0x00       # Do not send EMG data.
    SEND_FILT = 0x01  # Send bandpass-filtered && rectified EMG data.
    # noqa            #  - This is a hidden mode in myohw.h.
    # noqa            #  - See FVData for the interpolated type
    SEND_EMG = 0x02   # Send filtered && unrectified EMG data.
    SEND_RAW = 0x03   # Send unfiltered and unrectified EMG data.
    # noqa                  #  - The values are scaled between [-128,127]
# fmt: on


# -> myohw_fw_info_t
class FirmwareInfo:
    def __init__(self, data):
        u = struct.unpack("<6BH12B", data)  # 20 bytes
        ser = list(u[:6])
        ser.reverse()
        ser = [hex(i)[-2:] for i in ser]
        self._serial_number = ":".join(ser).upper()
        self._unlock_pose = Pose(u[6]).name
        self._active_classifier_type = ClassifierModelType(u[7]).name
        self._active_classifier_index = u[8]
        self._has_custom_classifier = bool(u[9])
        self._stream_indicating = bool(u[10])
        self._sku = SKU(u[11]).name
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
        u = struct.unpack("<4H", data)  # 4x uint16_t
        self._major = u[0]
        self._minor = u[1]
        self._patch = u[2]
        self._hardware_rev = HardwareRev(u[3])

    def __str__(self):
        return f"{self._major}.{self._minor}.{self._patch}.{self._hardware_rev.name}"


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
            self.w = w / ORIENTATION_SCALE
            self.x = x / ORIENTATION_SCALE
            self.y = y / ORIENTATION_SCALE
            self.z = z / ORIENTATION_SCALE

        def to_dict(self):
            return {"w": self.w, "x": self.x, "y": self.y, "z": self.z}

    def __init__(self, data):
        u = struct.unpack("<10h", data)
        self.orientation = self.Orientation(u[0], u[1], u[2], u[3])
        self.accelerometer = [v / ACCELEROMETER_SCALE for v in u[4:7]]
        self.gyroscope = [v / GYROSCOPE_SCALE for v in u[7:10]]

    def __repr__(self):
        return str(
            (
                self.orientation.w,
                self.orientation.x,
                self.orientation.y,
                self.orientation.z,
                self.accelerometer,
                self.gyroscope,
            )
        )

    def json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {
            "orientation": self.orientation.to_dict(),
            "accelerometer": self.accelerometer,
            "gyroscope": self.gyroscope,
        }


# -> myohw_imu_mode_t
# fmt: off
class IMUMode(aenum.Enum):
    NONE = 0x00         # Do not send IMU data or events.
    SEND_DATA = 0x01    # Send IMU data streams (accel, gyro, and orientation).
    SEND_EVENTS = 0x02  # Send motion events detected by the IMU (e.g. taps).
    SEND_ALL = 0x03     # Send both IMU data streams and motion events.
    SEND_RAW = 0x04     # Send raw IMU data streams.
# fmt: on


# -> myohw_motion_event_t
class MotionEvent:
    def __init__(self, data):
        t, _, _ = struct.unpack("<3b", data)
        self.t = MotionEventType(t)
        # MotionEvent is a union
        if self.t == MotionEventType.TAP:
            _, td, tc = struct.unpack("<3b", data)
            self.tap_direction = td
            self.tap_count = tc

    def __repr__(self):
        if self.t == MotionEventType.TAP:
            return str((self.t.value, self.tap_direction, self.tap_count))
        else:
            return str((self.t,))

    def json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        if self.t == MotionEventType.TAP:
            return {
                "type": self.t.name,
                "tap-direction": self.tap_direction,
                "tap-count": self.tap_count,
            }
        else:
            return {
                "type": self.t.name,
            }


# -> myohw_motion_event_type_t
class MotionEventType(aenum.Enum):
    TAP = 0x00
    UNKNOWN1 = 0x01
    UNKNOWN2 = 0x02


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
