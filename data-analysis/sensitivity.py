# Gavin Heinrichs-Majetich
# gmh33@pitt.edu
# https://github.com/Elsklivet

import os
import argparse
import termcolor
import time
from collections import deque

arg_parser = argparse.ArgumentParser(description='Commit sensitivit analysis about the azimuth-trigger parameter for TrackCycle.',
usage="python sensitivity.py -i <input file path> [-a <trigger angle> -d <debug level: integer>]")
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
        level = termcolor.colored(f"ERROR", 'red')
        print(f"[ {level} ] {msg}")
    def warning(msg: str):
        level = termcolor.colored(f"WARNING", 'yellow')
        print(f"[ {level} ] {msg}")
    def ok(msg: str):
        level = termcolor.colored(f"OK", 'green')
        print(f"[ {level} ] {msg}")
    def info(msg: str):
        print(f"[ INFO ] {msg}")
        
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

    if args.angle == None:
        while True:
            try:
                ANGLE = int(input('Enter an angle about which to perform sensitivity analysis: '))
                break
            except ValueError:
                Log.error("Invald input, please only enter a floating point value.")
    else:
        ANGLE = args.angle
    
    # Simulate 
    
    # Will run through each line and track azimuth. Determine if GPS would be on or off
    # at the time. It takes about three seconds to get first fix. Factor in delays and what not
    # to then note when the GPS would turn off and how many --GPS LOCATION CHANGED-- would be picked up by
    # an always on versus with azimuth trigger angle.
    
    start = time.time()
    
    lines = []
    with open(path, 'r') as infile:
        Log.info(f"Begins processing {path}.")
        lines = infile.readlines()
        
    total = len(lines)
    
    last_X_azimuth = deque(maxlen=NUM_PTS_TO_AVG)
    last_trigger_azimuth = 0
    last_trigger_time = 0
    last_measured_time = 0
    
    points_collected = [0, 0]
    points = [[], []]
    # RMSE = sqrt( ( sum( (predicted - actual)^2 ) ) / n )
    rmse = 0
    gps_on = True
    off_cycles = 0
    on_cycles = 0
    time_off = 0
    time_on = 0
    
    current = 0
    
    # Should be feasible in a single pass
    for (idx, line) in enumerate(lines):
        if idx == 0:
            continue
        
        # Marker lines
        if line.startswith("--"):
            if line.startswith("--GPS LOCATION CHANGED--"):
                # New GPS location
                points_collected[0] += 1
                time_diff = last_measured_time - last_trigger_time
                # It is important to consider that points are not collected
                # for TTFS milliseconds after GPS is initially turned on
                if gps_on:
                    if time_diff >= TTFS: # CHANGE THIS LINE (>= GPS_START_TIME) IF YOU WANT POINTS DRAWN TO MAP AND NOT JUST POINTS COLLECTED
                        points_collected[1] += 1
                    elif off_cycles == 0:
                        points_collected[1] += 1
        # Normal numerical lines
        else:
            try:
                data = parse_line(line)
            except Exception:
                Log.error(f"Line number {idx} got a None from parse: '{line}'")
            
            # Get "current time"
            if "time" in data:
                now = data["time"]
            else:
                now = (idx // LINES_PER_SECOND) * 1000
            
            if "curr" in data:
                current += abs(data["curr"])
                
            last_measured_time = now
            
            points[0].append({"lat": data["lat"], "lon": data["lon"]})
            
            if gps_on:
                points[1].append({"lat": data["lat"], "lon": data["lon"]})
                time_on += 1
            else:
                time_off += 1
            
            # Collect azimuth, popping off the left side
            # if we need to make space.
            if len(last_X_azimuth) == NUM_PTS_TO_AVG:
                last_X_azimuth.popleft()
            last_X_azimuth.append(data["azimuth"])
            
            # Trigger azimuth will actually be the current average of 
            # last (up to) 100 azimuth measurements
            avg_azimuth = int(sum(last_X_azimuth)/len(last_X_azimuth))
            # Collect differences in angle and time for duty cycling 
            angle_diff = abs(abs(avg_azimuth) - abs(last_trigger_azimuth))
            time_diff = (now - last_trigger_time)
            
            # Simulate duty cycle
            if not gps_on and time_diff >= GPS_CYCLE_SAVE_THRESHOLD and angle_diff >= ANGLE:
                on_cycles += 1
                gps_on = True
                last_trigger_time = now
            if gps_on and (now - last_trigger_time) >= GPS_CYCLE_OFF_TIME and angle_diff < ANGLE:
                off_cycles += 1
                gps_on = False
                last_trigger_time = now
    
    time_off = (time_off / LINES_PER_SECOND)
    time_on = (time_on / LINES_PER_SECOND)
    end = time.time()
    Log.ok(f"Finished simulation in {(end-start)} seconds")
    print(
f"""========================================================================
{ANGLE=}
{TTFS=}
{GPS_START_TIME=}
{GPS_CYCLE_SAVE_THRESHOLD=}
{GPS_CYCLE_OFF_TIME=}
{LINES_PER_SECOND=}
{NUM_PTS_TO_AVG=}
------------------------------------------------------------------------
GPS cycled off:                  {off_cycles} times
GPS cycled back on:              {on_cycles} times
GPS seconds on (estimate):       {time_on} s
GPS seconds off (estimate):      {time_off} s
Percent time off (estimate):     {(time_off/time_on)*100}%
Average current:                 {current/total} mA
Points collected always on:      {points_collected[0]}
Points collected duty cycled:    {points_collected[1]}
Accuracy (as percent):           {(points_collected[1]/points_collected[0])*100}%
========================================================================"""
)  

if __name__=="__main__":
    main()       
            
    
    
