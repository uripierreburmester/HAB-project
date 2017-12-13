# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 09:09:55 2017

@author: Pierre
"""

import os
read_pos = 0
safe_line = []

def file_empty(filepath):
    try:
        return (os.stat(filepath).st_size < 120)
    
    except FileNotFoundError:
        return True

def read_properly(f):
    tmp = f.readline().split(',')
    
    if tmp[0] == '$$YERRA':
        return tmp
    elif tmp[0] == '':
        return ['end']
    else:
        return read_properly(f)

def record_launch_values(filepath):
    
    global read_pos
    
    with open(filepath) as f:
        f.seek(read_pos)  
        
        line = read_properly(f)
        
        start_time = line[2]
        start_lat = float(line[3])
        start_long = float(line[4])
        start_elev = float(line[5])
        
        read_pos = f.tell()    
    
    return (start_time,start_lat,start_long,start_elev)


def add_telemetry(filepath):
    try:
        global read_pos
        global safe_line
        
        with open(filepath,'r') as f:
            
            f.seek(read_pos)
            last_line = read_properly(f)  
            read_pos = f.tell()
            
            
        if false_telemetry(filepath,[last_line[2],float(last_line[3]),\
                float(last_line[4]),float(last_line[5]),float(last_line[6]),\
                float(last_line[7])]):
            raise ValueError
        
        safe_line = [last_line[0],last_line[1],last_line[2], float(last_line[3]),\
                float(last_line[4]),float(last_line[5]),float(last_line[6]),\
                float(last_line[7]), int(last_line[8]),float(last_line[9]),\
                float(last_line[10]),last_line[11],last_line[12]]
        
        return safe_line
        
    except (IndexError,ValueError):
        return safe_line
    

def false_telemetry(filepath,state = None):
    
    if state == None:
        (start_time,start_lat,start_long,start_elev) = record_launch_values(filepath)
        return (start_time == '00:00:00' or start_lat == 0.0 or start_long == 0.0 or start_elev == 0.0)
    
    else:
        [time,lat,long,alt,speed,heading] = state[:] #state variable
        
        return (not(-40 < lat < 0) or not(110 < long < 155) or alt < 1)