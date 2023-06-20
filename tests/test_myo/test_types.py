import csv
import logging
import os
import re

import pytest
from myo.types import ClassifierEvent, EMGData, FirmwareInfo, FirmwareVersion, FVData, IMUData, MotionEvent

logger = logging.getLogger(__name__)


def load_cases(testdata_filename):
    class Case:
        def __init__(self, blob, out):
            self.blob = blob
            self.out = out

    testfile = os.path.join(os.path.dirname(__file__), "test_data", testdata_filename)
    logger.debug(f"loading {testfile}")

    cases = []
    with open(testfile) as f:
        for row in csv.DictReader(f, delimiter=";"):
            cases.append(Case(bytes.fromhex(row["blob"]), row["out"]))

    return cases


def parametrize(name, values):
    # function for readable description
    return pytest.mark.parametrize(name, values, ids=map(repr, values))


@parametrize("case", load_cases("classifier_event.csv"))
def test_classifier_event(case):
    ce = ClassifierEvent(case.blob)
    assert repr(ce) == case.out


@parametrize("case", load_cases("emg_data.csv"))
def test_emg_data(case):
    emg = EMGData(case.blob)
    assert repr(emg.sample1 + emg.sample2) == case.out
    bs = [int(s) for s in re.sub(r'[() ]', '', case.out).split(',')]
    assert emg.json() == str({"sample1": bs[:8], "sample2": bs[8:]}).replace("'", '"')


@parametrize("case", load_cases("fv_data.csv"))
def test_fv_data(case):
    fvd = FVData(case.blob)
    assert repr(fvd) == case.out


@parametrize("case", load_cases("imu_data.csv"))
def test_imu_data(case):
    imud = IMUData(case.blob)
    assert repr(imud) == case.out


@parametrize("case", load_cases("motion_event.csv"))
def test_motion_event(case):
    me = MotionEvent(case.blob)
    assert repr(me) == case.out


@pytest.mark.parametrize(
    "blob,fi_dict",
    [
        (
            bytearray(b'\x8e2\x94\x85;\xd2\x05\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            {
                'serial_number': 'D2:3B:85:94:32:8E',
                'unlock_pose': True,
                'active_classifier_type': 'BUILTIN',
                'active_classifier_index': 0,
                'has_custom_classifier': True,
                'stream_indicating': False,
                'sku': 'UNKNOWN',
            },
        ),  # noqa
    ],
)
def test_firmware_info(blob, fi_dict):
    fi = FirmwareInfo(blob)
    assert fi.to_dict() == fi_dict


@pytest.mark.parametrize(
    "blob,fv_str",
    [
        (bytearray(b'\x01\x00\x05\x00\xb2\x07\x02\x00'), '1.5.1970.REVD'),
    ],
)
def test_firmware_version(blob, fv_str):
    fv = FirmwareVersion(blob)
    assert str(fv) == fv_str
