'''
Contains functions for optimizing the window and tolerance arguments 
for the initialization of an NTPUpdater class
'''

# Imports

import time
import numpy as np

# Function 

def profile_hardware(samples=10000):
    '''
    Returns a theoretically safe value (ns) for window
    '''
    deltas = np.zeros(samples)
    for i in range(samples):
        p1 = time.perf_counter_ns()
        _ = time.time_ns()
        p2 = time.perf_counter_ns()
        deltas[i] = p2 - p1
    return np.max(deltas)

# Main

if __name__ == '__main__':
    print(profile_hardware())