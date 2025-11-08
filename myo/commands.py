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
        """
        Return the command payload.

        Returns:
            payload (bytearray): The command payload bytes (empty by default).
        """
        return bytearray(tuple())

    @property
    def data(self) -> bytearray:
        """
        Return the full command bytes consisting of a 2-byte header followed by the payload.

        Returns:
            bytearray: Header `[cmd, payload_length]` concatenated with the command payload bytes.
        """
        # myohw_command_header_t
        header = bytearray([self.cmd, len(self.payload)])
        return header + self.payload

    def __str__(self) -> str:
        """
        Return a concise, debug-friendly representation of the command.

        Returns:
            A string in the format "ClassName: <payload>" where `<payload>` is the command's payload.
        """
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
        """
        Initialize the SetMode command with specific classifier, EMG, and IMU modes.

        Parameters:
            classifier_mode (ClassifierMode): Mode to set for the on-device classifier.
            emg_mode (EMGMode): Mode to set for EMG sampling/processing.
            imu_mode (IMUMode): Mode to set for the IMU (inertial measurement unit).
        """
        self.classifier_mode = classifier_mode
        self.emg_mode = emg_mode
        self.imu_mode = imu_mode

    @property
    def payload(self) -> bytearray:
        """
        Payload bytes for the SetMode command in EMG, IMU, then Classifier order.

        Returns:
            bytearray: Three-byte payload containing the EMG mode value, the IMU mode value,
                and the Classifier mode value, in that order.
        """
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
        """
        Initialize the Vibrate command with a specified vibration type.

        Parameters:
            vibration_type (VibrationType): Vibration pattern/strength to send to the device.
        """
        self.vibration_type = vibration_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.vibration_type.value,))


# -> myohw_command_deep_sleep_t
class DeepSleep(Command):
    """Command to put the device into deep sleep."""

    cmd: int = 0x04

    def __init__(self) -> None:
        """
        Create a DeepSleep command instance.

        This command requires no parameters and produces no payload;
        it represents a request to put the device into deep sleep.
        """
        pass


# undocumented in myohw.h
class LED(Command):
    """Command to set LED colors (undocumented in myohw.h)."""

    cmd: int = 0x06

    def __init__(self, logo: list[int], line: list[int]):
        """
        Initialize LED command with RGB values for the logo and line LEDs.

        Parameters:
            logo: Three integers [r, g, b] for the logo LED (each 0–255).
            line: Three integers [r, g, b] for the line LED (each 0–255).

        Raises:
            ValueError: If `logo` or `line` does not contain exactly three values.
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
            Create a vibration step with a duration and strength.

            Parameters:
                duration (int): Duration in milliseconds (0–65535).
                strength (int): Vibration strength 0–255 (0 = motor off, 255 = full speed).
            """
            self.duration = duration
            self.strength = strength

    def __init__(self, duration: int, strength: int):
        """
        Create a Vibrate2 command configured with a single vibration step.

        Parameters:
            duration (int): Duration of the vibration in milliseconds (0–65535).
            strength (int): Vibration strength as an unsigned byte (0–255).
        """
        self.steps = self.Steps(duration, strength)

    @property
    def payload(self) -> bytearray:
        """
        Get the three-byte payload for the vibration step: duration high byte, duration low byte, then strength.

        Returns:
            bytearray: Three bytes in order: high byte of `steps.duration`,
                low byte of `steps.duration`, and `steps.strength`.
        """
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
        """
        Initialize the command with the desired device sleep mode.

        Parameters:
            sleep_mode (SleepMode): The sleep mode to apply to the device.
        """
        self.sleep_mode = sleep_mode

    @property
    def payload(self) -> bytearray:
        return bytearray((self.sleep_mode.value,))


# -> myohw_command_unlock_t
class Unlock(Command):
    """Command to unlock the device."""

    cmd: int = 0x0A

    def __init__(self, unlock_type: UnlockType):
        """
        Initialize the Unlock command with the specified unlock type.

        Parameters:
            unlock_type (UnlockType): The unlock action to send to the device; used to construct the command payload.
        """
        self.unlock_type = unlock_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.unlock_type.value,))


class UserAction(Command):
    """Command for user actions."""

    cmd: int = 0x0B

    def __init__(self, user_action_type: UserActionType):
        """
        Initialize a UserAction command with the specified user action type.

        Parameters:
            user_action_type (UserActionType): The action to send to the device as the command payload.
        """
        self.user_action_type = user_action_type

    @property
    def payload(self) -> bytearray:
        return bytearray((self.user_action_type.value,))
