import os

import pytest
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
def file_data_1(test_1_path):
    with open(test_1_path, "r") as f:
        return f.read()


@pytest.fixture
def sbobj1(test_1_path):
    return sb.ScoreboardingSIM(test_1_path)


def test_parse_file(sbobj1):
    print(sbobj1)
    assert 0
