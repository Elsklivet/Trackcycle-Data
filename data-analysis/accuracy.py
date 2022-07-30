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
from random import uniform
from pyproj import CRS, Transformer
from shapely.geometry import Point, LineString
# import pandas as pd
# import geopandas as gpd
# from geopandas import GeoDataFrame

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
            last_lat = last_lon = None
            for idx, line in enumerate(infile.readlines()):
                # A couple special cases that need skipped by the processor:
                #  *  The first line in each file is the column-header row
                #  *  Any lines starting with "--" represent special markers for some of the other analyzers
                #  *  The sensors collect several tens of times per second, and the GPS won't change in that time,
                #     so we can significantly save on space (and make our calculations easier) by skipping repeats.
                if idx == 0:
                    continue
                elif line.startswith("--"):
                    continue
                data = parse_line(line)
                
                if data['lat'] == 0 and data['lon'] == 0:
                    continue

                if not last_lat and not last_lon:
                    # Initialize if not exists
                    last_lat = data['lat']
                    last_lon = data['lon']
                elif data['lat'] == last_lat and data['lon'] == last_lon:
                    # Skip if the data for this line is the same as the last 
                    # collected data
                    continue
                else:
                    # Append the data otherwise
                    last_lat = data['lat']
                    last_lon = data['lon']
                    lines.append(data)
    except Exception:
        Log.error(f"Failed to parse file '{path}'")
        return
    end = time.time()
    Log.ok(f"Finished processing '{path}' in {end-start} seconds")
    queue.put((mode,lines))
    
def haversine(coord1: tuple, coord2: tuple):
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

def reproject_point(lon, lat):
    # Kindly borrowed from https://gis.stackexchange.com/questions/433825/interpolating-series-of-points-between-two-locations-using-python
    in_crs = CRS.from_epsg(4326)
    out_crs = CRS.from_epsg(2272)
    proj = Transformer.from_crs(in_crs, out_crs, always_xy=True)
    x, y = proj.transform(lon, lat)
    return x, y

def generate_random_points_on_line(number, line):
    # Kindly borrowed from https://gis.stackexchange.com/questions/433825/interpolating-series-of-points-between-two-locations-using-python
    points = []
    while len(points) < number:
        point = line.interpolate(uniform(0, line.length))
        points.append(point)
    return points

def main():
    global args
    global debug
    global TTFS
    global GPS_START_TIME
    global GPS_CYCLE_SAVE_THRESHOLD
    global GPS_CYCLE_OFF_TIM
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
        exit(2)

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
        exit(3)
    if not back or type(back) != list:
        Log.error(f"Respone 'back' was somehow not a list")
        exit(3)
    
    # Now we have to process those points
    
    # Need lengths of arrays for clamping
    there_len = len(there)
    back_len = len(back)
    
    there_duration = there[-1]['time']-there[0]['time']
    back_duration = back[-1]['time']-back[0]['time']

    # Difference in duration is important for determining interpolation
    diff = abs(there_len - back_len)
    
    if debug:
        Log.info(f"Length of first trip={there_len}")
        Log.info(f"Length of back trip={back_len}")
        Log.info(f"Duration difference of {abs(there_duration-back_duration)/1000} s with first trip={there_duration/1000} s and back={back_duration/1000} s")
        dis = haversine((there[0]['lat'], there[0]['lon']), (back[-1]['lat'], back[-1]['lon']))
        Log.info(f"Distance between initial points of {dis} meters")
    
    geoid = Geod(ellps="WGS84")

    # Begin by interpolating shorter list to be size of longer list
    if there_len < back_len:
        # First array is shorter
        idx = 0
        while idx < len(there):
            current = there[idx]['curr']
            curr_time = there[idx]['time']
            next_time = None
            if idx+1 < len(there):
                next_time = there[idx+1]['time']
            if next_time:
                time_diff = abs(next_time - curr_time)
                time_diff /= 1000
                if debug:
                    Log.info(f"Time difference of {time_diff}")
                if time_diff > 1:
                    if debug:
                        Log.info(f"Detected time difference")
                    # Longer than one second in between, interpolate here
                    start_point = Point(there[idx]['lat'], there[idx]['lon'])
                    end_point = Point(there[idx+1]['lat'], there[idx+1]['lon'])
                    line = LineString([start_point, end_point])
                    points = geoid.npts(there[idx]['lat'], there[idx]['lon'], there[idx+1]['lat'], there[idx+1]['lon'], time_diff)
                    if debug:
                        Log.info(f"Initial point = {(there[idx]['lat'], there[idx]['lon'])}")
                        Log.info(f"{points}")
                        Log.info(f"Final point = {(there[idx+1]['lat'], there[idx+1]['lon'])}")
                    seconds = 1
                    for point in points:
                        inst = {'lat': point[0], 'lon':point[1], "azimuth":0, "time": curr_time + seconds*1000, "curr": current}
                        there.insert(idx+1, inst)
                        idx += 1
                        seconds +=1
            idx += 1

        if len(there) < len(back):
            idx = len(there) - 1
            diff = len(back) - len(there)
            points = geoid.npts(there[idx]['lat'], there[idx]['lon'], back[-1]['lat'], back[-1]['lon'], diff)
            if debug:
                Log.info(f"Initial point = {(there[idx]['lat'], there[idx]['lon'])}")
                Log.info(f"{points}")
                Log.info(f"Final point = {(back[-1]['lat'], back[-1]['lon'])}")
            seconds = 1
            for point in points:
                inst = {'lat': point[0], 'lon':point[1], "azimuth":0, "time": curr_time + seconds*1000, "curr": current}
                there.insert(idx+1, inst)
                idx += 1

        there.reverse()

    elif back_len < there_len:
        # Second array is shorter
        idx = 0
        while idx < len(back):
            current = back[idx]['curr']
            curr_time = back[idx]['time']
            next_time = None
            if idx+1 < len(back):
                next_time = back[idx+1]['time']
            if next_time:
                time_diff = abs(next_time - curr_time)
                time_diff /= 1000
                if debug:
                    Log.info(f"Time difference of {time_diff}")
                if time_diff > 1:
                    if debug:
                        Log.info(f"Detected time difference")
                    # Longer than one second in between, interpolate here
                    points = geoid.npts(back[idx]['lat'], back[idx]['lon'], back[idx+1]['lat'], back[idx+1]['lon'], time_diff)
                    if debug:
                        Log.info(f"Initial point = {(back[idx]['lat'], back[idx]['lon'])}")
                        Log.info(f"{points}")
                        Log.info(f"Final point = {(back[idx+1]['lat'], back[idx+1]['lon'])}")
                    seconds = 1
                    for point in points:
                        inst = {'lat': point[0], 'lon':point[1], "azimuth":0, "time": curr_time + seconds*1000, "curr": current}
                        back.insert(idx+1, inst)
                        idx += 1
                        seconds +=1

            idx += 1

        if len(back) < len(there):
            idx = len(back) - 1
            diff = len(there) - len(back)
            points = geoid.npts(back[idx]['lat'], back[idx]['lon'], there[-1]['lat'], there[-1]['lon'], diff)
            if debug:
                Log.info(f"Initial point = {(back[idx]['lat'], back[idx]['lon'])}")
                Log.info(f"{points}")
                Log.info(f"Final point = {(there[-1]['lat'], there[-1]['lon'])}")
            seconds = 1
            for point in points:
                inst = {'lat': point[0], 'lon':point[1], "azimuth":0, "time": curr_time + seconds*1000, "curr": current}
                back.insert(idx+1, inst)
                idx += 1

        back.reverse()

    # In the rare occasion they are of equal length, nothing can safely be interpolated.
    if debug:
        Log.info(f"There preview {there[-5:]}")
        Log.info(f"Back preview {back[-5:]}")
        Log.info(f"Length of there = {len(there)}")
        Log.info(f"Length of back = {len(back)}")
    if len(there) != len(back):
        Log.error("Lengths not equal")
    # Root mean squared error
    # RMSE = sqrt( ( sum( (predicted - actual)^2 ) ) / n )
    rmse = 0
    
    for there_point, back_point in zip(there,back):
        dis = haversine((there_point['lat'], there_point['lon']), (back_point['lat'], back_point['lon']))
        Log.info(f"{(there_point['lat'], there_point['lon'])} @ {(back_point['lat'], back_point['lon'])}")
        # Log.info(f"Distance = {dis}")
        rmse += dis*dis

    rmse /= there_len
    rmse = math.sqrt(rmse)
    Log.info(f"RMSE = {rmse}")

    

    # there_df = pd.DataFrame(there)
    # back_df = pd.DatetimeIndex(back)

    # there_geom = [Point(xy) for xy in zip(there_df['lat'], there_df['lon'])]
    # there_gdf = GeoDataFrame(there_df, there_geom)

    # back_geom = [Point(xy) for xy in zip(back_df['lat'], back_df['lon'])]
    # back_gdf = GeoDataFrame(back_df, back_geom)

    # fig, world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')).plot(figsize=(10, 6))

    # there_gdf.plot(ax=world, marker='o', color='red', markersize=15)
    # back_gdf.plot(ax=world, marker='o', color='blue', markersize=15)

if __name__ == "__main__":
    main()
