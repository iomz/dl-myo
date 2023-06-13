import csv
import logging
import os
import pytest
from myo import ClassifierEvent, FVData, IMUData, MotionEvent

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
