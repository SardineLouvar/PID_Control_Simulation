import pandas as pd
from api.read_json import get_sorted_json_filepaths, extract_row_from_json, file_heading, time_heading, temp_heading, co2_heading, o2_heading, thermal_heading
from services.database import generate_table, insert_data

def initialise_dataframe():
    """
    task: generate a data frame of all JSON files in dummy_data.
    input: all JSON files located in the "dummy_data" directory.
    output: data frame containing all the data, ordered numerically by file name.
    """
    # make dataframe and set data types
    data = pd.DataFrame({
        file_heading: pd.Series(dtype="str"),
        time_heading: pd.Series(dtype="float"),
        temp_heading: pd.Series(dtype="float"),
        co2_heading: pd.Series(dtype="float"),
        o2_heading: pd.Series(dtype="float"),
        thermal_heading: pd.Series(dtype="int")
    })

    filepaths = get_sorted_json_filepaths()
    for file_path in filepaths:
        row = extract_row_from_json(file_path)
        row_df = pd.DataFrame([row])
        data = pd.concat([data, row_df], ignore_index=True)

    return data


def initialise_db():
    """
    task: generate an SQLite database using all JSON files in dummy_data.
    input: all JSON files located in the "dummy_data" directory.
    output: SQLite database containing all the data, ordered by id (determined through file name).
    """
    generate_table()
    filepaths = get_sorted_json_filepaths()
    for file_path in filepaths:
        row = extract_row_from_json(file_path)
        insert_data(
            row[time_heading],
            row[temp_heading],
            row[co2_heading],
            row[o2_heading],
            row[thermal_heading]
        )