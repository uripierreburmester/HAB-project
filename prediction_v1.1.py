# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 13:05:27 2017

@author: Pierre
"""

import time as t
import landing
import other_commands as oc
import wind

################################################

#import matplotlib.pyplot as plt
#import numpy as np
#
#how_far_list = []
#times_list = []
#predictions_made = 0

#################################################

#fp = 'test2.txt'
fp = 'YERRALOON1_DATA\\telemetry.txt'

#Quantities
rising = False
telemetry = []
winds = []
wind_band_width = 100
sleep_time = 0.001 #seconds
prediction_gap = 0.08 #seconds
last_prediction_time = 0
telemetry_cutoff = 4000;


#check if the file has any data written to it. If not, wait sleep_time seconds and try again
while oc.file_empty(fp):
    print('Telemetry file empty or non-existant')
    t.sleep(sleep_time)

#Record the position and time of the launch site, ignoring false telemetry
while oc.false_telemetry(fp):
    print('Waiting for launch site values')
    t.sleep(sleep_time)

(start_time,start_lat,start_long,start_elev) = oc.record_launch_values(fp)
    
#MAIN LOOP
    
while len(telemetry) < telemetry_cutoff:
    
    #add a new line to the telemetry list    
    new_telemetry = oc.add_telemetry(fp)
    
    #extract the relevant quantities
    state = new_telemetry[2:8]
    alt = new_telemetry[5]
    
    #Detect when the balloon has started to lift off, set the lower wind band data
    if rising == False and (alt - start_elev) > 100:
        rising = True
        wind_lower_data = state[:]
            
    if rising == True:
        
        #add the new telemetry to the list of telemetry
        telemetry.append(new_telemetry)
        
        #If a wind band has been crossed ...
        if (alt - wind_lower_data[3]) >= wind_band_width:
            
            #...Make a new wind band starting from the current location
            
            [winds,wind_lower_data] = wind.make_new_band(state,wind_lower_data,winds)
            
        #If sufficient time has passed, predict the landing site
        
        if (t.time() - last_prediction_time) >= prediction_gap:
            
            prediction = landing.splat(state,winds)
            last_prediction_time = t.time()
            
            landing.check_drag_coefficient()
            
            #################################################
            
#            how_far_list.append(landing.how_far(prediction,state[0])[1])
#            times_list.append(landing.how_far(prediction,state[0])[0])
#            predictions_made += 1
            
            ##################################################
        
            #Find some way to transmit prediction?
    
    #put the code to sleep until new data is expected
    t.sleep(sleep_time)
    
    
##############################################################
    
#x = np.linspace(0,130,predictions_made)
#plt.xticks(x,times_list,rotation = 'vertical')
#plt.plot(x,how_far_list)
#plt.show()

###############################################################