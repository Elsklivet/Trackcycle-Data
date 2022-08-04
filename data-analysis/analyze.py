# Gavin Heinrichs-Majetich
# gmh33@pitt.edu
# https://github.com/Elsklivet

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import argparse
from sys import argv
from scipy import signal
import termcolor
import time

arg_parser = argparse.ArgumentParser(
    description="Process collected location and sensor data from TrackCycle application.",
    usage="python analyze.py -i <input file path> [-d <debug level: integer>]",
)
arg_parser.add_argument(
    "-i",
    "--input",
    type=str,
    help="input file path from which to read sensor data (note: sensor data should be in a CSV style file)",
)
arg_parser.add_argument(
    "-d",
    "--debug",
    type=int,
    help="debug level (0=no debugging (default), 1=debugging on)",
)
args = None
debug = False
data_length = None


class Log:
    def error(msg: str):
        level = termcolor.colored(f"ERROR", "red")
        print(f"[ {level} ] {msg}")

    def warning(msg: str):
        level = termcolor.colored(f"WARNING", "yellow")
        print(f"[ {level} ] {msg}")

    def ok(msg: str):
        level = termcolor.colored(f"OK", "green")
        print(f"[ {level} ] {msg}")

    def info(msg: str):
        print(f"[ INFO ] {msg}")


def parse_line(line: str, idx: int) -> dict:
    global data_length
    if line.startswith("--"):
        Log.error("Attempting to parse marker line. How did we get here?")
        return None
    data = ()
    dictionary = dict()

    try:
        data = list(map(float, line.split(",")))
        # 0   1   2   3   4     5      6      7      8     9     10    11      12    13   14   15     16      17    18
        # lat,lon,alt,acc,speed,accelx,accely,accelz,gyrox,gyroy,gyroz,azimuth,pitch,roll,time,batpct,current,capmah,engnwh
        if len(data) <= 14:
            dictionary = {
                "lat": data[0],
                "lon": data[1],
                "alt": data[2],
                "acc": data[3],
                "speed": data[4],
                "accelx": data[5],
                "accely": data[6],
                "accelz": data[7],
                "gyrox": data[8],
                "gyroy": data[9],
                "gyroz": data[10],
                "azimuth": data[11],
                "pitch": data[12],
                "roll": data[13],
            }
        elif len(data) <= 17:
            dictionary = {
                "lat": data[0],
                "lon": data[1],
                "alt": data[2],
                "acc": data[3],
                "speed": data[4],
                "accelx": data[5],
                "accely": data[6],
                "accelz": data[7],
                "gyrox": data[8],
                "gyroy": data[9],
                "gyroz": data[10],
                "azimuth": data[11],
                "pitch": data[12],
                "roll": data[13],
                "time": data[14],
                "batpct": data[15],
                "current": data[16],
            }
        elif len(data) > 18:
            dictionary = {
                "lat": data[0],
                "lon": data[1],
                "alt": data[2],
                "acc": data[3],
                "speed": data[4],
                "accelx": data[5],
                "accely": data[6],
                "accelz": data[7],
                "gyrox": data[8],
                "gyroy": data[9],
                "gyroz": data[10],
                "azimuth": data[11],
                "pitch": data[12],
                "roll": data[13],
                "time": data[14],
                "batpct": data[15],
                "current": data[16],
                "capmah": data[17],
                "engnwh": data[18],
            }
        if not data_length:
            data_length = len(data)
    except ValueError:
        Log.error(f"Could not parse line {idx}: {line}")
        return None
    except IndexError:
        if data:
            Log.error(
                f"Could not parse line {idx} due to insufficient length (len={len(data)}): {line}"
            )
        else:
            Log.error(
                f"Could not parse line {idx} due to insufficient length (data=None): {line}"
            )
        return None

    return dictionary


def main():
    global args
    global debug
    args = arg_parser.parse_args()

    if args.input == None:
        arg_parser.print_help()
        exit(1)

    path = args.input

    if not os.path.exists(path):
        Log.error(f"File {path} was inaccessible or does not exist")
        exit(2)

    if args.debug:
        if args.debug != 0 and args.debug != 1:
            Log.warning(
                f"Expected debug level 0 or 1, got {args.debug}. Defaulting to 0."
            )
        else:
            debug = args.debug == 1

    lines = []
    with open(path, "r") as infile:
        Log.info(f"Begins processing {path}.")
        lines = infile.readlines()

    markers = dict()
    marker_x = {
        "GPS_STOP": [],
        "GPS_START": [],
        "MOTION": [],
        "LEFT": [],
        "RIGHT": [],
        "STOP": [],
    }
    data = pd.DataFrame()

    start = time.time()

    for (idx, line) in enumerate(lines):
        if idx == 0:
            # lat,lon,alt,acc,speed,accelx,accely,accelz,gyrox,gyroy,gyroz,azimuth,pitch,roll
            continue

        if line.startswith("--"):
            if debug:
                Log.info(f"Line {idx} is a special marker")

            # This is a special marker line
            line = line.lstrip("--").rstrip("--\n")

            if line == "GPS STOPPED":
                markers[idx] = "GPS STOPPED"
                marker_x["GPS_STOP"].append(idx)
            if line == "GPS STARTED":
                markers[idx] = "GPS STARTED"
                marker_x["GPS_START"].append(idx)
            elif line == "SIGNIFICANT MOTION DETECTED":
                markers[idx] = "MOTION DETECTED"
                marker_x["MOTION"].append(idx)
            elif line == "LEFT":
                markers[idx] = "LEFT"
                marker_x["LEFT"].append(idx)
            elif line == "RIGHT":
                markers[idx] = "RIGHT"
                marker_x["RIGHT"].append(idx)
            elif line == "STOP":
                markers[idx] = "STOP"
                marker_x["STOP"].append(idx)
        else:
            if debug:
                Log.info(f"Line {idx} is a data line. Parsing...")

            # Normal data line, parse
            data = pd.concat(
                [data, pd.DataFrame([parse_line(line, idx)])], ignore_index=True
            )

    end = time.time()

    Log.ok(f"FINISHED PARSING IN {end-start} s")

    if debug:
        print(data)

    while True:
        # 0   1   2   3   4     5      6      7      8     9     10    11      12    13
        # lat,lon,alt,acc,speed,accelx,accely,accelz,gyrox,gyroy,gyroz,azimuth,pitch,roll
        choice = input(
            """What would you like to see a graph of?
        1 - All
        2 - Lat/Lon
        3 - Altitude
        4 - Accuracy
        5 - Speed
        6 - Accelerometer
        7 - Gyroscope
        8 - Orientation
        9 - Azimuth Only
        10 - Energy Use
        11 - Exit
    > """
        )
        try:
            choice = int(choice)
        except ValueError:
            Log.warning(f"Invalid choice selected, defaulting to 1: {choice}")
            choice = 1

        if choice == 1:
            # All
            fig, axes = plt.subplots(nrows=3, ncols=6)
            key_num = 0
            for row in range(3):
                for col in range(6):
                    if key_num >= len(data.keys()):
                        break
                    key = data.keys()[key_num]
                    key_num += 1
                    # data[key].plot(kind='line',title=f"{key}")
                    axes[row, col].plot(data[key])
                    axes[row, col].title.set_text(str(key).capitalize())
                    axes[row, col].vlines(
                        marker_x["LEFT"],
                        data[key].min(),
                        data[key].max(),
                        linestyles="dashed",
                        colors="green",
                    )
                    # axes[row,col].vlines(marker_x["GPS"], data[key].min(), data[key].max(), linestyles="dashed", colors="purple")
                    axes[row, col].vlines(
                        marker_x["RIGHT"],
                        data[key].min(),
                        data[key].max(),
                        linestyles="dashed",
                        colors="orange",
                    )
                    axes[row, col].vlines(
                        marker_x["STOP"],
                        data[key].min(),
                        data[key].max(),
                        linestyles="dashed",
                        colors="red",
                    )

        elif choice == 2:
            # Lat/Lon
            fig, axes = plt.subplots(nrows=1, ncols=2)
            key_num = 0
            for col in range(2):
                key = data.keys()[key_num]
                key_num += 1
                axes[col].plot(data[key])
                axes[col].title.set_text(str(key).capitalize())
                axes[col].vlines(
                    marker_x["LEFT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="green",
                )
                axes[col].vlines(
                    marker_x["RIGHT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="orange",
                )
                axes[col].vlines(
                    marker_x["STOP"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="red",
                )

        elif choice == 3:
            # Altitude
            fig, axes = plt.subplots(nrows=1, ncols=1)
            key = "alt"
            axes.plot(data[key])
            axes.title.set_text(key.capitalize())
            axes.vlines(
                marker_x["LEFT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="green",
            )
            axes.vlines(
                marker_x["RIGHT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="orange",
            )
            axes.vlines(
                marker_x["STOP"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="red",
            )

        elif choice == 4:
            # Accuracy
            fig, axes = plt.subplots(nrows=1, ncols=1)
            key = "acc"
            axes.plot(data[key])
            axes.title.set_text(key.capitalize())
            axes.vlines(
                marker_x["LEFT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="green",
            )
            axes.vlines(
                marker_x["RIGHT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="orange",
            )
            axes.vlines(
                marker_x["STOP"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="red",
            )

        elif choice == 5:
            # Speed
            fig, axes = plt.subplots(nrows=1, ncols=1)
            key = "speed"
            axes.plot(data[key])
            axes.title.set_text(key.capitalize())
            axes.vlines(
                marker_x["LEFT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="green",
            )
            axes.vlines(
                marker_x["RIGHT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="orange",
            )
            axes.vlines(
                marker_x["STOP"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="red",
            )

        elif choice == 6:
            # Accelerometer
            fig, axes = plt.subplots(nrows=1, ncols=3)
            key_num = 5
            for col in range(3):
                key = data.keys()[key_num]
                key_num += 1
                axes[col].plot(data[key])
                sos = signal.ellip(3, 2, 300, 0.01, output="sos", btype="lowpass")
                axes[col].plot(signal.sosfilt(sos, data[key]), "k-")
                axes[col].title.set_text(str(key).capitalize())
                axes[col].vlines(
                    marker_x["LEFT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="green",
                )
                axes[col].vlines(
                    marker_x["RIGHT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="orange",
                )
                axes[col].vlines(
                    marker_x["STOP"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="red",
                )
                axes[col].vlines(
                    marker_x["MOTION"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="purple",
                )

        elif choice == 7:
            # Gyroscope
            fig, axes = plt.subplots(nrows=1, ncols=3)
            key_num = 8
            for col in range(3):
                key = data.keys()[key_num]
                key_num += 1
                axes[col].plot(data[key])
                sos = signal.ellip(3, 2, 300, 0.01, output="sos", btype="lowpass")
                axes[col].plot(signal.sosfilt(sos, data[key]), "k-")
                axes[col].title.set_text(str(key).capitalize())
                axes[col].vlines(
                    marker_x["LEFT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="green",
                )
                axes[col].vlines(
                    marker_x["RIGHT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="orange",
                )
                axes[col].vlines(
                    marker_x["STOP"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="red",
                )
                axes[col].vlines(
                    marker_x["MOTION"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="purple",
                )

        elif choice == 8:
            # Orientation
            fig, axes = plt.subplots(nrows=1, ncols=3)
            key_num = 11
            for col in range(3):
                key = data.keys()[key_num]
                key_num += 1
                axes[col].plot(data[key])
                sos = signal.ellip(3, 2, 300, 0.01, output="sos", btype="lowpass")
                axes[col].plot(signal.sosfilt(sos, data[key]), "k-")
                axes[col].title.set_text(str(key).capitalize())
                axes[col].vlines(
                    marker_x["LEFT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="green",
                )
                axes[col].vlines(
                    marker_x["RIGHT"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="orange",
                )
                axes[col].vlines(
                    marker_x["STOP"],
                    data[key].min(),
                    data[key].max(),
                    linestyles="dashed",
                    colors="red",
                )
        elif choice == 9:
            # Speed
            fig, axes = plt.subplots(nrows=1, ncols=1)
            key = "azimuth"
            axes.plot(data[key])
            sos = signal.ellip(3, 2, 300, 0.01, output="sos", btype="lowpass")
            axes.plot(signal.sosfilt(sos, data[key]), "k-")

            axes.title.set_text(key.capitalize())
            axes.vlines(
                marker_x["LEFT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="green",
            )
            axes.vlines(
                marker_x["RIGHT"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="orange",
            )
            axes.vlines(
                marker_x["STOP"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="red",
            )
            axes.vlines(
                marker_x["MOTION"],
                data[key].min(),
                data[key].max(),
                linestyles="dashed",
                colors="purple",
            )
        elif choice == 10:
            # Energy
            fig, axes = plt.subplots(nrows=2, ncols=2)
            key_num = 15
            for row in range(2):
                for col in range(2):
                    if key_num >= len(data.keys()):
                        break
                    key = data.keys()[key_num]
                    key_num += 1
                    axes[row][col].plot(data[key])
                    axes[row][col].title.set_text(str(key).capitalize())
                    axes[row][col].vlines(
                        marker_x["GPS_START"],
                        data[key].min(),
                        data[key].max(),
                        linestyles="dashed",
                        colors="green",
                    )
                    axes[row][col].vlines(
                        marker_x["GPS_STOP"],
                        data[key].min(),
                        data[key].max(),
                        linestyles="dashed",
                        colors="red",
                    )
        elif choice == 11:
            break

        plt.show()


if __name__ == "__main__":
    main()
