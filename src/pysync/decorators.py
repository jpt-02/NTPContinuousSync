'''
Contains decorator used for verifying time reference acquisitions
'''

# Imports

import inspect
from timeanchor import TimeAnchor
import functools
import asyncio
import time

# Decorator Definition

def verify_drift(func):
    '''
    Decorator to verify that the system time has not drifted during the duration of
    a function. Calls function again if it has drifted.
    '''
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            while True:
                anchor_1 = TimeAnchor()
                result = await func(*args, **kwargs)
                anchor_2 = TimeAnchor()
                if not anchor_1.has_drifted(anchor_2):
                    return result
                print(f'Drift out of tolerance, re-running function {func.__name__}.')
                await asyncio.sleep(0.1)
        return async_wrapper

    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            while True:
                anchor_1 = TimeAnchor()
                result = func(*args, **kwargs)
                anchor_2 = TimeAnchor()
                if not anchor_1.has_drifted(anchor_2):
                    return result
                print(f'Drift out of tolerance, re-running function {func.__name__}.')
                time.sleep(0.1)
        return sync_wrapper