'''
Easy setup for NTPUpdaters and Endpoints. Automatically makes an NTP Updater and endpoint with the same 
optimization level.
'''

# Imports

import time
from pysync.ntpupdater import NTPUpdater
import pysync.endpoints.opt0 as opt0
import pysync.endpoints.opt1 as opt1
import pysync.endpoints.opt2 as opt2

# Class

class QuickStart:
    '''
    Initiates an NTPUpdater and an Endpoint, links the two, and starts the updater in its own thread. 
    To get the adjusted time, call the now() method.
    '''
    def __init__(self, type:str='lasterror', interval:int=300, optimization_flag:int=0):
        '''
        type:
            simple - Adds latest offset to current time
            unadjusted - Uses unadjusted system time (for reference)
            lasterror - SimpleEndpoint, but remembers the error at the end of each interval and assumes
                        subsequent intervals will be off by the same error. Adjusts to compensate.
        interval: time interval in seconds between each NTP sync
        optimization_flag:
            0 - pure python implementation
            1 - C++ implementation, but otherwise same as python
            2 - C++ implementation, auto-calculates time once every 1 ms and stores it in l1 cache
        '''
        dispatch_table = {
                ('simple',0) : opt0.Simple,
                ('unadjusted',0) : opt0.Unadjusted,
                ('lasterror',0) : opt0.LastError
                # TODO: fill this out as optimizations are made
            }

        if not any(t==type for t,o in dispatch_table):
            raise Exception(f"Invalid argument '{type}' for type")
        
        if not any(o==optimization_flag for t,o in dispatch_table):
            raise Exception(f"Invalid argument '{optimization_flag}' for optimization flag")
        
        self.endpoint = dispatch_table[(type,optimization_flag)]()
        self.updater = NTPUpdater(interval=interval, optimization_flag=optimization_flag)
        self.updater.link_endpoint(self.endpoint)
        self.updater.run_threaded()
        time.sleep(0.5) # give updater time to get first sync. Not necessary to prevent crash, can be removed if you want.

    def now(self):
        return self.endpoint.now()


if __name__ == '__main__':
    quickstart = QuickStart()
    while True:
        print(quickstart.now())
        time.sleep(2)