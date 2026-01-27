import json
from unittest.mock import patch, mock_open

from backend.simulation.generate_json import write_json


class TestWriteJson:
    """Tests for the write_json function."""

    def test_write_json_creates_file(self):
        """Tests that write_json creates a JSON file."""
        test_data = {"temperature": 21.5, "co2": 401}
        filename = "test_data"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            # Verify open was called
            m.assert_called_once()

    def test_write_json_correct_content(self):
        """Tests that write_json writes correct JSON content."""
        test_data = {"temperature": 21.5, "co2": 401, "o2": 21.0}
        filename = "test_content"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            # Get the write calls
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_nested_dict(self):
        """Tests that write_json handles nested dictionaries."""
        test_data = {
            "room": {"temperature": 21.5, "humidity": 45},
            "hvac": {"status": "on", "mode": "heating"}
        }
        filename = "nested_data"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_list(self):
        """Tests that write_json handles lists."""
        test_data = {
            "timestamps": [1, 2, 3, 4, 5],
            "values": [21.0, 21.5, 22.0, 21.8, 21.3]
        }
        filename = "list_data"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_special_characters(self):
        """Tests that write_json handles special characters."""
        test_data = {
            "description": "Test with special chars: éàü",
            "symbols": "!@#$%^&*()",
            "quotes": 'He said "hello"'
        }
        filename = "special_chars"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_empty_dict(self):
        """Tests that write_json handles empty dictionaries."""
        test_data = {}
        filename = "empty_dict"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == {}

    def test_write_json_with_empty_list(self):
        """Tests that write_json handles empty lists."""
        test_data = {"data": []}
        filename = "empty_list"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_null_values(self):
        """Tests that write_json handles null values."""
        test_data = {"value": None, "optional": None}
        filename = "null_values"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_boolean_values(self):
        """Tests that write_json handles boolean values."""
        test_data = {"active": True, "enabled": False}
        filename = "bool_values"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_numeric_types(self):
        """Tests that write_json handles various numeric types."""
        test_data = {
            "integer": 42,
            "float": 3.14159,
            "negative": -100,
            "zero": 0
        }
        filename = "numeric_types"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_with_long_string(self):
        """Tests that write_json handles long strings."""
        test_data = {"long_text": "a" * 10000}
        filename = "long_string"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert len(loaded_data["long_text"]) == 10000

    def test_write_json_with_deeply_nested_structure(self):
        """Tests that write_json handles deeply nested structures."""
        test_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {"value": 42}
                    }
                }
            }
        }
        filename = "deep_nesting"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_filename_format(self):
        """Tests that write_json uses correct filename format."""
        test_data = {"key": "value"}
        filename = "my_data"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            # Check that open was called with correct filename
            call_args = m.call_args
            assert f"{filename}.json" in call_args[0][0]

    def test_write_json_config_access(self):
        """Tests that write_json accesses config correctly."""
        test_data = {"key": "value"}
        filename = "config_test"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "custom_data"
            
            write_json(test_data, filename)
            
            # Verify config was accessed with 'data_path'
            mock_config.__getitem__.assert_called_with('data_path')

    def test_write_json_makedirs_called(self):
        """Tests that write_json calls os.makedirs."""
        test_data = {"key": "value"}
        filename = "dir_test"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs") as mock_makedirs:
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            # Verify makedirs was called
            mock_makedirs.assert_called_once()
            assert mock_makedirs.call_args[1].get('exist_ok') == True

    def test_write_json_indentation_used(self):
        """Tests that write_json uses indent=2."""
        test_data = {"a": 1, "b": 2}
        filename = "indent_test"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            # Check that json.dump was called with indent=2
            # The written content should have indentation
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            assert "  " in written  # indent=2 produces 2-space indentation

    def test_write_json_with_mixed_types(self):
        """Tests that write_json handles mixed data types."""
        test_data = {
            "string": "value",
            "integer": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        filename = "mixed_types"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            loaded_data = json.loads(written)
            assert loaded_data == test_data

    def test_write_json_file_mode(self):
        """Tests that write_json opens file in write mode."""
        test_data = {"key": "value"}
        filename = "mode_test"
        
        m = mock_open()
        with patch("backend.simulation.generate_json.config") as mock_config, \
             patch("backend.simulation.generate_json.open", m), \
             patch("backend.simulation.generate_json.os.makedirs"):
            mock_config.__getitem__.return_value = "dummy_data"
            
            write_json(test_data, filename)
            
            # Verify file was opened in write mode
            call_args = m.call_args
            assert call_args[0][1] == "w"
