# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 09:09:55 2017

@author: Pierre
"""
from os import stat
from landing import temp_press_at_alt
from math import nan
from config import callsign_index,packet_index,time_index,lat_index,long_index,alt_index,speed_index,\
heading_index,satellites_index,internal_index,external_index,pressure_index,hum_check_index,callsign

read_pos = 0
safe_line = [nan,nan,nan,nan,nan,nan,nan,nan,nan,nan,nan,nan,nan]
indices = {}
missing_indices = {}
optional_quantities = {'Packets': 1,'Speed': 6,'Heading': 7,'Satellites': 8,'Internal': 9,'External': 10,'Pressure': 11,'Hum_Check': 12}

def file_empty(filepath):
    """file_empty checks the status of the file at filepath. If it's empty 
    (less than the approximate length of a telemetry line) or 
    non-existant, it returns True."""
    
    try:
        #120 is approximately the length of one $$YERRA line
        return (stat(filepath).st_size < 120)
    
    except FileNotFoundError:
        return True

def read_properly(f):
    """This function reads an open file object, f, recursively until it 
    a line of telemetry beginning with '$$YERRA' or it reaches the end
    of the file. It will either return the properly formatted telemetry
    as a list or (in the case of reaching the end) will return ['end']"""
    
    tmp = f.readline().split(',')
    
    if tmp[0] == callsign: #Telemetry found        
        
        return tmp
    
    elif tmp[0] == '': #End of file found
        return ['end']
    else: #Something else found. Will read next line.
        return read_properly(f) 

def record_launch_values(filepath):
    """record_launch_values() is called once as soon as the telemetry file 
    stops displaying false telemetry on boot. It records the start time,
    latitude, longitude and altitude of the launch from the file object
    f and returns them. If an error occurs, the function returns the"""
    
    try:
        
        #Open file as f
        
        with open(filepath) as f:
            f.seek(read_pos)  
            line = read_properly(f)
            update_read_position(f.tell())
            
        #record and return launch values
        
        start_time = line[time_index]
        start_lat = float(line[lat_index])
        start_long = float(line[long_index])
        start_alt = float(line[alt_index])
        
        if (indices.get('External') == None or indices.get('Pressure') == None):
            [start_temp,start_pres] = temp_press_at_alt(start_alt)
        
        else:
            start_temp = float(line[external_index]) + 273.15
            start_pres = float(line[pressure_index]) * 100
        
        return (start_time,start_lat,start_long,start_alt,start_temp,start_pres)

    except (IndexError,FileNotFoundError,ValueError):
        safe_launch_values = last_safe_line()
        return (safe_launch_values[2],safe_launch_values[3],safe_launch_values[4],safe_launch_values[5])
    
def add_telemetry(filepath):
    """ add_telemetry() takes the filepath of the telemtry file, opens it 
    as f and calls read_properly() on f. add_telemetry then updates the 
    global read_position in the file and formats the telemetry as strings,
    floats and ints. add_telemetry() calls false_telemetry() to check that
    the data is valid. If it is, the new, formatted line is returned and
    it becomes the new 'last safe line' of telemetry. If it is not valid, 
    the previous last safe line of telemetry is returned."""
    
    try:
        
        #Open the file as f and call read_properly
        
        with open(filepath) as f:
            f.seek(read_pos)
            line = read_properly(f)  
            update_read_position(f.tell())
            
        #Format the data
        
        if len(indices) == 8:
                        
            new_line = [line[callsign_index],line[packet_index],line[time_index], float(line[lat_index]),float(line[long_index]),\
                        float(line[alt_index]),float(line[speed_index]),float(line[heading_index]), int(line[satellites_index]),\
                        float(line[internal_index]),float(line[external_index]),float(line[pressure_index])]
            
            tmp = line[hum_check_index].split('*')
            new_line.extend([float(tmp[0]),tmp[1]])
            
            
        else:
            new_line = fill_in_missing_data(line)
        
        #Check for false telemetry
        
        if false_telemetry(filepath,new_line[2:8]):
            raise ValueError
            
        else:
            safe_line = new_line
            
        #If not false telemetry, set as the new safe_line and return
        
        make_new_safe_line(safe_line)
        
        return safe_line
        
    except (IndexError,ValueError):
        
        #If false telemetry, return the last safe line, stored globally
        
        return last_safe_line()
    

def false_telemetry(filepath,state = None):
    """false_telemetry() runs several tests on either the filepath or the
    current state to determine if the data are incorrect. It will return
    True if any of these tests are failed."""
    
    if state == None: #For the case where state has not been defined yet
        (start_time,start_lat,start_long,start_elev,start_temp,start_pres) = record_launch_values(filepath)
        return (start_time == '00:00:00' or start_lat == 0.0 or start_long == 0.0 or start_elev == 0.0)
    
    else:
        [time,lat,long,alt,speed,heading] = state[:] #extract the data
        
        last_lat = safe_line[3]
        last_long = safe_line[4]
        
        return ((abs(lat - last_lat) > 10) or (abs(long - last_long) > 10) or alt < 1)
    
    
def last_safe_line():
    """Returns the globally-defined last safe line"""
    return safe_line

def make_new_safe_line(new_safe_line):
    """Makes a new safe line from the input"""
    
    global safe_line
    
    safe_line = new_safe_line
    
    
def update_read_position(new_read_pos):
    """Updates the read position to the supplied value"""
    
    global read_pos
    
    read_pos = new_read_pos
    
def skip_telemetry(filepath):
    """skip_telemetry() skips to the end of the user-specified telemetry file
    to ignore any telemetry from previous flights"""
    
    with open(filepath) as f:
        
            #skip to the end, update read position
            f.seek(2)
            update_read_position(f.tell())
            
def identify_provided_data():
    
    global indices
    
    [callsign_index,packet_index,time_index,lat_index,long_index,alt_index,speed_index,\
     heading_index,satellites_index,internal_index,external_index,pressure_index,hum_check_index] = indices[:]
    
    #Identify if any vital components are missing
    
    if (callsign_index == 'NI' or time_index == 'NI' or lat_index == 'NI' or long_index == 'NI' or alt_index == 'NI'):
        
        raise Exception('Callsign, time, latitude, longitude and altitude data MUST be provided. \
                        At least one has been marked as NI (not included)')
        
    for index in [packet_index,speed_index,heading_index,satellites_index,\
                  internal_index,external_index,pressure_index,hum_check_index]:
        populate_dictionary(index)
        
        
def fill_in_missing_data(line):
    
    new_line = [line[callsign_index],0,line[time_index], float(line[lat_index]),\
            float(line[long_index]),float(line[alt_index]),0,0,0,0,0,0,0,0]
    
    included = list(indices.keys())
    
    for elem in included:
        
        if elem == 'Speed' or elem == 'Heading' or elem == 'Internal' or elem == 'External' or elem == 'Pressure':
        
            new_line[optional_quantities[elem]] = float(line[indices[elem]])
            
        elif elem == 'Satellites':
            
            new_line[optional_quantities[elem]] = int(line[indices[elem]])
            
        elif elem == 'Hum_Check':
            
            tmp = line[hum_check_index].split('*')
            new_line[12:14] = [float(tmp[0]),tmp[1]]
            
        else:
            
            new_line[optional_quantities[elem]] = line[indices[elem]]
        
    return new_line

def populate_dictionary(index):
    
    if not(index == 'NI'):
        indices[dictionary_lookup(index,optional_quantities)] = index
        
def dictionary_lookup(value,dictionary):
    
    dkeys = list(dictionary.keys())
    
    for k in dkeys:
        if dictionary[k] == value:
            return k
        
    return None