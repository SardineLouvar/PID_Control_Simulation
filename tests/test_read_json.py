from backend.api.read_json import extract_row_from_json, get_sorted_json_filepaths 
from backend.api.read_json import file_heading, time_heading, temp_heading, o2_heading, co2_heading, thermal_heading
from datetime import datetime
import pytest
import json

#for mock data
from unittest.mock import mock_open, patch

def patch_open_file(dummy_json):
    with patch("builtins.open", mock_open(read_data=dummy_json)), \
        patch("os.path.basename", return_value="dummy_file.json"):
        result_json = extract_row_from_json("fake/path/dummy_file.json")
    return result_json

def test_does_extract_json():
    """
    Checks that a correctly formatted json file can be extracted properly.
    """

    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": 22,
        "co2": 400,
        "o2": 21,
        "thermal": "5000"
    })

    result_json = patch_open_file(dummy_json)
        
    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: 22,
        co2_heading: 400,
        o2_heading: 21,
        thermal_heading: "5000"
    }

    assert result_json == expected_json


def test_accepts_empty_json():
    """
    Tests case that not all data is provided
    """

    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: None,
        co2_heading: None,
        o2_heading: None,
        thermal_heading: None
    }

    assert result_json == expected_json


# def test_get_sorted_json_filepaths():
#     dummy_filenames = ['10.json', '2.json', '1.json']
#     dummy_script_dir = '/fake/script'
#     dummy_data_dir = '/fake/data'

    