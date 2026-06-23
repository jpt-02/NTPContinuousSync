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
    def __init__(self):
        super().__init__()

    def now(self):
        return time.time()


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
