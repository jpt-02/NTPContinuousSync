'''
Contains functions for using NTP to get offset ( might change later)
'''

# Imports

import ntplib
import asyncio
import threading
import inspect
from timeanchor import TimeAnchor, OffsetAnchor
import functools
import time

# Class

class NTPUpdater:
    '''
    Gets relevant NTP sync information at every specified time interval
    '''
    def __init__(self,
                 interval:int=300,
                 tolerance:int=1000000):
        '''
        interval: time interval in seconds between each NTP sync
        tolerance: allowable system clock drift across the duration of the function that 
            queries NTP servers for best offset # TODO: find optimal default value
        '''
        self.interval = interval
        self.tolerance = tolerance
        self._subscribers = [] # functions that are run every time there is a new offset

    @staticmethod
    def verify_drift(func):
        '''
        Decorator to verify that the system time has not drifted during the duration of
        a function. Calls function again if it has drifted.
        '''
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                while True:
                    anchor_1 = TimeAnchor()
                    result = await func(self, *args, **kwargs)
                    anchor_2 = TimeAnchor()
                    if not anchor_1.has_drifted(anchor_2, self.tolerance):
                        return result
                    print(f'Drift out of tolerance, re-running function {func.__name__}.')
                    await asyncio.sleep(0.1)
            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                while True:
                    anchor_1 = TimeAnchor()
                    result = func(self, *args, **kwargs)
                    anchor_2 = TimeAnchor()
                    if not anchor_1.has_drifted(anchor_2, self.tolerance):
                        return result
                    print(f'Drift out of tolerance, re-running function {func.__name__}.')
                    time.sleep(0.1)
            return sync_wrapper
    
    def subscribe(self,callback:function):
        '''
        callback: function to be called every time there is a new offset
        '''
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    async def _query_server(self, server:str, client):
        '''
        Attempts NTP sync with a single server
        server: string containing the name of an NTP server
        client: ntplib.NTPClient object

        Returns: {'offset': offset in seconds, 'delay': delay in seconds, 'server': server name string)
        '''
        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(None, lambda: client.request(server, version=4, timeout=1.5))
            return {'offset': response.offset, 'delay': response.delay, 'server': server}
        except Exception as e:
            #print(f'Server {server} Critical Error: {e}')
            return None

    @verify_drift # make sure system doesnt NTP sync mid-way through this function
    async def get_best_offset(self):
        '''
        Queries multiple NTP servers and returns the offset from the 
        server with the lowest network delay (latency).

        Returns OffsetAnchor object, with attribute offset (seconds) to 
        be added to current time.
        '''
        servers = [
            "time.google.com", 
            "time.cloudflare.com", 
            "time.apple.com",
            "us.pool.ntp.org",
            "time.nist.gov",
            "pool.ntp.org",
            "time.windows.com"
        ]
        
        client = ntplib.NTPClient()
        best_sample = None

        tasks = [self._query_server(server,client) for server in servers]
        results = await asyncio.gather(*tasks) # get sync from each server
        valid_results = [result for result in results if result is not None]
        
        if not valid_results:
            print("Failed to sync with any NTP servers.")
            return None # return None if no servers responded
        
        best_sample = min(valid_results, key=lambda result: result['delay'])

        print(f"Best Source: {best_sample['server']} (Delay: {best_sample['delay']*1000:.2f}ms)")

        new_offset = best_sample['offset']
        new_offset_anchor = OffsetAnchor(offset=new_offset)
        return new_offset_anchor
    
    async def update_offset(self):
        '''
        Updates the offset and initates subscribed callbacks
        '''
        new_offset_anchor = await self.get_best_offset()
        if new_offset_anchor is not None:
            print(f'New Offset is {new_offset_anchor.offset}')
            for callback in self._subscribers:
                try:
                    # callback can be async or regular
                    if inspect.iscoroutinefunction(callback):
                        await callback(new_offset_anchor) # TODO: add support for more args I think
                    else:
                        callback(new_offset_anchor)
                except Exception as e:
                    print(f'Callback Error: {e}')

    async def _worker(self):
        '''
        Starts the loop to update offset once every interval
        '''
        while True:
            await self.update_offset()
            await asyncio.sleep(self.interval)

    def run_async(self):
        '''
        Runs the updater using asyncio - blocking
        (not recommended for fast reponse times)
        '''
        asyncio.run(self._worker())

    def run_threaded(self):
        '''
        Runs the updater using threads - not blocking
        (Recommended for fast response)
        '''
        syncthread = threading.Thread(
            target=lambda: asyncio.run(self._worker()), # necessary because worker is async
            daemon=True
            )
        syncthread.start()

# TODO: Make clean shutdown for async and threads

if __name__ == '__main__':
    updater = NTPUpdater(5)
    updater.run_threaded()