"""
    myo.commands
    ------------
    The available commands derived from myohw.h
"""

from .types import SleepMode, UnlockType, UserActionType


# myohw_command_t
class Command:
    cmd = 0x00

    @property
    def payload(self) -> bytearray:
        return bytearray(tuple())

    @property
    def data(self) -> bytearray:
        # myohw_command_header_t
        header = bytearray([self.cmd, len(self.payload)])
        return header + self.payload

    def __str__(self):
        return str(type(self).__name__) + ": " + str(self.payload)


# -> myohw_command_set_mode_t
class SetMode(Command):
    cmd = 0x01

    def __init__(self, emg_mode, imu_mode, classifier_mode):
        self.emg_mode = emg_mode
        self.imu_mode = imu_mode
        self.classifier_mode = classifier_mode

    @property
    def payload(self) -> bytearray:
        return bytearray(
            (
                self.emg_mode.value,
                self.imu_mode.value,
                self.classifier_mode.value,
            )
        )


# -> myohw_command_vibrate
class Vibrate(Command):
    cmd = 0x03

    def __init__(self, vibration_type):
        self.vibration_type = vibration_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.vibration_type.value,))


# -> myohw_command_deep_sleep_t
class DeepSleep(Command):
    cmd = 0x04

    def __init__(self):
        pass


# undocumented in myohw.h
class LED(Command):
    cmd = 0x06

    def __init__(self, logo, line):
        """[logoR, logoG, logoB], [lineR, lineG, lineB]"""
        if len(logo) != 3 or len(line) != 3:
            raise Exception("Led data: [r, g, b], [r, g, b]")
        self.logo = logo
        self.line = line

    @property
    def payload(self) -> bytearray:
        return bytearray(self.logo + self.line)


# -> myohw_command_vibrate2_t
class Vibrate2(Command):
    cmd = 0x07

    class Steps:
        def __init__(self, duration, strength):
            # uint16_t: duration (in ms) of the vibration
            self.duration = duration
            # uint8_t: strength of vibration (0 - motor off, 255 - full speed)
            self.strength = strength

    def __init__(self, duration, strength):
        self.steps = self.Steps(duration, strength)

    @property
    def payload(self) -> bytearray:
        return bytearray(
            (
                self.steps.duration >> 0xFF,
                self.steps.duration & 0xFF,
                self.steps.strength,
            )
        )


# -> myohw_command_set_sleep_mode_t
class SetSleepMode(Command):
    cmd = 0x09

    def __init__(self, sleep_mode: SleepMode):
        self.sleep_mode = sleep_mode

    @property
    def payload(self) -> bytearray:
        return bytearray((self.sleep_mode.value,))


# -> myohw_command_unlock_t
class Unlock(Command):
    cmd = 0x0A

    def __init__(self, unlock_type: UnlockType):
        self.unlock_type = unlock_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.unlock_type.value,))


class UserAction(Command):
    cmd = 0x0B

    def __init__(self, user_action_type: UserActionType):
        self.user_action_type = user_action_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.user_action_type.value,))
