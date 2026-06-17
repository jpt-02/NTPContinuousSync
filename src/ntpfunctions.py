'''
Contains functions for using NTP to get offset ( might change later)
'''

# Imports

import ntplib
import asyncio
import inspect
from timeanchor import OffsetAnchor
from decorators import verify_drift

# Class

class NTPUpdater:
    '''
    Gets relevant NTP sync information at every specified time interval
    '''
    def __init__(self,interval:int=300):
        '''
        interval: time interval in seconds between each NTP sync
        '''
        self.interval = interval
        self._subscribers = [] # functions that are run every time there is a new offset

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
        new_offset_anchor = OffsetAnchor(new_offset)
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
                        await callback(new_offset_anchor) # add support for more args I think
                    else:
                        callback(new_offset_anchor)
                except Exception as e:
                    print(f'Callback Error: {e}')

    async def worker(self):
        '''
        Starts the loop to update offset once every interval
        '''
        while True:
            await self.update_offset()
            await asyncio.sleep(self.interval)


if __name__ == '__main__':
    updater = NTPUpdater(5)
    asyncio.run(updater.worker())