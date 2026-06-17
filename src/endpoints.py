'''
Contains python endpoints for more precise times.
'''

# Imports

from ntpfunctions import NTPUpdater
from timeanchor import OffsetAnchor
import asyncio
import time
import threading

class SimpleEndpoint:
    '''
    An endpoint for corrected time that adds the latest offset to 
    whatever the current time is.
    '''
    def __init__(self, interval:int=300):
        '''
        interval: time interval in seconds between each NTP sync
        '''
        self._lock = threading.Lock()
        
        updater = NTPUpdater(interval)
        updater.subscribe(self.callback)
        syncthread = threading.Thread(
            target=lambda: asyncio.run(updater.worker()), # necessary because worker is async
            daemon=True
            )
        syncthread.start()

        self.offset_anchor = OffsetAnchor(0)

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
    


if __name__ == '__main__':
    endpoint = SimpleEndpoint(interval=5)

    # run until keyboard interrupt
    while True:
        time.sleep(2)
        print(endpoint.now())
