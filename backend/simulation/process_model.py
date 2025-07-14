import os
import matplotlib.pyplot as plt
from simulation.model import simulate_airsealed_room_no_control, simulate_airsealed_room_with_control, hours_run, start_time, init_temp_C, init_room_CO2, init_room_O2
from simulation.generate_json import write_json
from services.config_loader import load_config
from simulation.HVAC import PID, use_hvac

config = load_config()
db_type = config["database_type"]

data = []
time_list = []
temp_list = []
co2_list = []
o2_list = []
thermal_list = []


def plot_data(time_list,temp_list,co2_list,o2_list,thermal_list):
    """
    Task: Plot graphs to check the simulation
    """
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))

    process_for_dataframe()

    # Temperature subplot
    ax[0].plot(time_list, temp_list, 'r:', label='Room Temp')
    ax[0].set_xlabel("Time")
    ax[0].set_ylabel("Temperature (°C)")
    ax[0].tick_params(axis='x', rotation=45)
    ax[0].legend()

    # CO2 and O2 subplot
    ax[1].plot(time_list, co2_list, 'r:', label='CO₂')
    ax[1].plot(time_list, o2_list, 'b:', label='O₂')
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Concentration (ppm)")
    ax[1].tick_params(axis='x', rotation=45)
    ax[1].legend()

    plt.tight_layout()
    plt.show()


def process_for_dataframe():
    for i in range(hours_run*60):
        if not time_list:
            data = simulate_airsealed_room_no_control([start_time, init_temp_C, init_room_CO2, init_room_O2, 10000])
        else:
            data = simulate_airsealed_room_no_control(data)

        time, temp, co2, o2, thermal = data

        data_dict = {
            "time" : time.isoformat(),
            "temperature" : temp,
            "co2" : co2,
            "o2" : o2,
            "thermal" : thermal
        }
       
        write_json(data_dict, i+1)

        time_list.append(time)
        temp_list.append(temp)
        co2_list.append(co2)
        o2_list.append(o2)
        thermal_list.append(thermal)

    plot_data(time_list,temp_list,co2_list,o2_list,thermal_list)


def process_for_sql():
    pid_constants = config["pid_constants"]
    _t1,_t2,_t3 = pid_constants["temp_k"]
    _c1,_c2,_c3 = pid_constants["co2_k"]
    _o1,_o2,_o3 = pid_constants["o2_k"]

    pid_temp = PID(_t1,_t2,_t3,25)
    pid_co2 = PID(_c1,_c2,_c3,400)
    pid_o2 = PID (_o1,_o2,_o3,210000)

    hvac_data = None

    for i in range(hours_run*60):
        if not time_list:
            data = simulate_airsealed_room_no_control([start_time, init_temp_C, init_room_CO2, init_room_O2, 10000])
            hvac_data,pid_temp,pid_co2,pid_o2 = use_hvac(data,pid_temp,pid_co2,pid_o2)
        else:
            hvac_data,pid_temp,pid_co2,pid_o2 = use_hvac(data,pid_temp,pid_co2,pid_o2)
            data = simulate_airsealed_room_with_control(data,hvac_data)

        time, temp, co2, o2, thermal = data

        data_dict = {
            "time" : time.isoformat(),
            "temperature" : temp,
            "co2" : co2,
            "o2" : o2,
            "thermal" : thermal
        }
       
        write_json(data_dict, i+1)
