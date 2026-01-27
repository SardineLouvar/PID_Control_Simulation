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


def test_get_sorted_json_filepaths():
    """
    Tests that JSON files are sorted numerically by filename.
    """
    mock_files = ["file_3.json", "file_1.json", "file_2.json"]
    
    with patch("os.listdir", return_value=mock_files), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        filepaths = get_sorted_json_filepaths()
    
    # Verify files are sorted numerically: 1, 2, 3
    assert "file_1.json" in filepaths[0]
    assert "file_2.json" in filepaths[1]
    assert "file_3.json" in filepaths[2]


def test_get_sorted_json_filepaths_with_double_digits():
    """
    Tests that JSON files with double-digit numbers are sorted correctly.
    """
    mock_files = ["file_10.json", "file_2.json", "file_1.json", "file_20.json"]
    
    with patch("os.listdir", return_value=mock_files), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        filepaths = get_sorted_json_filepaths()
    
    # Verify numerical sorting: 1, 2, 10, 20 (not lexicographic)
    assert "file_1.json" in filepaths[0]
    assert "file_2.json" in filepaths[1]
    assert "file_10.json" in filepaths[2]
    assert "file_20.json" in filepaths[3]


def test_extract_row_with_null_values():
    """
    Tests that explicitly null JSON values are handled like missing fields.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": None,
        "co2": None,
        "o2": None,
        "thermal": None
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


def test_extract_row_with_unexpected_data_types():
    """
    Tests that unexpected data types are preserved (no type coercion).
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": "22C",  # String instead of number
        "co2": "400ppm",       # String instead of number
        "o2": 21,
        "thermal": 5000        # Number instead of string
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: "22C",
        co2_heading: "400ppm",
        o2_heading: 21,
        thermal_heading: 5000
    }

    assert result_json == expected_json


def test_extract_row_with_extra_fields():
    """
    Tests that extra/unexpected fields in JSON are ignored.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": 22,
        "co2": 400,
        "o2": 21,
        "thermal": "5000",
        "humidity": 65,          # Extra field
        "pressure": 1013,        # Extra field
        "location": "Room A"     # Extra field
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


def test_get_sorted_json_filepaths_empty_directory():
    """
    Tests that empty directory returns empty list.
    """
    with patch("os.listdir", return_value=[]), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        filepaths = get_sorted_json_filepaths()
    
    assert filepaths == []


def test_get_sorted_json_filepaths_files_without_numbers():
    """
    Tests handling of files that don't contain numbers in their names.
    """
    mock_files = ["fileA.json", "fileB.json"]
    
    with patch("os.listdir", return_value=mock_files), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        # This should raise an AttributeError because re.search returns None
        with pytest.raises(AttributeError):
            get_sorted_json_filepaths()


def test_get_sorted_json_filepaths_mixed_file_types():
    """
    Tests that non-JSON files are still included (function doesn't filter by extension).
    """
    mock_files = ["file_1.json", "file_2.txt", "file_3.csv", "file_4.json"]
    
    with patch("os.listdir", return_value=mock_files), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        filepaths = get_sorted_json_filepaths()
    
    # All files are returned, just sorted numerically
    assert len(filepaths) == 4
    assert "file_1.json" in filepaths[0]
    assert "file_2.txt" in filepaths[1]
    assert "file_3.csv" in filepaths[2]
    assert "file_4.json" in filepaths[3]


def test_extract_row_malformed_json():
    """
    Tests that malformed JSON raises a JSONDecodeError.
    """
    malformed_json = "{ invalid json }"
    
    with patch("builtins.open", mock_open(read_data=malformed_json)):
        with pytest.raises(json.JSONDecodeError):
            extract_row_from_json("fake/path/file.json")


def test_extract_row_with_very_large_numbers():
    """
    Tests that very large numbers are handled correctly.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": 999999.99,
        "co2": 1000000,
        "o2": 100,
        "thermal": 9999999999
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: 999999.99,
        co2_heading: 1000000,
        o2_heading: 100,
        thermal_heading: 9999999999
    }

    assert result_json == expected_json


def test_extract_row_with_zero_and_negative_values():
    """
    Tests that zero and negative values are handled correctly.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": 0,
        "co2": -50,
        "o2": 0.0,
        "thermal": -1000
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: 0,
        co2_heading: -50,
        o2_heading: 0.0,
        thermal_heading: -1000
    }

    assert result_json == expected_json


def test_extract_row_with_scientific_notation():
    """
    Tests that scientific notation values are preserved.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": 1.5e2,      # 150
        "co2": 4.0e2,              # 400
        "o2": 2.1e1,               # 21
        "thermal": 5e3             # 5000
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: 150.0,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }

    assert result_json == expected_json


def test_extract_row_with_boolean_values():
    """
    Tests that boolean values are preserved as-is.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": True,
        "co2": False,
        "o2": 21,
        "thermal": "5000"
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: True,
        co2_heading: False,
        o2_heading: 21,
        thermal_heading: "5000"
    }

    assert result_json == expected_json


def test_extract_row_with_nested_structures():
    """
    Tests that nested arrays/objects are preserved.
    """
    test_time = datetime.now().isoformat()

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": [20, 21, 22],       # Array
        "co2": {"value": 400, "unit": "ppm"},  # Object
        "o2": 21,
        "thermal": "5000"
    })

    result_json = patch_open_file(dummy_json)

    expected_json = {
        file_heading: "dummy_file.json",
        time_heading: test_time,
        temp_heading: [20, 21, 22],
        co2_heading: {"value": 400, "unit": "ppm"},
        o2_heading: 21,
        thermal_heading: "5000"
    }

    assert result_json == expected_json


def test_get_sorted_json_filepaths_case_sensitivity():
    """
    Tests that case sensitivity in file extensions is preserved.
    """
    mock_files = ["file_1.JSON", "file_2.json", "file_3.Json"]
    
    with patch("os.listdir", return_value=mock_files), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        filepaths = get_sorted_json_filepaths()
    
    # All files are returned sorted by number, regardless of case
    assert len(filepaths) == 3
    assert "file_1.JSON" in filepaths[0]
    assert "file_2.json" in filepaths[1]
    assert "file_3.Json" in filepaths[2]


def test_extract_row_with_unicode_filename():
    """
    Tests that Unicode characters in filenames are handled.
    """
    test_time = datetime.now().isoformat()
    unicode_filename = "données_1.json"

    dummy_json = json.dumps({
        "time": test_time,
        "temperature": 22,
        "co2": 400,
        "o2": 21,
        "thermal": "5000"
    })

    with patch("builtins.open", mock_open(read_data=dummy_json)), \
         patch("os.path.basename", return_value=unicode_filename):
        result_json = extract_row_from_json(f"fake/path/{unicode_filename}")

    expected_json = {
        file_heading: unicode_filename,
        time_heading: test_time,
        temp_heading: 22,
        co2_heading: 400,
        o2_heading: 21,
        thermal_heading: "5000"
    }

    assert result_json == expected_json
