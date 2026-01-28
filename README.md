# Simulation of an Airtight room with a HVAC system

This project simulates a controlled room environment, generating time-series data that is exposed via JSON APIs for seamless integration with an external system (`backend/services`). The data is stored in either dataframe or SQL form (determined using the `config.yaml` file) the data is plotted. Finally, a cleanup routine ensures the project stays organized by removing all generated files.

Python version: 3.10 or newer (tested with 3.13.5)

## How to run (Windows)
1. Download the entire project and extract it where you want to run it.
2. In `config.yaml` change the database_type to either "dataframe" to produce the uncontrolled simulation, or "sql" for the HVAC-controlled simulation. It is set to sql by default.
3. Open a terminal and ensure that the current working directory is the extracted project folder. For example, open the folder in an IDE like Visual Studio Code, or run `cd path\to\folder`.
4. Make a virtual environment and install dependencies by running:
`python -m venv venv && venv\scripts\activate && pip install -r requirements.txt`
5. Run the `main.py` file using `python -m backend.main` from the root folder.


## How to run (Mac / Linux)
1. Download the entire project and extract it where you want to run it.
2. In `config.yaml` change the database_type to either "dataframe" to produce the uncontrolled simulation, or "sql" for the HVAC-controlled simulation. It is set to sql by default.
3. Open a terminal and ensure that the current working directory is the extracted project folder. For example, open the folder in an IDE like Visual Studio Code, or run `cd path/to/folder`.
4. Make a virtual environment and install dependencies by running:
`python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
5. Run the `main.py` file using `python3 -m backend.main` from the root folder.


## Simulation
The following project contains a simulation of an airtight, isolated room filled with industrial equipment and workers. The workers produce carbon dioxide and consume oxygen, and the industrial equipment raise or lower the overall temperature of the room. The model is simplified and somewhat unrealistic, however I wanted a mixture of changes to the environment of the room to test the control with. A HVAC system is used to control the temperature, CO2 concentration and O2 concentration of the room using a proportional-integral-derivative (PID) control scheme.

### Model assumptions
- All thermal energy goes into the air (no absorption by walls, equipment, people etc.)
- Completely uniform temperature and composition of air in the room.
- The composition of air in the room does not affect the volume of oxygen consumed / co2 expelled
- No temperature or concentration gradient effect that make it more difficult to increase / decrease the temp and concs at extreme conditions.

### Credits:
[1] https://pmc.ncbi.nlm.nih.gov/articles/PMC5666301/ - 0.005 L/s of CO2 emitted by breathing
[2] https://en.wikipedia.org/wiki/Atmosphere_of_Earth - Approx 21% Oxygen in atmosphere
[3] https://pmc.ncbi.nlm.nih.gov/articles/PMC8672270/ - Breathe 6L air per min (resting), use approx 5% oxygen
[4] https://www.osha.gov/laws-regs/standardinterpretations/2007-04-02-0 - OSHA requires 19.5% oxygen minimum (195,000 ppm) and 23.5% max (235,000)
[5] https://www.osha.gov/chemicaldata/183 - OSHA requires a maximum of 5000 ppm of CO2 for an 8 hour shift


## Folder structure and purposes
```
backend/
│
├── main.py
│   - Entry point for the program.
│
├── config.yaml
│   - A config file where properties of the simulation can be easily changed (like starting conditions).
│
├── api/
│   └── read_json.py
│       - Handles reading the JSON simulation data from backend/dummy_data
│
├── services/
│   ├── config_loader.py
│       - Loads the config settings from config.yaml.
│   ├── data_processor.py
│       - Contains functions for inserting the dummy data into a database (dataframe or SQL)
│   ├── database.py
│       - Handles SQLite database creation, insertion and deletion.
│   ├── display_db.py
│       - Provides functionality for making a Flask web server to display the SQL table "experimental_data" or plot it.
│   ├── simulation.db
│       - This is the SQL database which is generated during runtime and deleted before ending the main script.
│
├── simulation/
│   ├── generate_json.py
│       - Generates simulation data in JSON format.
│   ├── HVAC.py
│       - Contains PID control and HVAC simulation logic.
│   ├── model.py
│       - Contains the model that data is generated from.
│   ├── process_model.py
│       - Contains functions for actually running the simulation.
│   └── dummy_data/
│       - Contains generated JSON files for the current simulation, which are deleted before ending the main script.
```

## Running Unit Tests
To run every unit test for the code, use the command `pytest`. Ensure that you have created the environment and downloaded the required dependencies before doing this.

## Notes

- Cursor was used to generate the file structure diagram, but the descriptions were added myself.


