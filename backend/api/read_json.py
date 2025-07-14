import json
import os
import pandas as pd
import re
from services.config_loader import load_config

config = load_config()

data_dir = None

file_heading = "file"
time_heading = "time"
temp_heading = "temperature"
co2_heading = "co2"
o2_heading = "o2"
thermal_heading = "thermal energy output"


def get_sorted_json_filepaths():
    """
    Returns a numerically sorted list of JSON file paths in the dummy_data directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "..", config['data_path'])
    filenames = sorted(
        os.listdir(data_dir),
        key=lambda x: int(re.search(r'\d+', x).group())
    )
    return [os.path.join(data_dir, filename) for filename in filenames]


def extract_row_from_json(file_path):
    """
    Loads a JSON file and returns a dictionary mapping the required headings.
    """
    with open(file_path, 'r') as file:
        file_data = json.load(file)
        filename = os.path.basename(file_path)
        file_data['file'] = filename
        return {
            file_heading: filename,
            time_heading: file_data.get("time"),
            temp_heading: file_data.get("temperature"),
            co2_heading: file_data.get("co2"),
            o2_heading: file_data.get("o2"),
            thermal_heading: file_data.get("thermal")
        }

