'''
Contains TimeAnchor and OffsetData classes
'''

# Imports

import time

# Classes

class TimeAnchor:
    '''
    Stores a time (system clock) and perftime (monotonic clock) reference.
    This is used so that it can be compared to other TimeAnchor objects to 
    determine if a system-wide NTP Sync occurred while the rest of the 
    program is calculating offset or other variables that are used to 
    calculate a more accurate time.

    Example of error this avoids:
    1. Program gets offset from NTP servers with respect to current system clock
    2. Windows/Linux syncs system clock with NTP server automatically
    3. Program calculates corrected time by adding offset to system time, but 
        because system time is now different, this gives an incorrect time.
    '''
    def __init__(self, window:int = 1000):
        '''
        Initiates a TimeAnchor object
        window: nanoseconds, acceptable window for references to be acquired
                    (see more in get_simultaneous_references)
        '''
        self.window = window
        references = self._get_simultaneous_references()
        self.time_ref = references[0] # time at initialization in nanoseconds
        self.perf_ref = references[1] # perf counter reference in nanoseconds

    def _get_simultaneous_references(self):
        '''
        Time reference and perf reference ideally are from the exact same nanosecond,
        but how close they are actually called to one another is up to the OS. This 
        function loops until it gets two references within a certain time window.
        On my machine, a window of 1000 ns has a roughly 90% success rate.

        Returns: tuple (time_ref, perf_ref)
        '''
        while True:
            p1 = time.perf_counter_ns()
            time_ref = time.time_ns()
            p2 = time.perf_counter_ns()

            if (p2-p1) < self.window:
                #print('Sucess')
                perf_ref = (p1+p2)//2
                return (time_ref, perf_ref)
            #print('Failure')
                
    
    def has_drifted(self, other_anchor:TimeAnchor, tolerance:int=1000000):
        '''
        Determines if system time has drifted for any reason between two anchors
        other_anchor: TimeAnchor object to be compared to
        tolerance: allowable drift in nanoseconds (default is 10^6 ns, or one ms)

        Returns True or False
        '''
        if not isinstance(other_anchor, TimeAnchor):
            raise TypeError('Can only compare drift between two TimeAnchor objects')
        
        time_ref_delta = abs(self.time_ref - other_anchor.time_ref)
        perf_ref_delta = abs(self.perf_ref - other_anchor.perf_ref)

        return abs(time_ref_delta-perf_ref_delta) > tolerance


class OffsetAnchor(TimeAnchor):
    '''
    Stores TimeAnchor data along with its corresponding NTP offset
    MUST be initiated in a function decorated by verify_drift
    '''
    def __init__(self,offset:float):
        '''
        Initiates an OffsetAnchor object
        offset: NTP offset in seconds
        '''
        super().__init__()
        self.offset = offset


if __name__ == '__main__':
    for i in range(10):
        anchor = TimeAnchor()