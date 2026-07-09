'''
Contains TimeAnchor and OffsetData classes
'''

# Imports

import time
import numpy as np

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
    def __init__(self, window:int):
        '''
        Initiates a TimeAnchor object
        window: nanoseconds, acceptable window for references to be acquired
                    (see more in get_simultaneous_references)
        '''
        self.window = window
        self.time_ref, self.perf_ref = self._get_constrained_references() # time at initialization in nanoseconds, perf counter reference in nanoseconds
    
    def _get_constrained_references(self):
        '''
        Time reference and perf reference ideally are from the exact same nanosecond,
        but how close they are actually called to one another is up to the OS. This 
        function loops repeatedly and takes the references from the smallest window.
        On my machine, this is typically 100ns.

        Returns: tuple of ints (time_ref, perf_ref)
        '''
        acquisition_list = []
        for _ in range(10): # on my machine, range of 4 is sufficient to get it down to 100 ns
            acquisition_list.append(self._get_simultaneous_references())
        
        data = np.array(acquisition_list)
        deltas = data[:,2] - data[:,0] # p2-p1

        min_idx = np.argmin(deltas)
        
        #min_window = np.min(deltas) TODO: have this propagate through program to be stored for max error reference
        #print(min_window)

        time_ref = data[min_idx, 1]
        perf_ref = (data[min_idx, 2] + data[min_idx, 0])//2

        return time_ref, perf_ref

    def _get_simultaneous_references(self):
        '''
        Gets time references for use in _get_constrained_references. Made as a 
        separate function so it can be easily replaced by an optimized c++ function 
        later on if desired.

        Returns: p1 (perf counter in ns), time_ref (current system time in ns), p2 (perf counter in ns)
        '''
        p1 = time.perf_counter_ns()
        time_ref = time.time_ns()
        p2 = time.perf_counter_ns()

        return p1, time_ref, p2

    def has_drifted(self, other_anchor:TimeAnchor, tolerance:int):
        '''
        Determines if system time has drifted for any reason between two anchors
        other_anchor: TimeAnchor object to be compared to
        tolerance: allowable drift in nanoseconds

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
    def __init__(self, window:int, offset:float):
        '''
        Initiates an OffsetAnchor object
        window: nanoseconds, acceptable window for references to be acquired
        offset: NTP offset in seconds
        '''
        super().__init__(window=window)
        self.offset = offset


if __name__ == '__main__':
    for i in range(1):
        anchor = TimeAnchor(1000)