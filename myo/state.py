# -*- coding: utf-8 -*-
from .command import *
from .constants import *
from .vector import Vector
from .quaternion import Quaternion

import struct


class EMG:
    def __init__(self, data=None):
        if data is not None:
            data = struct.unpack("<8HB", data)  # an extra byte for some reason
            self.sample1 = data[:8]
            self.sample2 = data[9:]
        else:
            self.sample1 = list((0, 0, 0, 0))
            self.sample2 = list((0, 0, 0, 0))

    def __str__(self):
        return f"EMG {str(self.sample1) + str(self.sample2)}"


class IMU:
    class Scale:
        ORIENTATION = 16384.0
        ACCELEROMETER = 2048.0
        GYROSCOPE = 16.0

    def __init__(self, data=None):
        if data:
            data = struct.unpack("<hhhhhhhhhh", data)
            self.accel = Vector(*[i / float(self.Scale.ACCELEROMETER) for i in data[4:7]])  # pyright: ignore
            self.gyro = Vector(*[i / float(self.Scale.GYROSCOPE) for i in data[7:]])  # pyright: ignore
            self.quat = Quaternion(*[i / float(self.Scale.ORIENTATION) for i in data[:4]])  # pyright: ignore
        else:
            self.accel = Vector()
            self.gyro = Vector()
            self.quat = Quaternion()

    def __str__(self):
        return f"IMU: {self.quat}"


class Firmware:
    def __init__(self, data):
        data = struct.unpack("4h", data)
        self.major = data[0]
        self.minor = data[1]
        self.patch = data[2]
        self.hardware_rev = HardwareRev(data[3])

    def __str__(self):
        s = str()
        s += str(self.major) + "."
        s += str(self.minor) + "."
        s += str(self.patch) + "."
        s += str(self.hardware_rev.name)  # pyright: ignore
        return s


class HardwareInfo:
    def __init__(self, data):
        data = list(data)
        ser = data[:6]
        ser.reverse()
        ser = [hex(i)[-2:] for i in ser]
        self.serial_number = ":".join(ser).upper()

        self.unlock_pose = Pose(data[6])
        self.active_classifier_type = data[7]
        self.active_classifier_index = data[8]
        self.has_custom_classifier = data[9]
        self.stream_indicating = data[10]
        self.sku = SKU(data[11])

    def __str__(self):
        return str(self.serial_number)


class MotionEvent:
    def __init__(self, data):
        data = struct.unpack("3b", data)
        self.type = MotionEventType(data[0])
        self.dir = data[1]
        self.count = data[2]

    def __str__(self):
        return str(self.type) + " to " + str(self.dir) + " x" + str(self.count)


class MyoState:
    def __init__(self):
        self.arm = Arm.UNKNOWN
        self.emg = EMG()
        self.imu = IMU()
        self.napq = Quaternion(0, 0, 0, 1)
        self.pose = Pose.REST
        self.startq = Quaternion(0, 0, 0, 1)
        self.synced = False
        self.x_direction = XDirection.ELBOW

    @property
    def otn(self):
        if self.pose not in ["rest", "unknown"]:
            return ~self.imu.quat * self.napq
        else:
            return self.imu.quat

    def unsync(self):
        self.arm = Arm.UNSYNC
        self.pose = Pose.UNSYNC
        self.x_direction = XDirection.UNSYNC

    def __str__(self):
        if self.pose not in ["rest", "unknown"]:
            a = ~self.imu.quat * self.napq
            return str(self.pose) + " " + str(a.rpy)
        else:
            a = ~self.imu.quat * self.startq
            return str(a.rpy)
