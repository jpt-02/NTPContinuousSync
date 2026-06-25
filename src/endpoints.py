'''
Contains python endpoints for more precise times.
'''

# Imports

from timeanchor import OffsetAnchor
from ntpfunctions import NTPUpdater
import time
import threading

# Classes

class TruthEndpoint:
    '''
    An endpoint that ONLY reports time directly after an NTP sync.
    Serves as ground truth for testing other endpoints. Intended to 
    be run on a NTPUpdater object with a shorter interval than that 
    which it is being compared to.
    '''
    def __init__(self, push:function):
        '''
        push: function to be called upon NTP sync, intended to store 
            ground truth time and call now() from other endpoints to 
            compare
        '''
        self._lock = threading.Lock()
        self.offset_anchor = OffsetAnchor(0)
        self.push = push

    def callback(self, offset_anchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally. Calls push with the 
        calculated current time.
        '''
        with self._lock:
            self.offset_anchor = offset_anchor

        perf_delta = time.perf_counter_ns() - offset_anchor.perf_ref
        true_time = (offset_anchor.time_ref + perf_delta)*1e-9 + offset_anchor.offset
        self.push(true_time)

class SimpleEndpoint:
    '''
    An endpoint for corrected time that adds the latest offset to 
    whatever the current time is.
    '''
    def __init__(self):
        self._lock = threading.Lock()
        self.offset_anchor = OffsetAnchor(0)
        # add easy setup parameter that automatically makes NTPUpdater object here

    def callback(self, offset_anchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally.
        '''
        with self._lock:
            self.offset_anchor = offset_anchor

    def now(self):
        '''
        Returns float containing current, corrected time in seconds
        '''
        # Get the class-wide anchor under lock
        with self._lock:
            offset_anchor = self.offset_anchor
        # use local copy to do math
        perf_delta = time.perf_counter_ns() - offset_anchor.perf_ref
        return (offset_anchor.time_ref + perf_delta)*1e-9 + offset_anchor.offset
    
    def easy_setup(self, interval:int=300):
        '''
        Creates an NTPUpdater and subscribes the endpoint to it

        interval: seconds between each sync
        run_forever: if True, starts a while loop to run until 
            keyboard interrupt. Only really used for testing.
        '''
        updater = NTPUpdater(interval=5)
        updater.subscribe(self.callback)
        updater.run_threaded()

class UnadjustedEndpoint(SimpleEndpoint):
    '''
    Endpoint that gives unadjusted time for reference
    '''
    def now(self):
        return time.time()

class UseLastErrorEndpoint(SimpleEndpoint):
    '''
    Starts as SimpleEndpoint, but logs the error after each interval. Assumes subsequent 
    intervals will be off by this amount and adjust accordingly.
    '''
    def __init__(self, interval:int):
        '''
        interval: time, in seconds, between each sync. Must be the same as whatever NTPUpdater
            the endpoint is subscribed to.
        '''
        super().__init__()
        self.interval = interval
        self.slew_coefficient = 1
        self.startup = True
    
    def callback(self, new_anchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally.
        Also stores previous offset for calculations.
        '''
        if not self.startup:
            with self._lock:
                old_anchor = self.offset_anchor
            old_perf_delta = time.perf_counter_ns() - old_anchor.perf_ref
            old_unadjusted_now = (old_anchor.time_ref + old_perf_delta)*1e-9 + old_anchor.offset

            new_perf_delta = time.perf_counter_ns() - new_anchor.perf_ref
            new_unadjusted_now = (new_anchor.time_ref + new_perf_delta)*1e-9 + new_anchor.offset
            # to be multiplied to the perf_delta
            self.slew_coefficient = 1 + ((new_unadjusted_now - old_unadjusted_now)/self.interval)
        else:
            self.slew_coefficient = 1
            self.startup = False

        with self._lock:
            self.offset_anchor = new_anchor
            
    def now(self):
        '''
        Returns float containing current, corrected time in seconds
        '''
        with self._lock:
            offset_anchor = self.offset_anchor

        perf_delta = (time.perf_counter_ns() - offset_anchor.perf_ref)*self.slew_coefficient
        return (offset_anchor.time_ref + perf_delta)*1e-9 + offset_anchor.offset
        
        

    


if __name__ == '__main__':
    
    endpoint = SimpleEndpoint()
    updater = NTPUpdater(interval=5)
    updater.subscribe(endpoint.callback)
    updater.run_threaded()
    #endpoint.easy_setup(interval=5)



    # run until keyboard interrupt
    while True:
        time.sleep(2)
        print(endpoint.now())
