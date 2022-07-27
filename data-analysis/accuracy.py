# Gavin Heinrichs-Majetich
# gmh33@pitt.edu
# https://github.com/Elsklivet

import os
import argparse
import termcolor
import time
from collections import deque

arg_parser = argparse.ArgumentParser(description='Commit sensitivit analysis about the azimuth-trigger parameter for TrackCycle.',
usage="python accuracy.py -i <input file path> [-a <trigger angle> -d <debug level: integer>]")
arg_parser.add_argument("-i","--input", type=str, help="input file path from which to read sensor data (note: sensor data should be in a CSV style file)")
arg_parser.add_argument("-a","--angle", type=float, help="angle with which to perform sensitivity analysis (if none is provided, you will be prompted for input)")
arg_parser.add_argument("-d","--debug", type=int, help="debug level (0=no debugging (default), 1=debugging on)")

args = None
debug = False

# For earlier measurements, azimuth was in radians, not degrees.
# As such, here is a degrees -> radians table for a few of the common angles
# DEG | RAD
# =========
# 15  |  0.2617994
# 20  |  0.3490659
# 30  |  0.5235988
# 40  |  0.6981317
# 45  |  0.7853982
# 50  |  0.8726646
# 60  |  1.047198
# 70  |  1.22173
# 80  |  1.396263
# 90  |  1.570796
# 180 |  3.141593 (pi)

ANGLE = 45.0
TTFS = 3000 # This actually could be anywhere from 1000 to 15000 :)
GPS_START_TIME = 14000
GPS_CYCLE_SAVE_THRESHOLD = 10000
GPS_CYCLE_OFF_TIME = GPS_START_TIME + GPS_CYCLE_SAVE_THRESHOLD
LINES_PER_SECOND = 90 # It is around this number, not exactly 90
NUM_PTS_TO_AVG = 500

class Log():
    def error(msg: str):
        termcolor.cprint(f"ERROR: {msg}", 'red')
    def warning(msg: str):
        termcolor.cprint(f"WARNING: {msg}", 'yellow')
    def info(msg: str):
        print(f"INFO: {msg}")
        
def parse_line(line:str):
    # 0   1   2   3   4     5      6      7      8     9     10    11      12    13   14   15     16
    # lat,lon,alt,acc,speed,accelx,accely,accelz,gyrox,gyroy,gyroz,azimuth,pitch,roll,time,batpct,current
    vals = line.split(',')
    ret = None
    try:
        ret = {"lat":float(vals[0]),"lon":float(vals[1]),"azimuth":float(vals[11]),"time":int(vals[14]),"curr":int(vals[16])}
    except IndexError:
        ret = {"lat":float(vals[0]),"lon":float(vals[1]),"azimuth":float(vals[11])}
    finally:
        if not ret:
            raise Exception("Returned a none value from parse")
        return ret

def main():
    global args
    global debug
    global ANGLE
    global TTFS
    global GPS_START_TIME
    global GPS_CYCLE_SAVE_THRESHOLD
    global GPS_CYCLE_OFF_TIME
    global LINES_PER_SECOND
    global NUM_PTS_TO_AVG
    
    args = arg_parser.parse_args()

    if not args.input:
        arg_parser.print_help()
        exit(1)
    
    path = args.input
    
    if not os.path.exists(path):
        Log.error(f"File '{path}' was inaccessible or does not exist")
        exit(2)

    if args.debug:
        if args.debug != 0 and args.debug != 1:
            Log.warning(f"Expected debug level 0 or 1, got '{args.debug}'. Defaulting to 0.")
        else:
            debug = args.debug == 1


if __name__ == "__main__":
    main()