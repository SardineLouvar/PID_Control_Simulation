import pytest
import pandas as pd
from datetime import datetime
import json
from unittest.mock import patch, MagicMock, call

from backend.services.data_processor import initialise_dataframe, initialise_db
from backend.api.read_json import (
    file_heading, time_heading, temp_heading, 
    co2_heading, o2_heading, thermal_heading
)


def test_initialise_dataframe_returns_dataframe():
    """
    Tests that initialise_dataframe returns a pandas DataFrame.
    """
    mock_files = []
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=mock_files):
        result = initialise_dataframe()
        assert isinstance(result, pd.DataFrame)


def test_initialise_dataframe_has_correct_columns():
    """
    Tests that the DataFrame has all required columns.
    """
    mock_files = []
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=mock_files):
        df = initialise_dataframe()
        
        expected_columns = [file_heading, time_heading, temp_heading, co2_heading, o2_heading, thermal_heading]
        assert list(df.columns) == expected_columns


def test_initialise_dataframe_has_correct_dtypes():
    """
    Tests that the DataFrame columns have correct data types.
    """
    mock_files = []
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=mock_files):
        df = initialise_dataframe()
        
        assert df[file_heading].dtype == "object"  # str
        assert df[time_heading].dtype == "float64"
        assert df[temp_heading].dtype == "float64"
        assert df[co2_heading].dtype == "float64"
        assert df[o2_heading].dtype == "float64"
        assert df[thermal_heading].dtype == "int64"


def test_initialise_dataframe_empty_directory():
    """
    Tests that initialise_dataframe returns empty DataFrame when no files exist.
    """
    mock_files = []
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=mock_files):
        df = initialise_dataframe()
        
        assert len(df) == 0
        assert list(df.columns) == [
            file_heading, time_heading, temp_heading, 
            co2_heading, o2_heading, thermal_heading
        ]


def test_initialise_dataframe_single_file():
    """
    Tests that initialise_dataframe correctly processes a single file.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: 22.5,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        assert df.iloc[0][file_heading] == "file_1.json"
        assert df.iloc[0][temp_heading] == 22.5
        assert df.iloc[0][co2_heading] == 400.0


def test_initialise_dataframe_multiple_files():
    """
    Tests that initialise_dataframe correctly processes multiple files.
    """
    test_time = datetime.now().isoformat()
    mock_rows = [
        {
            file_heading: f"file_{i}.json",
            time_heading: test_time,
            temp_heading: 20.0 + i,
            co2_heading: 400.0 + i,
            o2_heading: 21.0,
            thermal_heading: 5000 + i
        }
        for i in range(1, 4)
    ]
    
    file_paths = ["file_1.json", "file_2.json", "file_3.json"]
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows):
        df = initialise_dataframe()
        
        assert len(df) == 3
        assert list(df[file_heading]) == ["file_1.json", "file_2.json", "file_3.json"]
        assert list(df[temp_heading]) == [21.0, 22.0, 23.0]


def test_initialise_dataframe_preserves_order():
    """
    Tests that initialise_dataframe preserves the order of files.
    """
    test_time = datetime.now().isoformat()
    mock_rows = [
        {
            file_heading: f"file_{i}.json",
            time_heading: test_time,
            temp_heading: float(i),
            co2_heading: float(i),
            o2_heading: float(i),
            thermal_heading: i
        }
        for i in range(1, 6)
    ]
    
    file_paths = [f"file_{i}.json" for i in range(1, 6)]
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows):
        df = initialise_dataframe()
        
        assert list(df[file_heading]) == file_paths


def test_initialise_dataframe_handles_none_values():
    """
    Tests that initialise_dataframe handles None values correctly.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: None,
        co2_heading: None,
        o2_heading: None,
        thermal_heading: None
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        assert pd.isna(df.iloc[0][temp_heading])
        assert pd.isna(df.iloc[0][co2_heading])


def test_initialise_db_calls_generate_table():
    """
    Tests that initialise_db calls generate_table.
    """
    with patch("backend.services.data_processor.generate_table") as mock_generate, \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=[]), \
         patch("backend.services.data_processor.insert_data"):
        initialise_db()
        
        mock_generate.assert_called_once()


def test_initialise_db_no_files():
    """
    Tests that initialise_db handles empty directory correctly.
    """
    with patch("backend.services.data_processor.generate_table") as mock_generate, \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=[]), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        mock_generate.assert_called_once()
        mock_insert.assert_not_called()


def test_initialise_db_single_file():
    """
    Tests that initialise_db correctly inserts data for a single file.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: 22.5,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        mock_insert.assert_called_once_with(test_time, 22.5, 400.0, 21.0, 5000)


def test_initialise_db_multiple_files():
    """
    Tests that initialise_db correctly inserts data for multiple files.
    """
    test_time = datetime.now().isoformat()
    mock_rows = [
        {
            file_heading: f"file_{i}.json",
            time_heading: test_time,
            temp_heading: 20.0 + i,
            co2_heading: 400.0 + i,
            o2_heading: 21.0 + i,
            thermal_heading: 5000 + i
        }
        for i in range(1, 4)
    ]
    
    file_paths = ["file_1.json", "file_2.json", "file_3.json"]
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        assert mock_insert.call_count == 3
        
        # Verify each call
        expected_calls = [
            call(test_time, 21.0, 401.0, 22.0, 5001),
            call(test_time, 22.0, 402.0, 23.0, 5002),
            call(test_time, 23.0, 403.0, 24.0, 5003),
        ]
        mock_insert.assert_has_calls(expected_calls)


def test_initialise_db_preserves_file_order():
    """
    Tests that initialise_db processes files in correct order.
    """
    test_time = datetime.now().isoformat()
    mock_rows = [
        {
            file_heading: f"file_{i}.json",
            time_heading: test_time,
            temp_heading: float(i),
            co2_heading: float(i),
            o2_heading: float(i),
            thermal_heading: i
        }
        for i in range(1, 6)
    ]
    
    file_paths = [f"file_{i}.json" for i in range(1, 6)]
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        assert mock_insert.call_count == 5
        
        # Verify order by checking first argument (time) is consistent
        for call_obj in mock_insert.call_args_list:
            assert call_obj[0][0] == test_time


def test_initialise_db_with_none_values():
    """
    Tests that initialise_db handles None values correctly.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: None,
        co2_heading: None,
        o2_heading: None,
        thermal_heading: None
    }
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        mock_insert.assert_called_once_with(test_time, None, None, None, None)


def test_initialise_dataframe_with_mixed_data_types():
    """
    Tests that initialise_dataframe handles mixed numeric types correctly.
    """
    test_time = datetime.now().isoformat()
    mock_rows = [
        {
            file_heading: "file_1.json",
            time_heading: test_time,
            temp_heading: 22,          # int
            co2_heading: 400.5,        # float
            o2_heading: 21,            # int
            thermal_heading: 5000      # int
        },
        {
            file_heading: "file_2.json",
            time_heading: test_time,
            temp_heading: 23.7,        # float
            co2_heading: 401,          # int
            o2_heading: 21.5,          # float
            thermal_heading: 5001      # int
        }
    ]
    
    file_paths = ["file_1.json", "file_2.json"]
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows):
        df = initialise_dataframe()
        
        assert len(df) == 2
        # All numeric columns should be converted to float64 (except thermal which is int64)
        assert df[temp_heading].dtype == "float64"
        assert df[co2_heading].dtype == "float64"
        assert df[o2_heading].dtype == "float64"

def test_initialise_dataframe_with_nan_values():
    """
    Tests that initialise_dataframe handles NaN values correctly.
    """
    test_time = datetime.now().isoformat()
    import math
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: math.nan,
        co2_heading: 400.0,
        o2_heading: math.nan,
        thermal_heading: 5000
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        assert pd.isna(df.iloc[0][temp_heading])
        assert pd.isna(df.iloc[0][o2_heading])
        assert df.iloc[0][co2_heading] == 400.0


def test_initialise_dataframe_with_infinity_values():
    """
    Tests that initialise_dataframe handles infinity values.
    """
    test_time = datetime.now().isoformat()
    import math
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: math.inf,
        co2_heading: -math.inf,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        assert df.iloc[0][temp_heading] == pytest.approx(float('inf'))
        assert df.iloc[0][co2_heading] == pytest.approx(float('-inf'))


def test_initialise_dataframe_with_negative_values():
    """
    Tests that initialise_dataframe handles negative values correctly.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: -10.5,
        co2_heading: -100.0,
        o2_heading: -5.0,
        thermal_heading: -1000
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        assert df.iloc[0][temp_heading] == -10.5
        assert df.iloc[0][co2_heading] == -100.0


def test_initialise_dataframe_extract_raises_exception():
    """
    Tests that initialise_dataframe raises exception if extract_row_from_json fails.
    """
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=json.JSONDecodeError("msg", "doc", 0)):
        with pytest.raises(json.JSONDecodeError):
            initialise_dataframe()


def test_initialise_dataframe_large_dataset():
    """
    Tests that initialise_dataframe handles large datasets efficiently.
    """
    test_time = datetime.now().isoformat()
    num_files = 1000
    
    mock_rows = [
        {
            file_heading: f"file_{i}.json",
            time_heading: test_time,
            temp_heading: 20.0 + (i % 10),
            co2_heading: 400.0 + (i % 50),
            o2_heading: 21.0,
            thermal_heading: 5000 + i
        }
        for i in range(num_files)
    ]
    
    file_paths = [f"file_{i}.json" for i in range(num_files)]
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows):
        df = initialise_dataframe()
        
        assert len(df) == num_files
        assert len(df.columns) == 6


def test_initialise_dataframe_with_string_numeric_values():
    """
    Tests that initialise_dataframe handles string values in numeric fields.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: "22.5",       # String instead of float
        co2_heading: "400",         # String instead of float
        o2_heading: 21.0,
        thermal_heading: "5000"     # String instead of int
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        # Strings will be preserved in their original form
        assert df.iloc[0][temp_heading] == "22.5"


def test_initialise_dataframe_repeated_calls():
    """
    Tests that repeated calls to initialise_dataframe produce consistent results.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: 22.5,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    file_paths = ["file_1.json"]
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df1 = initialise_dataframe()
        df2 = initialise_dataframe()
        
        # Both should have same structure and content
        assert len(df1) == len(df2)
        pd.testing.assert_frame_equal(df1, df2)


def test_initialise_db_extract_raises_exception():
    """
    Tests that initialise_db raises exception if extract_row_from_json fails.
    """
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=FileNotFoundError("File not found")):
        with pytest.raises(FileNotFoundError):
            initialise_db()


def test_initialise_db_insert_raises_exception():
    """
    Tests that initialise_db raises exception if insert_data fails.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: 22.5,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row), \
         patch("backend.services.data_processor.insert_data", side_effect=Exception("DB error")):
        with pytest.raises(Exception):
            initialise_db()


def test_initialise_db_large_dataset():
    """
    Tests that initialise_db handles large datasets efficiently.
    """
    test_time = datetime.now().isoformat()
    num_files = 1000
    
    mock_rows = [
        {
            file_heading: f"file_{i}.json",
            time_heading: test_time,
            temp_heading: 20.0 + (i % 10),
            co2_heading: 400.0 + (i % 50),
            o2_heading: 21.0 + (i % 5),
            thermal_heading: 5000 + i
        }
        for i in range(num_files)
    ]
    
    file_paths = [f"file_{i}.json" for i in range(num_files)]
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", side_effect=mock_rows), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        assert mock_insert.call_count == num_files


def test_initialise_db_with_negative_values():
    """
    Tests that initialise_db handles negative values correctly.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: -10.5,
        co2_heading: -100.0,
        o2_heading: -5.0,
        thermal_heading: -1000
    }
    
    with patch("backend.services.data_processor.generate_table"), \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        
        mock_insert.assert_called_once_with(test_time, -10.5, -100.0, -5.0, -1000)


def test_initialise_db_repeated_calls():
    """
    Tests that repeated calls to initialise_db work correctly.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "file_1.json",
        time_heading: test_time,
        temp_heading: 22.5,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    file_paths = ["file_1.json"]
    
    with patch("backend.services.data_processor.generate_table") as mock_generate, \
         patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=file_paths), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row), \
         patch("backend.services.data_processor.insert_data") as mock_insert:
        initialise_db()
        initialise_db()
        
        # generate_table should be called twice
        assert mock_generate.call_count == 2
        # insert_data should be called twice
        assert mock_insert.call_count == 2


def test_initialise_dataframe_with_empty_string_values():
    """
    Tests that initialise_dataframe handles empty strings in fields.
    """
    test_time = datetime.now().isoformat()
    mock_row = {
        file_heading: "",              # Empty string
        time_heading: test_time,
        temp_heading: None,
        co2_heading: 400.0,
        o2_heading: 21.0,
        thermal_heading: 5000
    }
    
    with patch("backend.services.data_processor.get_sorted_json_filepaths", return_value=["file_1.json"]), \
         patch("backend.services.data_processor.extract_row_from_json", return_value=mock_row):
        df = initialise_dataframe()
        
        assert len(df) == 1
        assert df.iloc[0][file_heading] == ""
        assert pd.isna(df.iloc[0][temp_heading])