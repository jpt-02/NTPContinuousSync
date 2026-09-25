'''
Optimization 0 | Pure Python

Contains endpoints (classes that calculate and return the current time) that are implemented purely in python.
'''

# Imports

import threading
import time
from pysync.anchors import OffsetAnchor
from pysync.ntpupdater import NTPUpdater

# Classes

class Truth:
    '''
    An endpoint that ONLY reports time directly after an NTP sync.
    Serves as ground truth for testing other endpoints. Intended to 
    be run on a NTPUpdater object with a shorter interval than that 
    which it is being compared to.
    '''
    def __init__(self, push):
        '''
        push: function to be called upon NTP sync, intended to store 
            ground truth time and call now() from other endpoints to 
            compare
        '''
        #self._lock = threading.Lock()
        self.true_time = time.time()
        self.push = push

    def callback(self, new_anchor:OffsetAnchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally. Calls push with the 
        calculated current time.
        '''
        if new_anchor: # no lock needed here because nothing else accesses this variable
            perf_delta = time.perf_counter_ns() - new_anchor.perf_ref
            self.true_time = (new_anchor.time_ref + perf_delta)*1e-9 + new_anchor.offset
            self.push(self.true_time)
        else:
            self.push(self.true_time)
            print(f'Truth failed a sync at {time.time()}, test may be corrupted.')

    def link_to_updater(self, updater:NTPUpdater):
        '''
        Links the endpoint to an NTPUpdater. Does nothing here, just stops the error.
        '''
        pass

class Simple:
    '''
    An endpoint for corrected time that adds the latest offset to 
    whatever the current time is.
    '''
    def __init__(self):
        self._lock = threading.Lock()
        self.now = self._now_startup

    def _now(self):
        '''
        Used for self.now after startup is complete.
        
        Returns float containing current, corrected time in seconds
        '''
        # Get the class-wide anchor under lock
        with self._lock:
            offset_anchor = self.offset_anchor
        # use local copy to do math
        perf_delta = time.perf_counter_ns() - offset_anchor.perf_ref
        return (offset_anchor.time_ref + perf_delta)*1e-9 + offset_anchor.offset

    def _now_startup(self):
        '''
        Startup implementation for self.now. Placeholder until startup is complete.

        Returns float containing uncorrected time in seconds
        '''
        print('Warning: now() method called before startup finished')
        return time.time_ns()*(1e-9)

    def link_to_updater(self, updater:NTPUpdater):
        '''
        Links the endpoint to an NTPUpdater. Not strictly necessary, but allows the endpoint 
        to inherit things like interval if they are needed for certain now() calculations.
        '''
        pass

        ## EXAMPLE IMPLEMENTATION:
        # with self._lock:
        #    self.interval = updater.interval
            
    def callback(self, new_anchor:OffsetAnchor):
        '''
        Method called each time there is a new NTP sync.
        Stores the offset_anchor object locally. If first time, takes endpoint out of startup.
        '''
        if new_anchor:
            with self._lock:
                self.offset_anchor = new_anchor

                # switch out now functions here because its possible for the connection to fail and an anchor
                # not be recieved. callback is called ONLY if there is a valid anchor.
                if new_anchor and (self.now == self._now_startup):
                    self.now = self._now

    def easy_setup(self, interval:int=300):
        '''
        Creates an NTPUpdater and subscribes the endpoint to it

        interval: seconds between each sync
        '''
        updater = NTPUpdater(interval)
        updater.link_endpoint(self)
        updater.run_threaded()

class Unadjusted(Simple):
    '''
    Endpoint that gives unadjusted time for reference
    '''
    def _now(self):
        '''
        Returns float containing current, corrected time in seconds
        '''
        return time.time_ns()*(1e-9)

class LastError(Simple):
    '''
    Starts as SimpleEndpoint, but logs the error after each interval. Assumes subsequent 
    intervals will be off by this amount and adjust accordingly.
    '''
    def __init__(self):
        super().__init__()
        self.slew_coefficient = 1
        self.startup = True

    def _now(self):
        '''
        Returns float containing current, corrected time in seconds
        '''
        with self._lock:
            offset_anchor = self.offset_anchor
            slew_coefficient = self.slew_coefficient

        perf_delta = (time.perf_counter_ns() - offset_anchor.perf_ref)*slew_coefficient
        return (offset_anchor.time_ref + perf_delta)*1e-9 + offset_anchor.offset

    def link_to_updater(self, updater:NTPUpdater):
        '''
        Links the endpoint to an NTPUpdater. Not strictly necessary, but allows the endpoint 
        to inherit things like interval if they are needed for certain now() calculations.
        '''
        with self._lock:
            self.interval = updater.interval
            self.interval_accumulator = self.interval
    
    def callback(self, new_anchor:OffsetAnchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally.
        Also stores previous offset for calculations. If NTP sync fails, keeps track of how many 
        intervals have passed to maintain accurate calculation.
        '''
        if new_anchor:
            self.interval_accumulator = self.interval

            if not self.startup:
                with self._lock:
                    old_anchor = self.offset_anchor
                old_perf_delta = time.perf_counter_ns() - old_anchor.perf_ref
                old_unadjusted_now = (old_anchor.time_ref + old_perf_delta)*1e-9 + old_anchor.offset # unadjusted - does not use slew coefficient.

                new_perf_delta = time.perf_counter_ns() - new_anchor.perf_ref
                true_now = (new_anchor.time_ref + new_perf_delta)*1e-9 + new_anchor.offset
                # to be multiplied to the perf_delta
                new_slew = 1 + ((true_now - old_unadjusted_now)/self.interval_accumulator) # seconds per second
            else:
                new_slew = 1
                self.startup = False

            with self._lock:
                self.offset_anchor = new_anchor
                self.slew_coefficient = new_slew
                if self.now == self._now_startup:
                    self.now = self._now

        else:
            self.interval_accumulator += self.interval


if __name__ == '__main__':
    testpoint = Simple()
    updater = NTPUpdater(interval=5)
    updater.link_endpoint(testpoint) # TODO: change name of link_to_endpoint so its obvious its a private method
    updater.run_threaded()

    while True:
        time.sleep(2)
        print(testpoint.now())