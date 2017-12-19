# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 08:59:41 2017

@author: Pierre
"""

from math import exp, pi, sqrt, sin, cos, asin, radians

g_0 = 9.80665 # m/s^2
R_star = 8.3144598 #gas constant, m^3 Pa/ K / mol
M = 0.0289644 #molar mass of air
M_helium = 0.004 #kg/mol
R = 6371 + 0.280 #km. Earth radius + temora altitude
 
parachute_area = pi * 0.3048 ** 2 #r = 1 foot in meters
payload_area = 0.3 * 0.3

C = 1.75 #from https://www.grc.nasa.gov/www/k-12/VirtualAero/BottleRocket/airplane/rktvrecv.html
C_box = 1.15 #from https://www.engineersedge.com/fluid_flow/rectangular_flat_plate_drag_14036.htm

#mass parameters of the balloon
pay_m = 1.2
bal_m = 1.2
gas_m = 2.912 #kg, estimated from https://www.webqc.org/ideal_gas_law.html

n = gas_m / M_helium

descent_m = pay_m + 0.05 * bal_m #DESCENT MASS 

def density_at_alt(alt):
    
    #altitutde is given in m above mean sea level
    #from https://en.wikipedia.org/wiki/Barometric_formula
    
    if 0 <= alt < 11000:
        p_b = 1.2250
        T_b = 288.15
        L_b = -0.0065
        h_b = 0
        
    elif 11000 <= alt < 20000:
        p_b = 0.36391
        T_b = 216.65
        L_b = 0
        h_b = 11000
        
    elif 20000 <= alt < 32000:
        p_b = 0.08803
        T_b = 216.65
        L_b = 0.001
        h_b = 20000
        
    elif 32000 <= alt < 47000:
        p_b = 0.01322
        T_b = 288.65
        L_b = 0.0028
        h_b = 32000
        
    if L_b != 0:
        
        fraction = T_b / (T_b + L_b*(alt - h_b))
        exponent = 1 + (g_0 * M)/(R_star * L_b)
        
        return p_b * (fraction) ** exponent
    
    if L_b == 0:
        exponent = (-g_0 * M * (alt - h_b))/(R_star * T_b)
        
        return p_b * exp(exponent)

def drag_at_alt(alt,descent_rate):
    
    rho = density_at_alt(alt)
    
    return 0.5 * descent_rate ** 2 * rho * (C * parachute_area + C_box * payload_area)
    #return 0.5 * C * descent_rate ** 2 * rho * (parachute_area + payload_area)

def find_bandchange(windband,v0):
    
    #extract data from the windband
    
    [alt_lower,alt_upper,dLat_dt,dLong_dt] = windband[:]
    
    bandwidth =  alt_upper - alt_lower
    
    #split the windband into band_sections...
    
    band_section = -0.001 * bandwidth
    
    sum_t = 0
    alti = alt_upper
    
    #...and find the time spent in each using kinematic equations
    
    for i in range (0,1000):
        a = 1/descent_m * (drag_at_alt(alti,v0) - g_0)
        
        dt = (-v0 - sqrt(v0 ** 2 + 2 * a * band_section))/a
        
        sum_t += dt
        
        alti += band_section
        v0 = v0 + a * dt
    
    #find the bandchange by multiplying the rate of change of latitude ...
    #and longitude by the total time spent, sum_t
    
    delta_lat = dLat_dt * sum_t
    delta_long = dLong_dt * sum_t
    
    return [sum_t,delta_lat,delta_long,alt_lower,v0]

def how_many_bands(winds,alt):
    for i in range(0,len(winds)):
        if winds[i][1] > alt:
            return i

    return len(winds)

def splat(state,winds):
    
    #extract the relevant quantities from the arguments
    
    [time,lat,long,alt,speed,heading] = state[0:6]
    
    #find the number of bands below the payload
    
    num_bands = how_many_bands(winds,alt)
    
    #call find_bandchange on each band and sum the results
    
    for i in range(num_bands-1,-1,-1):
        
        [_,delta_lat,delta_long,new_alt,new_speed] = find_bandchange(winds[i],speed)
        
        lat = lat + delta_lat
        long = long + delta_long
        speed = new_speed
        
    #write the results to the prediction file and return the current precition
        
    with open('prediction.txt','a') as h:
        h.write(time + ',' + str(round(lat,6)) + ',' + str(round(long,6)) + '\n')
    
    return (lat,long)
            

def how_far(prediction,time,lat2 = -34.37435, long2 = 147.859):
    
    #this function finds the distance between any two points of latitude and longitude
    #default arguments are for YERRALOON1's landing site.
    
    #Forumula from https://www.movable-type.co.uk/scripts/latlong.html
    
    [lat1,long1] = prediction[:]
    
    del_lat = radians(lat1 - lat2)
    del_long = radians(long1 - long2)

    lat1 = radians(lat1)
    lat2 = radians(lat2)
    
    a = sin(del_lat/2)**2 + cos(lat1)*cos(lat2)*sin(del_long/2)**2
    c = 2*asin(sqrt(a))
    dist = R*c
    
    return [time,dist] 

def radius_at_alt(alt,T,P):
    
    return ((3 * n * R_star * T)/(4 * pi * P)) ** (1/3)

def ac_at_alt(alt,temp,press):
    
    balloon_radius = radius_at_alt(alt,temp,press)
    area_unburst = payload_area + pi * (balloon_radius) ** 2
    area_burst = payload_area + parachute_area
    
    return area_burst/area_unburst