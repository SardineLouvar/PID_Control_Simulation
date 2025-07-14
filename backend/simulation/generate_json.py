import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'services'))
from services.config_loader import load_config

config = load_config()

def write_json(data, filename):
    # Use config for dummy_data folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_data_dir = os.path.join(script_dir, '..', config['data_path'])
    os.makedirs(dummy_data_dir, exist_ok=True)
    file_path = os.path.join(dummy_data_dir, f"{filename}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
        