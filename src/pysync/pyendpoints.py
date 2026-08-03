'''
Contains python endpoints for more precise times.
'''

# Imports

from anchors import OffsetAnchor
from ntpupdater import NTPUpdater
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
    def __init__(self, push):
        '''
        push: function to be called upon NTP sync, intended to store 
            ground truth time and call now() from other endpoints to 
            compare
        '''
        self._lock = threading.Lock()
        self.offset_anchor = OffsetAnchor(offset=0)
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


class _NowEngine:
    '''
    Defines now() for each endpoint and each optimization
    '''
    def get_specialized_functions(self, type:str, optimization_flag:int):
        '''
        type:
            simple - Adds latest offset to current time
            unadjusted - Uses unadjusted system time (for reference)
            lasterror - SimpleEndpoint, but remembers the error at the end of each interval and assumes
                        subsequent intervals will be off by the same error. Adjusts to compensate.
        optimization_flag:
            0 - pure python implementation
            1 - C++ implementation, but otherwise same as python
            2 - C++ implementation, auto-calculates time once every 1 ms and stores it in l1 cache

        Returns (new function for now(), new function for secondary_callback())
        '''
        dispatch_table = {
            ('simple',0) : (self._simple_opt0, None),
            ('unadjusted',0) : (self._unadjusted_opt0, None),
            ('lasterror',0) : (self._lasterror_opt0, None)
            # TODO: fill this out as optimizations are made
        }

        tup = (type, optimization_flag)
        if tup not in dispatch_table:
            raise Exception(f'Invalid args for endpoint construction')
        else:
            return dispatch_table[tup]

    @staticmethod
    def _simple_opt0(endpoint):
        with endpoint._lock:
            offset_anchor = endpoint.offset_anchor
        # use local copy to do math
        perf_delta = time.perf_counter_ns() - offset_anchor.perf_ref
        return (offset_anchor.time_ref + perf_delta)*1e-9 + offset_anchor.offset

    @staticmethod
    def _unadjusted_opt0(endpoint):
        pass

    @staticmethod
    def _lasterror_opt0(endpoint):
        pass

    @staticmethod
    def _simple_otp1(endpoint):
        pass

    @staticmethod
    def _simple_opt1_callback(endpoint):
        pass

    @staticmethod
    def _unadjusted_otp1(endpoint):
        pass

    @staticmethod
    def _unadjusted_opt1_callback(endpoint):
        pass

    @staticmethod
    def _lasterror_otp1(endpoint):
        pass

    @staticmethod
    def _lasterror_opt1_callback(endpoint):
        pass

    @staticmethod
    def _simple_otp2(endpoint):
        pass

    @staticmethod
    def _simple_opt2_callback(endpoint):
        pass

    @staticmethod
    def _unadjusted_otp2(endpoint):
        pass

    @staticmethod
    def _unadjusted_opt2_callback(endpoint):
        pass

    @staticmethod
    def _lasterror_otp2(endpoint):
        pass

    @staticmethod
    def _lasterror_opt2_callback(endpoint):
        pass

    






class Endpoint:
    def __init__(self, type, optimization_flag:int=0):
        '''
        type:
            simple - Adds latest offset to current time
            unadjusted - Uses unadjusted system time (for reference)
            lasterror - SimpleEndpoint, but remembers the error at the end of each interval and assumes
                        subsequent intervals will be off by the same error. Adjusts to compensate.
        optimization_flag:
            0 - pure python implementation
            1 - C++ implementation, but otherwise same as python
            2 - C++ implementation, auto-calculates time once every 1 ms and stores it in l1 cache
        '''
        self._type = type
        self._optimization_flag = optimization_flag
        self._lock = threading.Lock()
        self._now_engine = _NowEngine()
        self.now = self._now_startup # returns unadjusted system time, prevents crash before first sync
        self.secondary_callback = self._secondary_callback_startup

        # placeholders for calculations - not strictly necessary
        self.offset_anchor = None # inherited after first sucessful sync
        self.interval = None # inherited from NTPUpdater after linking

    def link_to_updater(self, updater:NTPUpdater):
        '''
        Links the endpoint to an NTPUpdater. Not strictly necessary, but allows the endpoint 
        to inherit things like interval if they are needed for certain now() calculations.
        '''
        with self._lock:
            self.interval = updater.interval
            self._optimization_flag = updater.optimization_flag
            future = updater.force_update() # force the NTPUpdater to give a time anchor
            if future is not None: # this happens if the NTPUpdater isnt running
                future.result() # block until the anchor is recieved (not strictly necessary)         
    
    def _now_startup(self):
        '''
        Placeholder for before the link to updater
        '''
        print('Warning: No offset used.') # TODO: make this more detailed
        return time.time_ns()*(1e-9)
    
    def _secondary_callback_startup(self):
        '''
        Placeholder for before the link to updater
        '''
        pass
    
    def callback(self, offset_anchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally.
        '''
        with self._lock:
            self.offset_anchor = offset_anchor
            self.secondary_callback() # used for c++ optimizations, does nothing otherwise
            # TODO: make sure args work above
            
            # switch out now functions here because its possible for the connection to fail and an anchor
            # not be recieved after the link forces an update
            if self.now == self._now_startup:
                new_now, new_secondary_callback = self._now_engine.get_specialized_functions(self._type, self._optimization_flag)
                # bind it to this instance so endpoint.now() calls it directly without dispatch overhead
                self.now = lambda: new_now(self)
                if new_secondary_callback: # some optimizations dont use this so its just None
                    self.secondary_callback = lambda: new_secondary_callback(self)

    def easy_setup(self, interval:int=300):
        '''
        Creates an NTPUpdater and subscribes the endpoint to it

        interval: seconds between each sync
        '''
        updater = NTPUpdater(interval)
        updater.link_endpoint(self)
        updater.run_threaded()



class SimpleEndpoint:
    '''
    An endpoint for corrected time that adds the latest offset to 
    whatever the current time is.
    '''
    def __init__(self):
        self._lock = threading.Lock()
        self.offset_anchor = OffsetAnchor(offset=0)

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
        '''
        updater = NTPUpdater(interval)
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
    
    def easy_setup(self):
        '''
        Creates an NTPUpdater and subscribes the endpoint to it

        interval: seconds between each sync
        '''
        updater = NTPUpdater(interval=self.interval)
        updater.subscribe(self.callback)
        updater.run_threaded()
        
        

if __name__ == '__main__':
    
    # endpoint = SimpleEndpoint()
    # updater = NTPUpdater(interval=5)
    # updater.subscribe(endpoint.callback)
    # updater.run_threaded()
    # #endpoint.easy_setup(interval=5)

    endpoint = Endpoint('simple',0)
    endpoint.easy_setup(interval=5) # TODO: see if this works
    # TODO: test subscribing after the NTPupdater is running to make sure force update works



    # run until keyboard interrupt
    while True:
        time.sleep(2)
        print(endpoint.now())
