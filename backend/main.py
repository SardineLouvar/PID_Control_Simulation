import runpy
import os
import shutil
from simulation.process_model import process_for_dataframe, process_for_sql
from services.data_processor import initialise_db, initialise_dataframe
from services.database import delete_db
from services.display_db import start_server, plot_data_from_db
from services.config_loader import load_config

config = load_config()

database_type = config["database_type"]

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, config['data_path'])
db_path = os.path.join(script_dir, config['database_name'])


def delete_pycache_dirs():
    """
    Task: Remove all pycache directories for cleaner look after running code.
    """
    for dirpath, dirnames, filenames in os.walk("."):
        for dirname in dirnames:
            if dirname == "__pycache__":
                full_path = os.path.join(dirpath, dirname)
                shutil.rmtree(full_path)
            

def delete_data():
    """
    Task: Delete all data that has been generated
    """
    for filename in os.listdir(data_path):
        os.remove(os.path.join(data_path, filename))


if __name__ == "__main__":
    """
    Tasks: - Run the simulation to either produce data for a dataframe or SQL table.
           - Clean the project.
    """

    os.system('cls')

    # Create a dataframe from all of the experimental data
    if database_type == "dataframe":
        process_for_dataframe()
        data = initialise_dataframe()
        print(data)
    else:
        # Create an SQL table of the data by default
        process_for_sql()
        initialise_db()
        start_server()

    plot_data_from_db()

    # Clean the project
    delete_data()
    delete_pycache_dirs()
    delete_db()