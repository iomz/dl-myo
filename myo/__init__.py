"""
    dl-myo
    ------
    Yet another MyoConnect alternative without dongles.
"""
from __future__ import absolute_import, annotations

from .client import MyoClient
from .core import Myo
from .profile import Handle
from .types import (
    ClassifierEvent,
    ClassifierMode,
    EMGData,
    EMGMode,
    FVData,
    FirmwareInfo,
    FirmwareVersion,
    IMUData,
    IMUMode,
    MotionEvent,
    SleepMode,
    UnlockType,
    UserActionType,
    VibrationType,
)
from .version import __version__

__author__ = "Iori Mizutani"
__copyright__ = "Copyright (c) 2023 Iori Mizutani"
__email__ = "iomz@sazanka.io"
__license__ = "GPLv3"
__summary__ = "Yet another MyoConnect alternative without dongles"
__uri__ = "https://github.com/iomz/dl-myo"
