"""
    myo.commands
    ------------
    The available commands derived from myohw.h
"""

from .types import (
    ClassifierMode,
    EMGMode,
    IMUMode,
    SleepMode,
    UnlockType,
    UserActionType,
    VibrationType,
)


# myohw_command_t
class Command:
    """Base class for all Myo commands."""

    cmd: int = 0x00

    @property
    def payload(self) -> bytearray:
        """Get command payload."""
        return bytearray(tuple())

    @property
    def data(self) -> bytearray:
        """Get complete command data with header."""
        # myohw_command_header_t
        header = bytearray([self.cmd, len(self.payload)])
        return header + self.payload

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.payload}"


# -> myohw_command_set_mode_t
class SetMode(Command):
    """Command to set EMG, IMU, and Classifier modes."""

    cmd: int = 0x01

    def __init__(
        self,
        classifier_mode: ClassifierMode,
        emg_mode: EMGMode,
        imu_mode: IMUMode,
    ):
        self.classifier_mode = classifier_mode
        self.emg_mode = emg_mode
        self.imu_mode = imu_mode

    @property
    def payload(self) -> bytearray:
        """Get payload. Note: payload requires bytearray in this specific order."""
        return bytearray(
            (
                self.emg_mode.value,
                self.imu_mode.value,
                self.classifier_mode.value,
            )
        )


# -> myohw_command_vibrate
class Vibrate(Command):
    """Command to vibrate the device."""

    cmd: int = 0x03

    def __init__(self, vibration_type: VibrationType):
        self.vibration_type = vibration_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.vibration_type.value,))


# -> myohw_command_deep_sleep_t
class DeepSleep(Command):
    """Command to put the device into deep sleep."""

    cmd: int = 0x04

    def __init__(self) -> None:
        pass


# undocumented in myohw.h
class LED(Command):
    """Command to set LED colors (undocumented in myohw.h)."""

    cmd: int = 0x06

    def __init__(self, logo: list[int], line: list[int]):
        """
        Initialize LED command.

        Args:
            logo: RGB values for logo LED [r, g, b] (0-255)
            line: RGB values for line LED [r, g, b] (0-255)

        Raises:
            ValueError: If invalid RGB data is provided
        """
        if len(logo) != 3 or len(line) != 3:
            raise ValueError("LED data must be [r, g, b] format for both logo and line")
        self.logo = logo
        self.line = line

    @property
    def payload(self) -> bytearray:
        return bytearray(self.logo + self.line)


# -> myohw_command_vibrate2_t
class Vibrate2(Command):
    """Command to vibrate with custom duration and strength."""

    cmd: int = 0x07

    class Steps:
        """Vibration step parameters."""

        def __init__(self, duration: int, strength: int):
            """
            Initialize vibration step.

            Args:
                duration: Duration in milliseconds (uint16_t)
                strength: Strength of vibration 0-255 (uint8_t, 0 = motor off, 255 = full speed)
            """
            self.duration = duration
            self.strength = strength

    def __init__(self, duration: int, strength: int):
        """
        Initialize Vibrate2 command.

        Args:
            duration: Duration in milliseconds
            strength: Strength (0-255)
        """
        self.steps = self.Steps(duration, strength)

    @property
    def payload(self) -> bytearray:
        return bytearray(
            (
                (self.steps.duration >> 8) & 0xFF,  # High byte
                self.steps.duration & 0xFF,  # Low byte
                self.steps.strength,
            )
        )


# -> myohw_command_set_sleep_mode_t
class SetSleepMode(Command):
    """Command to set sleep mode."""

    cmd: int = 0x09

    def __init__(self, sleep_mode: SleepMode):
        self.sleep_mode = sleep_mode

    @property
    def payload(self) -> bytearray:
        return bytearray((self.sleep_mode.value,))


# -> myohw_command_unlock_t
class Unlock(Command):
    """Command to unlock the device."""

    cmd: int = 0x0A

    def __init__(self, unlock_type: UnlockType):
        self.unlock_type = unlock_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.unlock_type.value,))


class UserAction(Command):
    """Command for user actions."""

    cmd: int = 0x0B

    def __init__(self, user_action_type: UserActionType):
        self.user_action_type = user_action_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.user_action_type.value,))
