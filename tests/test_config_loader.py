from backend.services.config_loader import load_config
import pytest
import yaml
import os
from unittest.mock import patch, mock_open


def test_load_config_returns_dict():
    """
    Tests that load_config returns a dictionary.
    """
    config = load_config()
    assert isinstance(config, dict)


def test_load_config_contains_required_keys():
    """
    Tests that config contains expected keys.
    """
    config = load_config()
    assert "database_type" in config
    assert "simulation" in config
    assert "pid_constants" in config
    assert "data_path" in config
    assert "database_name" in config


def test_load_config_database_type_is_string():
    """
    Tests that database_type is a string with valid values.
    """
    config = load_config()
    assert isinstance(config["database_type"], str)
    assert config["database_type"] in ["dataframe", "sql"]


def test_load_config_simulation_structure():
    """
    Tests that simulation section has expected structure.
    """
    config = load_config()
    simulation = config["simulation"]
    assert isinstance(simulation, dict)
    assert "hours_run" in simulation
    assert "init_temp_C" in simulation
    assert "init_room_CO2" in simulation
    assert "init_room_O2" in simulation
    assert "room_volume" in simulation
    assert "occupants" in simulation


def test_load_config_pid_constants_structure():
    """
    Tests that pid_constants section has expected structure.
    """
    config = load_config()
    pid = config["pid_constants"]
    assert isinstance(pid, dict)
    assert "temp_k" in pid
    assert "co2_k" in pid
    assert "o2_k" in pid
    
    # Each PID constant should be a list of 3 values
    assert isinstance(pid["temp_k"], list)
    assert len(pid["temp_k"]) == 3
    assert isinstance(pid["co2_k"], list)
    assert len(pid["co2_k"]) == 3
    assert isinstance(pid["o2_k"], list)
    assert len(pid["o2_k"]) == 3


def test_load_config_paths_are_strings():
    """
    Tests that data_path and database_name are strings.
    """
    config = load_config()
    assert isinstance(config["data_path"], str)
    assert isinstance(config["database_name"], str)


def test_load_config_missing_file():
    """
    Tests that FileNotFoundError is raised when config file doesn't exist.
    """
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_config()


def test_load_config_malformed_yaml():
    """
    Tests that yaml parsing error is raised for malformed YAML.
    """
    malformed_yaml = """
    database_type: sql
    simulation:
      hours_run: 6
      invalid: [unclosed list
    """
    
    with patch("builtins.open", mock_open(read_data=malformed_yaml)):
        with pytest.raises(yaml.YAMLError):
            load_config()


def test_load_config_empty_file():
    """
    Tests that empty YAML file returns None.
    """
    empty_yaml = ""
    
    with patch("builtins.open", mock_open(read_data=empty_yaml)):
        config = load_config()
        assert config is None


def test_load_config_numeric_values():
    """
    Tests that numeric configuration values are correctly parsed.
    """
    config = load_config()
    
    # Check simulation numeric values
    assert isinstance(config["simulation"]["hours_run"], int)
    assert config["simulation"]["hours_run"] > 0
    
    assert isinstance(config["simulation"]["init_temp_C"], float)
    assert config["simulation"]["init_room_CO2"] > 0
    assert config["simulation"]["room_volume"] > 0
    assert config["simulation"]["occupants"] > 0


def test_load_config_pid_constants_are_numeric():
    """
    Tests that PID constant values are numeric.
    """
    config = load_config()
    pid = config["pid_constants"]
    
    for k, v in pid.items():
        for val in v:
            assert isinstance(val, (int, float))


def test_load_config_with_comments():
    """
    Tests that YAML comments are properly ignored.
    """
    yaml_with_comments = """
    # This is a comment
    database_type: sql  # inline comment
    
    # Another comment
    simulation:
      hours_run: 6
    """
    
    with patch("builtins.open", mock_open(read_data=yaml_with_comments)):
        config = load_config()
        assert config["database_type"] == "sql"
        assert config["simulation"]["hours_run"] == 6


def test_load_config_with_special_characters():
    """
    Tests that paths with special characters are handled.
    """
    yaml_content = """
    database_type: sql
    data_path: simulation/dummy_data
    database_name: services/simulation.db
    simulation:
      hours_run: 6
    pid_constants:
      temp_k: [1, 1, 1]
    """
    
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        config = load_config()
        assert "/" in config["data_path"]
        assert "/" in config["database_name"]


def test_load_config_idempotent():
    """
    Tests that calling load_config multiple times returns consistent results.
    """
    config1 = load_config()
    config2 = load_config()
    
    assert config1 == config2


def test_load_config_with_nested_structures():
    """
    Tests that deeply nested YAML structures are properly parsed.
    """
    yaml_nested = """
    database_type: sql
    simulation:
      hours_run: 6
      init_temp_C: 25.0
      settings:
        advanced:
          parameter: value
    pid_constants:
      temp_k: [1, 2, 3]
    """
    
    with patch("builtins.open", mock_open(read_data=yaml_nested)):
        config = load_config()
        assert config["simulation"]["settings"]["advanced"]["parameter"] == "value"

