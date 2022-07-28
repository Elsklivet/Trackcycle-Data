# Gavin Heinrichs-Majetich
# gmh33@pitt.edu
# https://github.com/Elsklivet

import os
import argparse
import termcolor
import time
import multiprocessing
import math
from pyproj import Geod

arg_parser = argparse.ArgumentParser(description='Commit sensitivit analysis about the azimuth-trigger parameter for TrackCycle.',
usage="python accuracy.py -t <input file path> -b <input file path> [-d <debug level: integer>]")
arg_parser.add_argument("-t","--there", type=str, help="input file path from which to read ALWAYS-ON sensor data")
arg_parser.add_argument("-b","--back", type=str, help="input file path from which to read BASELINE or DUTY-CYCLED sensor data")
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
    
def read_and_parse(path:str, queue:multiprocessing.Queue, mode:str):
    start = time.time()
    Log.info(f"Begins processing '{path}'")
    lines = []
    try:
        with open(path, 'r') as infile:
            for idx, line in enumerate(infile.readlines()):
                if idx == 0:
                    continue
                elif line.startswith("--"):
                    continue
                lines.append(parse_line(line))
    except Exception:
        Log.error(f"Failed to parse file '{path}'")
        return
    end = time.time()
    Log.ok(f"Finished processing '{path}' in {end-start} seconds")
    queue.put((mode,lines))
    
def haversine(coord1, coord2):
    # Kindly borrowed from https://janakiev.com/blog/gps-points-distance-python/
    R = 6372800  # Earth radius in meters
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

def main():
    global args
    global debug
    global TTFS
    global GPS_START_TIME
    global GPS_CYCLE_SAVE_THRESHOLD
    global GPS_CYCLE_OFF_TIME
    global LINES_PER_SECOND
    global NUM_PTS_TO_AVG
    
    args = arg_parser.parse_args()

    if not args.there or not args.back:
        arg_parser.print_help()
        exit(1)
    
    alwayson_path = args.there
    
    if not os.path.exists(alwayson_path):
        Log.error(f"File (--there) '{alwayson_path}' was inaccessible or does not exist")
        exit(2)
        
    cycled_path = args.back
    
    if not os.path.exists(cycled_path):
        Log.error(f"File (--back) '{cycled_path}' was inaccessible or does not exist")
        exit(3)

    if args.debug:
        if args.debug != 0 and args.debug != 1:
            Log.warning(f"Expected debug level 0 or 1, got '{args.debug}'. Defaulting to 0.")
        else:
            debug = args.debug == 1
            
    # Need to come up with some way to read files of a different size as well as backwards and just "guess"?

    context = multiprocessing.get_context('spawn')
    queue = context.Queue()
    there_proc = multiprocessing.Process(target=read_and_parse, args=(alwayson_path, queue, "there"))
    back_proc = multiprocessing.Process(target=read_and_parse, args=(cycled_path, queue, "back"))
    
    there_proc.start()
    back_proc.start()
    
    response = []
    response.append(queue.get())
    response.append(queue.get())
    
    there_proc.join()
    back_proc.join()
    
    there = back = None
    
    for res in response:
        if res[0] == "there":
            there = res[1]
        else:
            back = res[1]
    
    # print(there[0])
    # print(back[0])
    
    if not there or type(there) != list:
        Log.error(f"Respone 'there' was somehow not a list")
    if not back or type(back) != list:
        Log.error(f"Respone 'back' was somehow not a list")
    
    # Now we have to process those points
    

if __name__ == "__main__":
    main()