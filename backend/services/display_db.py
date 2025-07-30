from flask import Flask, render_template_string
import sqlite3
import os
import matplotlib.pyplot as plt
from datetime import datetime
from backend.services.config_loader import load_config
from backend.services.database import conn, cur

config = load_config()

app = Flask(__name__)

HTML = """
<!doctype html>
<title>Simulation Data</title>
<h1>Experimental Data</h1>
<table border=1>
  <tr><th>ID</th><th>Time</th><th>Temperature</th><th>CO2</th><th>O2</th><th>Thermal</th></tr>
  {% for row in data %}
  <tr>
    <td>{{ row[0] }}</td>
    <td>{{ row[1] }}</td>
    <td>{{ row[2] }}</td>
    <td>{{ row[3] }}</td>
    <td>{{ row[4] }}</td>
    <td>{{ row[5] }}</td>
  </tr>
  {% endfor %}
</table>
"""

@app.route("/")
def index():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', config['database_name'])
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM experimental_data")
    data = cur.fetchall()
    conn.close()
    return render_template_string(HTML, data=data)

def start_server():
    app.run(debug=False)


def plot_data_from_db():
    """
    Fetches data from the experimental_data table and plots it.
    """
    # Fetch data
    cur.execute("SELECT id, temperature, co2, o2, thermal FROM experimental_data")
    rows = cur.fetchall()

    # Unpack columns
    id_list = [row[0] for row in rows]
    temp_list = [row[1] for row in rows]
    co2_list = [row[2] for row in rows]
    o2_list = [row[3] for row in rows]
    thermal_list = [row[4] for row in rows]

    # Plotting
    fig, ax = plt.subplots(2, 2, figsize=(14, 8))

    ax[0, 0].plot(id_list, temp_list, 'r-', label='Temperature (degC)')
    ax[0, 0].set_title("Temperature")
    ax[0, 0].set_ylabel("degC")
    ax[0, 0].legend()

    ax[0, 1].plot(id_list, co2_list, 'g-', label='CO2 (ppm)')
    ax[0, 1].set_title("CO2 Concentration")
    ax[0, 1].set_ylabel("ppm")
    ax[0, 1].set_ylim(0, max(co2_list) * 1.2)
    ax[0, 1].legend()

    ax[1, 0].plot(id_list, o2_list, 'b-', label='O2 (ppm)')
    ax[1, 0].set_title("O2 Concentration")
    ax[1, 0].set_ylabel("ppm")
    ax[1, 0].set_ylim(0, max(o2_list) * 1.2)
    ax[1, 0].legend()
    

    ax[1, 1].plot(id_list, thermal_list, 'b-', label='Thermal energy')
    ax[1, 1].set_title("Thermal energy emitted")
    ax[1, 1].set_ylabel("Joules")
    ax[1, 1].legend()

    for a in ax.flatten():
        a.set_xlabel("Time since start (minutes)")
        a.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.show()