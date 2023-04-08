import os

import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

import sbsim.scoreboarding as sb


@pytest.fixture
def data_path():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    top = os.path.join("..", dir_path)
    data = os.path.join(top, "data")
    return data


@pytest.fixture
def test_1_path(data_path):
    file = os.path.join(data_path, "test_1.txt")
    return file


@pytest.fixture
def test_1_parsed_data() -> tuple[dict, dict]:
    """Class parsed data should be like that"""
    functional_units_config = {
        "int": {"n_units": "1", "n_cycle": "1"},
        "mult": {"n_units": "2", "n_cycle": "4"},
        "add": {"n_units": "1", "n_cycle": "2"},
        "div": {"n_units": "1", "n_cycle": "10"},
    }
    instructions_to_execute = {
        "fld": ["f9", "0(x3)"],
        "fmul": ["f7", "f1", "f2"],
        "fadd": ["f4", "f5", "f2"],
        "fdiv": ["f3", "f1", "f7"],
        "fsub": ["f6", "f3", "f4"],
        "fsd": ["f1", "50(x11)"],
    }
    return functional_units_config, instructions_to_execute


@pytest.fixture
def build_instruction_table_1():
    """Table that the first test should return"""
    instructions = ["fld", "fmul", "fadd", "fdiv", "fsub", "fsd"]
    none_table = [None for i in range(len(instructions))]
    table = {
        "instruction": instructions,
        "issue": none_table,
        "read": none_table,
        "ex": none_table,
        "write": none_table,
    }
    return pd.DataFrame(table)


@pytest.fixture
def file_data_1(test_1_path):
    with open(test_1_path, "r") as f:
        return f.read()


@pytest.fixture
def sbobj1(test_1_path):
    return sb.ScoreboardingSIM(test_1_path)


def test_parse_file(sbobj1, test_1_parsed_data):
    print(sbobj1.parse_file())
    assert test_1_parsed_data == sbobj1.parse_file()


def test_build_instruction_table(sbobj1, build_instruction_table_1):
    sbobj1.execute()
    assert_frame_equal(sbobj1.build_instruction_status(), build_instruction_table_1)
