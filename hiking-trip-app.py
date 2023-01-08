#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 30 20:06:15 2022

@author: richard
"""

import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import streamlit as st

plt.close('all')


st.title('Hiking pace calculator')

col1, col2 = st.columns(2)
with col1:
    av_pace = st.slider('Average pace [km/hr]', 0.1, 10.0, 5.0, step=0.1)
    hike_distance = st.slider('Total hike distance [km]',
                                    0.5, 100.0, 30.0, step=0.5)
    t_start = st.time_input('Start time [HH:MM:SS]',
                            dt.datetime(2000, 1, 1, hour=7, minute=40))
with col2:
    rest_interval = st.slider('Distance between rests [km]', 
                                    0.1, 20.0, 5.0, step=0.1)
    standard_rest = st.slider('Standard rest period [minutes]',
                                    0, 60, 15, step=1)
    lunch_rest = st.slider('Lunch rest period  [minutes]',
                                 0 , 60, 40, step=1)


t_start = dt.datetime(2000, 1, 1).replace(hour=t_start.hour, minute=t_start.minute)

# av_pace = 4.4 #km/hr - average pace
# hike_distance = 32 # km - total hike distance
# rest_interval = 5 # km - distance interval between rests
# standard_rest = 15 # mins - normal rest time
# lunch_rest = 60 # mins - lunch rest
# t_start = dt.datetime(2000, 1, 1, hour=7, minute=40) #  start time for hike

# Modify rest interval to nearest value which has integer division with av_pace (km/min)
rest_interval = (av_pace/60) * np.round(rest_interval/(av_pace/60))

params = {'av_pace' : av_pace,
          'hike_distance' : hike_distance,
          'rest_interval' : rest_interval,
          'standard_rest' : standard_rest,
          'lunch_rest' :  lunch_rest,
          't_start' : t_start}

##############################################################################

def calculate_hike_stats(params):
    
    # calculate rests and total hike time:
    n_rests = (hike_distance-1)//rest_interval
    params['n_rests'] = n_rests
    
    total_rest = (dt.timedelta(minutes=n_rests*standard_rest)
                  + dt.timedelta(minutes=(lunch_rest - standard_rest)))
    params['total_rest'] = total_rest

    total_hiketime = dt.timedelta(hours=(hike_distance/av_pace))
    params['total_hiketime'] = total_hiketime
    
    # calculate arrival time
    t_arrival = t_start + total_hiketime + total_rest
    params['t_arrival'] = t_arrival

    effective_pace = np.round(3600*hike_distance/(total_hiketime.seconds + total_rest.seconds), 2)
    params['effective_pace'] = effective_pace
    
    print('Departing at: ', t_start.time())
    print('Average pace: {0} km/hr'.format(av_pace))
    print('Resting every {0} km, results in {1} rests totalling {2} (HH:MM:SS) '.format(
        rest_interval, n_rests, total_rest))
    print('Total hike time (HH:MM:SS): ', total_hiketime)
    print('Effective pace (inc\' rests): {0} km/hr'.format(effective_pace))
    print('Estimated arrival time: ', t_arrival.time())

    return params

def create_hike_plots(params):
    
    rest_interval = params['rest_interval']
    t_start = params['t_start']
    lunch_rest = params['lunch_rest']
    standard_rest = params['standard_rest']
    t_arrival = params['t_arrival']
    av_pace = params['av_pace']
    
    # initialise some datetime constants
    t_sunrise = dt.datetime(2000, 1, 1, hour=6,minute=30)
    t_sunset= dt.datetime(2000, 1, 1, hour=19,minute=00)
    
    d = [0]
    i = 1
    rest_time = 0
    t = np.arange(t_sunrise, t_sunset+dt.timedelta(minutes=1), dt.timedelta(minutes=1))
    
    # Calculate progress:
    for t_sim in t[:-1]:
        d_sim = d[i-1]
        # Create the 'rest' flag based on the current distance:
        rest = (abs(d_sim - rest_interval*(np.round(d_sim/rest_interval))) < 1e-4) 
        # set the length of rest depending on current simulation time
        if (t_sim > dt.datetime(2000, 1, 1, hour=12) ) and (t_sim < dt.datetime(2000, 1, 1, hour=14, minute=0)):
            rest_period = lunch_rest
        else: rest_period = standard_rest
        
        
        if t_sim < t_start:
            d.append(0)
            
        elif (t_sim < t_arrival) and (t_sim > t_start):
            # are we resting?
            if rest and (d_sim > 0) and (rest_time < rest_period):
                rest_time += 1
                d.append(d[i-1])
            # are we restarting after a rest?
            elif rest_time >= rest_period:
                rest_time = 0
                d.append(d_sim + av_pace/60)
            # otherwise we are in a normal hiking window
            else: d.append(d_sim + av_pace/60)
            
        else:
            d.append(d_sim)
    
        i+=1 
    
    df = pd.DataFrame(index = t, data = {'distance' : d})
    
    # plot figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(ax=ax, linewidth=5, legend=False)
    # add some annotations
    plt.text(dt.datetime(2000, 1, 1, hour=12, minute=1),
             0.1*params['hike_distance'],
             ' lunch window', fontsize=12)
    ax.axvspan(dt.datetime(2000, 1, 1, hour=12),
               dt.datetime(2000, 1, 1, hour=14), alpha=0.2)
    plt.vlines(params['t_start'], 0, params['hike_distance'],
               linestyles='--', color='r', linewidth=3) 
    plt.vlines(params['t_arrival'], 0, params['hike_distance'],
               linestyles='--', color='r', linewidth=3) 
    ax.set_xlabel('Time of day')
    ax.set_ylabel('Distance travelled [km]')
    ax.set_ylim(0, params['hike_distance'])
    plt.show()
    return fig

def hours_minutes(td):
    if type(td) == dt.timedelta:
        hours = str(td.seconds//3600).zfill(2)
        minutes = str((td.seconds//60)%60).zfill(2)
        s = '{0}:{1}'.format(hours, minutes)
    elif type(td) == dt.datetime:
        hours = str(td.hour).zfill(2)
        minutes = str(td.minute).zfill(2)        
        s = '{0}:{1}'.format(hours, minutes)
    return s

params = calculate_hike_stats(params)
fig = create_hike_plots(params)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label = 'Nunber of rests', value = int(params['n_rests']))
col2.metric(label = 'Time resting [HH:MM:SS]', value = hours_minutes(params['total_rest']))
col3.metric(label = 'Time hiking [HH:MM:SS]', value = hours_minutes(params['total_hiketime']))
col4.metric(label = 'Arrival time [HH:MM:SS]', value = hours_minutes(params['t_arrival']))
col5.metric(label = 'Effective pace [km/hr]', value = params['effective_pace'])

st.write(fig)
