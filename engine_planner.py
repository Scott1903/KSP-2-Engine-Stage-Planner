import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import easygui
import sys

# Engine data to numpy
try:
    engine_df = pd.read_csv('engines.csv')
except:
    easygui.msgbox("engines.csv file read error.\n\nPlease ensure the engines.csv file is located in the same directory as the .exe.", "engines.csv error", "OK")
    sys.exit()
try:
    engine_df = engine_df.drop(engine_df[engine_df['Fuel'] == 'Methane'].index)
except:
    pass
n_engines = len(engine_df['Engine'])
try:
    engines = engine_df[['Name', 'Radial', 'Fuel', 'Mass', 'Thrust (atm)', 'Thrust (vac)', 'ISP (atm)', 'ISP (vac)']].to_numpy()
except:
    easygui.msgbox("engines.csv missing columns.\n\nMust have the following at a minimum:\n\nName, Radial, Fuel, Mass, Thrust (atm), Thrust (vac), ISP (atm), ISP (vac)", "engines.csv error", "OK")
    sys.exit()
max_n_engines = 16
logo = "icon.ico"



# Calculate final mass of payload+engine+fuel+tank
def get_total_mass(engine_mass, payload, dV, isp):
    num = 8*(engine_mass + payload)*math.e**(dV/9.80665/isp)
    den = math.e**(dV/9.80665/isp) - 9
    return -num/den

# Calculate TWR (Kerbin)
def get_twr(engine_mass, thrust):
    return thrust/engine_mass/9.80665

# Positive number input box
def positive_number_input(text):
    while True:
        payload = easygui.enterbox(text)
        try:
            payload = float(payload)
        except:
            if payload is None:
                return None
            easygui.msgbox("Must be a number.", "Number Error", "OK")
            continue
        if payload <= 0:
            easygui.msgbox("Must be greater than zero.", "Positive Number Error", "OK")
            continue
        return payload

# Main stage planner steps
def begin_stage_planning(engines, max_n_engines, stage_type):
    n_engines = len(engines)

    # Get stage details
    payload = positive_number_input("Payload for this stage (t):\n\nValues might be between 0.1 and 200.")
    if payload is None:
        return
    twr = positive_number_input("Minimum Thrust-to-Weight Ratio (TWR on Kerbin gravity):\n\nValues might be between 0.1 and 4.")
    if twr is None:
        return
    dV = positive_number_input("Approximate dV requirement (m/s):\n\nValues might be between 100 and 10000.")
    if dV is None:
        return
    if stage_type == "Atmosphere Stage":
        thrust = 4
        isp = 6
    else:
        thrust = 5
        isp = 7

    # Initialize dV range
    dVs = np.arange(0, 7100, 10)
    n_dVs = len(dVs)
    masses = np.zeros((n_engines, n_dVs))
    ns = np.zeros((n_engines, n_dVs))

    # Plot across all dVs
    plt.figure(figsize=(22,9))
    plt.subplot(1, 2, 1)
    plt.title('Final Mass for n Engines of Each Type\nPayload: ' + str(payload) + "t, TWR: " + str(twr))
    plt.xlabel("dV")
    plt.ylabel("Final Stage Mass (t)")
    for e, engine in enumerate(engines):
        if engine[1]:
            n = 2
        else:
            n = 1
        for i, dv in enumerate(dVs):
            if n > max_n_engines:
                masses[e][i] = math.inf
                ns[e][i] = 0
                continue
            masses[e][i] = get_total_mass(n*engine[3], payload, dv, engine[isp])
            while n*engine[thrust]/masses[e][i]/9.807 < twr:
                n += 1
                if n > max_n_engines or masses[e][i] < 0:
                    masses[e][i] = math.inf
                    if i > 0:
                        plt.text(dv, masses[e][i-1], engine[0])
                    break
                masses[e][i] = get_total_mass(n*engine[3], payload, dv, engine[isp])
            ns[e][i] = n
            if i == len(dVs) - 1:
                plt.text(dv, masses[e][i-1], engine[0])
        plt.plot(dVs, masses[e], label = engine[0], linewidth = 2)
    plt.yscale("log")

    # Initialize dV range for detailed view
    dVs = np.arange(round(dV*.85, 0), dV+round(dV*.15, 0), 1)
    n_dVs = len(dVs)
    masses = np.zeros((n_engines, n_dVs))
    ns = np.zeros((n_engines, n_dVs))

    # Plot detailed view
    plt.subplot(1, 2, 2)
    plt.title('Detailed View')
    plt.xlabel("dV")
    plt.ylabel("Final Stage Mass (t)")
    for e, engine in enumerate(engines):
        if engine[1]:
            n = 2
        else:
            n = 1
        for i, dv in enumerate(dVs):
            if n > max_n_engines:
                masses[e][i] = math.inf
                ns[e][i] = 0
                continue
            masses[e][i] = get_total_mass(n*engine[3], payload, dv, engine[isp])
            while n*engine[thrust]/masses[e][i]/9.807 < twr:
                n += 1
                if n > max_n_engines or masses[e][i] < 0:
                    masses[e][i] = math.inf
                    if i > 0:
                        plt.text(dv, masses[e][i-1], engine[0])
                    break
                masses[e][i] = get_total_mass(n*engine[3], payload, dv, engine[isp])
            ns[e][i] = n
            if dv == dV:
                if n > 1:
                    plt.text(dv, masses[e][i], str(n) + " " + engine[0] + "s " + str(round(masses[e][i],2)) + "t")
                else:
                    plt.text(dv, masses[e][i], str(n) + " " + engine[0] + " " + str(round(masses[e][i],2)) + "t")
        plt.plot(dVs, masses[e], label = engine[0], linewidth = 2)

    # Get y plot limits
    y_min = 99999.0
    y_max = np.full(4, 99999.0)
    for e in range(0, n_engines):
        if masses[e][0] < y_min:
            y_min = masses[e][0]
        for i, mass in enumerate(y_max):
            if masses[e][n_dVs - 1] < mass:
                for j in range(len(y_max) - 1, i, -1):
                    y_max[j] = y_max[j - 1]
                y_max[i] = masses[e][n_dVs - 1]
                break
    plt.ylim([y_min, y_max[len(y_max) - 1]])
    plt.show()

# GUI menu
input = easygui.buttonbox("Would you like to plan a new stage?\n\nYou'll need the following for the stage you're working on:\n* The mass of the payload (t)\n* The minimum TWR needed\n* The approximate dV needed (m/s)", "KSP 2 Stage Engine Planner - by /u/wrigh516", choices=["Atmosphere Stage", "Vacuum Stage", "Close"])
while input != "Close":
    begin_stage_planning(engines, max_n_engines, input)
    input = easygui.buttonbox("Would you like to plan a new stage?\n\nYou'll need the following for the stage you're working on:\n* The mass of the payload (t)\n* The minimum TWR needed\n* The approximate dV needed (m/s)", "KSP 2 Stage Engine Planner - by /u/wrigh516", choices=["Atmosphere Stage", "Vacuum Stage", "Close"])