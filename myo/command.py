# -*- coding: utf-8 -*-
from .constants import *


class Command(object):
    cmd = 0x00

    @property
    def value(self):
        return []

    @property
    def data(self):
        return bytearray([self.cmd, len(self)]) + self.bytearray()

    def bytearray(self):
        return bytearray([i for i in self.value])

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return str(type(self).__name__) + ": " + str(self.value)


class DeepSleep(Command):
    cmd = 0x04

    @property
    def value(self):
        return self.data


class LED(Command):
    cmd = 0x06

    def __init__(self, logo, line):
        """[logoR, logoG, logoB], [lineR, lineG, lineB]"""
        if len(logo) != 3 or len(line) != 3:
            raise Exception("Led data: [r, g, b], [r, g, b]")
        self.logo = logo
        self.line = line

    @property
    def value(self):
        return list(self.logo) + list(self.line)


class SetMode(Command):
    cmd = 0x01

    def __init__(self, data, imu=None, classifier=None):
        if hasattr(data, "__iter__"):
            self.emg = EMGMode(data[0])
            self.imu = IMUMode(data[1])
            self.classifier = ClassifierMode(data[2])
        else:
            self.emg = EMGMode(data)  # pyright: ignore
            self.imu = IMUMode(imu)  # pyright: ignore
            self.classifier = ClassifierMode(classifier)  # pyright: ignore

    @property
    def value(self):
        return self.emg.value, self.imu.value, self.classifier.value  # pyright: ignore


class SleepMode(Command):
    cmd = 0x09

    def normal(self):
        self.mode = 0
        return self

    def never(self):
        self.mode = 1
        return self

    def __init__(self, mode=0x00):
        """0 - normal, 1 - never sleep"""
        if mode not in [0, 1]:
            raise Exception("SleepMode: 0 - normal, 1 - never sleep")

        self.mode = mode

    @property
    def value(self):
        return list([self.mode])


class Unlock(Command):
    cmd = 0x0A

    def __init__(self, data=0x02):
        self.data = data  # pyright: ignore

    def lock(self):
        self.data = 0x00  # pyright: ignore
        return self

    def timed(self):
        self.data = 0x01  # pyright: ignore
        return self

    def hold(self):
        self.data = 0x02  # pyright: ignore
        return self

    @property
    def value(self):
        return list([self.data])


class UserAction(Command):
    cmd = 0x0B

    def __init__(self, data=0x00):
        self.data = data  # pyright: ignore

    @property
    def value(self):
        return 0x00


class Vibration(Command):
    cmd = 0x03

    def __init__(self, data, strength=None):
        if type(data) == int:
            if strength is None:
                if data not in range(1, 4):
                    raise Exception("Wrong vibration time")
                self.cmd = 0x03
            else:
                self.cmd = 0x07
            self.duration = data
            self.strength = strength
        elif len(data) == 2:
            self.cmd = 0x07
            self.duration = data[0]
            self.strength = data[1]
        else:
            raise Exception("Wrong data")

    @property
    def value(self):
        if self.cmd == 0x03:
            return list([self.duration])
        elif self.cmd == 0x07:
            return list([self.duration >> 0xFF, self.duration & 0xFF, self.strength])
        else:
            raise Exception("Wrong cmd")
