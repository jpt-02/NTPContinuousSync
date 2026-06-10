import time
import ntplib
from socket import gaierror, timeout
import threading
import logging

logger = logging.getLogger(__name__)

class SyncClock:
    def __init__(self,interval=300):
        self.interval = interval
        self.offset = 0.0
        self.skew = 0.0
        self.skewrate = 0.0
        self.system_time_reference = time.time_ns()/(10**9)
        self.perf_reference = time.perf_counter() # perf counter starting point

        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.startup = True
        self.thread.start()
    
    def get_best_offset(self):
        """
        Queries multiple NTP servers and returns the offset from the 
        server with the lowest network delay (latency).
        """
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

        for server in servers:
            try:
                # We use version 3 for maximum compatibility
                response = client.request(server, version=3, timeout=1.5)
                # The 'delay' is the round-trip time. 
                # We want the lowest delay because it has the smallest error bound.
                if best_sample is None or response.delay < best_sample['delay']:
                    best_sample = {
                        'server': server,
                        'offset': response.offset,
                        'delay': response.delay
                    }
                    
            except (ntplib.NTPException, gaierror, timeout):
                continue # Skip servers that are down or timing out

        if best_sample:
            print(f"Best Source: {best_sample['server']} (Delay: {best_sample['delay']*1000:.2f}ms)")
            best_offset = best_sample['offset']
        else:
            print("Failed to reach any NTP servers.")
            best_offset = None
        
        return best_offset, time.time_ns()/(10**9)
        
    def update_time_reference(self):
        new_offset, new_system_time_reference = self.get_best_offset()

        with self._lock:
            if new_offset:
                old_now = self.now()
                new_now = new_system_time_reference + new_offset

                self.skew = new_now - old_now # Difference between pre and post NTP sync times
                self.skewrate = self.skew/self.interval # Seconds to change per second

                if self.startup:
                    self.skew = 0
                    self.skewrate = 0
                    self.startup = False

                # Update Old Variables
                self.offset = new_offset
                self.system_time_reference = new_system_time_reference
                self.perf_reference = time.perf_counter()

                print(f'Offset is {self.offset*1000}ms')

                # for testing
                #self.newtarget = new_now + self.interval

    def _worker(self):
        self.update_time_reference() # initial on startup

        while True:
            try:
                time.sleep(self.interval)

                # for testing
                #errorval = self.now() - self.newtarget
                #print(f'Error of {errorval} at end of Sync interval')

                self.update_time_reference()
            except Exception as e:
                print(f"Critical error in Timer Thread: {e}")
                time.sleep(10) # wait before retrying
    
    def _print_error(self):
        errorval = self.now() - self.now_no_skew()
        print(f'Error of {errorval}')
    
    def now_no_skew(self):
        elapsed = time.perf_counter() - self.perf_reference
        return self.system_time_reference + self.offset + elapsed
        
    def now(self):
        elapsed = time.perf_counter() - self.perf_reference
        return self.system_time_reference + self.offset + elapsed - self.skew + (elapsed*self.skewrate)

    
if __name__ == '__main__':
    timer = SyncClock(10)
    while True:
        time.sleep(1)
        timer._print_error()
    