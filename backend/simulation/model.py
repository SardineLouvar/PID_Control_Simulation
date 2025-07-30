import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import random
from backend.services.config_loader import load_config

"""
A simulation of an airtight sterile room, where a HVAC system must manage the environment conditions.

To do:
- Simulate room increasing uniformly in temp
- Simulate CO2 increase from breathing
- Simulate O2 decrease from breathing
- Add random noise so model isnt completely uniform, add a sin wave to simulate breathing speed variety?
- Make breathing consumption/emission dependent on temperature (higher temp = more)
"""

config = load_config()
sim_config = config['simulation']

# Constants
air_density = 1.225  # kg/m³
air_cp = 1005  # J/kg°C
co2_gen_per_person = 0.005*60 #[1] L/min
o2_cons_per_person = 6*0.05
start_time = datetime.now()

# Load simulation parameters from config
hours_run = sim_config['hours_run']
init_temp_C = sim_config['init_temp_C']
init_room_CO2 = sim_config['init_room_CO2']
init_room_O2 = sim_config['init_room_O2']
room_volume = sim_config['room_volume']
occupants = sim_config['occupants']

room_air_mass = room_volume * air_density

#convert gases to ppm from L/min
co2_gen_per_person = (co2_gen_per_person/1000)/room_volume * 10**6
o2_cons_per_person = (o2_cons_per_person/1000)/room_volume * 10**6



def simulate_process_equipment(thermal):
    mod = random.random()

    #Add random step
    if mod < 0.01:
        thermal += random.randint(-50000,50000)
    
    thermal += random.randint(-5000,5000)
        
    return thermal



def simulate_breathing_changes(co2,o2,temp):
    def mod_breathing(g,min,max,diff):
        if g >= min or g <= max:
            g += random.randrange(-diff,diff)/1000
        
        g = g * abs(temp/25)
        #g = g * 2**(abs(temp - 25) / 15)

        return g
    

    #CO2 increases in the room (ppm)
    co2 = co2 + mod_breathing(co2_gen_per_person,co2_gen_per_person/10,co2_gen_per_person*10,int(co2_gen_per_person*100))*occupants

    #O2 decreases in room (ppm)
    o2 = o2 - mod_breathing(o2_cons_per_person,o2_cons_per_person/10,o2_cons_per_person*10,int(o2_cons_per_person*100))*occupants

    co2 = max(min(1000000,co2),0)
    o2 = max(min(1000000,o2),0)

    return [co2,o2]



def simulate_airsealed_room_no_control(data):
    """
    Inputs: 
    - data = Array of the values below, in order:
    - temp = Temperature of the room,
    - co2 = The CO2 in the room,
    - o2 = The O2 in the room,
    - thermal = Thermal energy output by process equipment.

    Task: Model the inputs after 1 minute using mass and energy balances.
    """
    time, temp, co2, o2, thermal = data

    #increment time
    time += timedelta(minutes=1)

    #Temperature increases in the room (simplified, degC)
    thermal = simulate_process_equipment(thermal)
    temp = temp + (thermal/(room_air_mass*air_cp))

    #Prevent temp going below min
    temp = max(temp, -273)

    #Simulate co2 and o2 changes from breathing in the room
    co2, o2 = simulate_breathing_changes(co2,o2,temp)

    return [time,temp,co2,o2,thermal]



def simulate_airsealed_room_with_control(data, hvac_data):
    """
    Inputs: 
    - data = Array of the values below, in order:
    - temp = Temperature of the room,
    - co2 = The CO2 in the room,
    - o2 = The O2 in the room,
    - thermal = Thermal energy output by process equipment.

    Task: Model the inputs after 1 minute using mass and energy balances.
    """
    time, temp, co2, o2, thermal = data
    hvac_temp, hvac_co2, hvac_o2 = hvac_data

    #increment time
    time += timedelta(minutes=1)

    #Temperature increases in the room (simplified, degC)
    thermal = simulate_process_equipment(thermal)
    temp = temp + (thermal/(room_air_mass*air_cp) + hvac_temp)

    #Prevent temp going below min
    if temp < -273:
        temp = -273

    #Simulate co2 and o2 changes from breathing in the room
    co2, o2 = simulate_breathing_changes(co2,o2,temp)
    co2 += hvac_co2
    o2 += hvac_o2

    return [time,temp,co2,o2,thermal]











if __name__ == '__main__':
    """
    Task: - Simulate the process of an airtight sterile room, where a HVAC system must manage the environment conditions.
          - Plot the results of the simulation.
    Inputs:
    - data = Array of the values below, in order:
    - temp = Temperature of the room,
    - co2 = The CO2 in the room,
    - o2 = The O2 in the room,
    - thermal = Thermal energy output by process equipment.
    """
    os.system('cls')
    data = []
    time_list = []
    temp_list = []
    co2_list = []
    o2_list = []
    thermal_list = []


    for i in range(hours_run*60):
        if not time_list:
            data = simulate_airsealed_room_no_control([start_time, init_temp_C, init_room_CO2, init_room_O2, 10000])
        else:
            data = simulate_airsealed_room_no_control(data)

        ntime, ntemp, nco2, no2, nthermal = data

        time_list.append(ntime)
        temp_list.append(ntemp)
        co2_list.append(nco2)
        o2_list.append(no2)
        thermal_list.append(nthermal)


    # Plotting
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))  # Optional: increase figure size

    # Temperature subplot
    ax[0].plot(time_list, temp_list, label='Room Temp')
    ax[0].set_xlabel("Time")
    ax[0].set_ylabel("Temperature (°C)")
    ax[0].tick_params(axis='x', rotation=45)
    ax[0].legend()

    # CO2 and O2 subplot
    ax[1].plot(time_list, co2_list, 'r.', label='CO₂')
    ax[1].plot(time_list, o2_list, 'b.', label='O₂')
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Concentration (ppm)")
    ax[1].tick_params(axis='x', rotation=45)
    ax[1].legend()

    plt.tight_layout()
    plt.show()

