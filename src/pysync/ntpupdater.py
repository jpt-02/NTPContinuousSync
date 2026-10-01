'''
Contains functions for using NTP to get offset ( might change later)
'''

# Imports

import ntplib
import asyncio
import threading
import inspect
from pysync.anchors import TimeAnchor, OffsetAnchor
import functools
import time

# Classes

class NTPUpdater:
    '''
    Gets relevant NTP sync information at every specified time interval
    '''
    def __init__(self,
                 interval:int=300,
                 tolerance:int=1000000,
                 optimization_flag:int=0):
        '''
        interval: time interval in seconds between each NTP sync
        tolerance: allowable system clock drift across the duration of the function that 
            queries NTP servers for best offset # TODO: find optimal default value
            # TODO: specify units
        optimization_flag:
            0 - pure python implementation
            1 - C++ implementation, but otherwise same as python
            2 - C++ implementation, auto-calculates time once every 1 ms and stores it in l1 cache
        # TODO: if opt flag is 2, start the cpp clock.
        # TODO: possibly add option to have offset anchor pre-converted to ms, us, or ns
        # TODO: make it so that if opt2, can only use subscribe before running. Maybe make it so its always like this.
        '''
        self.interval = interval
        self.tolerance = tolerance
        self.optimization_flag = optimization_flag # TODO: propagate this to anchors
        self._linked_endpoints = [] # linked endpoints that are updated every time there is a new offset
        self._linked_endpoint_callbacks = [] # functions that are run every time there is a new offset
        self._loop = None # the active event loop for getting an update each interval

        if self.optimization_flag == 2:
            pass # TODO: call cpp to start l1 clock

    def link_endpoint(self,endpoint):
        '''
        Links the NTPUpdater to an endpoint. When there is a new offset from the NTPUpdater, 
        the link allows a callback in the endpoint to be called, updating the info.
        Also shares other info, like interval.

        Endpoint: any public class in the pyendpoints.py file # TODO: change file name if necessary
        '''
        if self._loop is None or not self._loop.is_running():
            if endpoint not in self._linked_endpoints:
                self._linked_endpoints.append(endpoint)
                endpoint._link_to_updater(self)
        else:
            print('link_endpoint() method: NTPUpdater is running so endpoint cannot be linked') # TODO: test this

    def run_async(self):
        '''
        Runs the updater using asyncio - blocking
        (not recommended for fast reponse times)
        '''
        if self._loop is None or not self._loop.is_running():
            asyncio.run(self._worker()) # TODO: make sure this works
        else:
            print('run_async() method: NTPUpdater is already running')

    def run_threaded(self):
        '''
        Runs the updater using threads - not blocking
        (Recommended for fast response)
        '''
        if self._loop is None or not self._loop.is_running():
            syncthread = threading.Thread(
                target=lambda: asyncio.run(self._worker()), # necessary because worker is async
                daemon=True
                )
            syncthread.start()
        else:
            print('run_threaded() method: NTPUpdater is already running')

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
        Returns None if all connections fail.
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
        new_offset_anchor = OffsetAnchor(offset=new_offset) # TODO: change behavior based on opt flag
        return new_offset_anchor
    
    async def _update_offset(self):
        '''
        Updates the offset and initates subscribed callbacks
        Callbacks are called with None as argument if NTP sync fails. Endpoints handle this.
        '''
        new_offset_anchor = await self.get_best_offset()

        if new_offset_anchor is not None:
            print(f'New Offset is {new_offset_anchor.offset}')
        else:
            print('NTP Sync Failed, callbacks called with None')

        for endpoint in self._linked_endpoints:
            callback = endpoint.callback # TODO: this should work but test it out 
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
        self._loop = asyncio.get_running_loop()
        while True:
            await self._update_offset()
            await asyncio.sleep(self.interval)

    # TODO: Make clean shutdown for async and threads


class NTPUpdater_debug(NTPUpdater):
    '''
    Subclass of NTPUpdater with dedicated features for debugging and testing

    Features:
        - Force Update: Allows for an NTP update to be called via a method instead of waiting for the interval
        - Emulate Connection Loss: Deliberately emulates a lost connection to induce a failure state
    '''
    def __init__(self,
                interval:int=300,
                tolerance:int=1000000,
                optimization_flag:int=0):
        '''
        interval: time interval in seconds between each NTP sync
        tolerance: allowable system clock drift across the duration of the function that 
            queries NTP servers for best offset # TODO: find optimal default value
        optimization_flag:
            0 - pure python implementation
            1 - C++ implementation, but otherwise same as python
            2 - C++ implementation, auto-calculates time once every 1 ms and stores it in l1 cache
        '''
        super().__init__(interval, tolerance, optimization_flag)
        self._current_iteration = 0
        self._iteration_to_fail = None
    
    def force_update(self):
        '''
        Forces the NTPUpdater to get a new offset, regardless of where it is
        in the interval.

        WARNING: This can break the logic of endpoints that calculate time based on 
                interval (LastError).

        returns Future (only if running)
            if function call is followed by future.result(), this blocks until 
            the update finishes. Completely optional.
        '''
        if self._loop is None or not self._loop.is_running():
            print('force_update() method: failed, NTPUpdater not currently running')
            return None
        
        future = asyncio.run_coroutine_threadsafe(
            self._update_offset(), self._loop
        )
        return future
    
    def emulate_connection_loss(self, iteration:int):
        '''
        Emulates a lost connection for a predetermined NTP sync (returns None instead of an offset anchor).
        Used for testing purposes. Must be invoked before the updater is started.

        iteration: 0-indexed number indicating which sync to deliberately fail
        '''
        if self._loop is None or not self._loop.is_running():
            self._iteration_to_fail = iteration
        else:
            print('emulate_connection_loss() method: failed, NTPUpdater is already running')

    async def _update_offset(self):
        '''
        Updates the offset and initates subscribed callbacks
        Callbacks are called with None as argument if NTP sync fails. Endpoints handle this.
        Redefined here to include emulate_connection_loss compatibility 
        '''
        iteration = self._current_iteration
        
        if (self._iteration_to_fail is not None) and (iteration == self._iteration_to_fail):
            print(f"[EMULATION] Simulating network connection loss for iteration {iteration}")
            new_offset_anchor = None
        else:
            new_offset_anchor = await self.get_best_offset()

        if new_offset_anchor is not None:
            print(f'New Offset is {new_offset_anchor.offset}')
        else:
            print('NTP Sync Failed, callbacks called with None')

        for endpoint in self._linked_endpoints:
            callback = endpoint.callback # TODO: this should work but test it out 
            try:
                # callback can be async or regular
                if inspect.iscoroutinefunction(callback):
                    await callback(new_offset_anchor) # TODO: add support for more args I think
                else:
                    callback(new_offset_anchor)
            except Exception as e:
                print(f'Callback Error: {e}')

        self._current_iteration += 1



if __name__ == '__main__':
    updater = NTPUpdater(5)
    updater.run_threaded()