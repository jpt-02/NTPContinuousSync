'''
Contains python endpoints for more precise times.
'''

# Imports

from ntpfunctions import NTPUpdater
import asyncio
import time

class SimpleEndpoint:
    '''
    An endpoint for corrected time that adds the latest offset to 
    whatever the current time is.
    '''
    def __init__(self, interval:int=300):
        '''
        interval: time interval in seconds between each NTP sync
        '''
        updater = NTPUpdater(interval)
        updater.subscribe(self.callback)
        asyncio.run(updater.start())

        self.offset_anchor = None

    def callback(self, offset_anchor):
        '''
        Callback for each sync.
        Stores the offset_anchor object locally.
        '''
        self.offset_anchor = offset_anchor

    def now(self):
        '''
        Returns float containing current, corrected time in seconds
        '''
        perf_delta = time.perf_counter_ns() - self.offset_anchor.perf_ref
        return (time.time_ns() + perf_delta)*10**-9 + self.offset_anchor.offset
    


if __name__ == '__main__':
    endpoint = SimpleEndpoint()
    print('ok')
    time.sleep(2)
    print(endpoint.now())
