'''
Used for testing the accuracy of endpoints and saving/plotting data
'''

# Imports

import endpoints
from endpoints import TruthEndpoint
import inspect
from ntpfunctions import NTPUpdater
import queue
import time
import pandas as pd

# Helper Function

def get_all_endpoints():
    '''
    Used to initiate an EndpointTester object with one of each endpoint

    Returns dict {name:str : endpoint object}
    '''
    returndict = {}
    all_classes = inspect.getmembers(endpoints, inspect.isclass)
    for name, class_ in all_classes:
        # only keep classes that are from endpoints and not TruthEndpoint
        if (class_.__module__ == endpoints.__name__) and (name != 'TruthEndpoint'):
            returndict[name] = class_()
    return returndict

# Class

class EndpointTester:
    '''
    Used to test endpoints. Has a single TruthEndpoint as a point of reference.
    When TruthEndpoint gets a sync, it pushes the current true time to the tester.
    Tester calls now() for all other endpoints, bundles results together, and adds 
    to a queue. Queue is periodically emptied by the tester.
    '''
    def __init__(self, 
                 truth_interval:int, 
                 test_interval:int, 
                 test_time:int,
                 endpoint_dict:list[(str,object)],
                 save_path:str = 'testdata.csv'):
        '''
        truth_interval: seconds between each true time point
        test_interval: seconds between each NTP sync for endpoints
            being tested
        test_time: total time for the test to run
        endpoint_dict: dict {name:str : endpoint object} to be tested
        save_path: path to save data to (must end in .csv)
        '''
        self.queue = queue.Queue()
        self.truth_interval = truth_interval
        self.test_time = test_time
        self.save_path = save_path

        self.endpoint_dict = endpoint_dict
        # loop through and alter any keys that are 'TruthEndpoint' just in case anyone doubles it

        self.raw_data = [] # list of data points {name:str : time:float}
        self.series_error_data = {} # dict of series error data {name:str : [error:float, ...]}
        # initiate lists for each endpoint (besides TruthEndpoint)
        for name in endpoint_dict:
            self.series_error_data[name] = []

        # create truth updater and truth endpoint
        self.truth_updater = NTPUpdater(truth_interval)
        self.truth_endpoint = TruthEndpoint(self.push_reciever)
        self.truth_updater.subscribe(self.truth_endpoint.callback)

        # create test updater and add all other endpoints to it
        self.test_updater = NTPUpdater(test_interval)
        for endpoint in endpoint_dict.values():
            self.test_updater.subscribe(endpoint.callback)

        # start test before truth so sync is done before push is called
        self.test_updater.run_threaded()
        self.truth_updater.run_threaded()

        self.run_test()

    def push_reciever(self, true_time:float):
        '''
        Bundles true time with now() from each endpoint and adds it to the queue

        true_time: Time right after TruthEndpoint finishes a sync

        Appends dict {name:str : time:float}
        '''
        datalist = [] # use a list first because its faster
        for endpoint in self.endpoint_dict.values():
            datalist.append(endpoint.now())

        # now make into dictionary
        data_point = dict(zip(self.endpoint_dict.keys(),datalist))
        data_point['TruthEndpoint'] = true_time

        self.queue.put(data_point)
        
    def run_test(self):
        '''
        Starts a loop that empties the queue and terminates once the test time
        has elapsed.
        '''
        start_perf = time.perf_counter()

        try: # use try to handle keyboard interrupt message
            while True:
                # check time
                if (time.perf_counter() - start_perf) > self.test_time:
                    print(f'Test finished after {self.test_time} seconds.')
                    break
                
                try:
                    data_point = self.queue.get(block=True, timeout=1.0)
                except queue.Empty:
                    # In combination with timeout=1.0, this allows the thread to check 
                    # for keyboard interrupts once a second. Without timeout it would 
                    # never cause an exception.
                    continue

                # save raw data
                self.raw_data.append(data_point)
                # save series data
                true_time = data_point['TruthEndpoint']
                for name, time_ in  data_point.items():
                    if name != 'TruthEndpoint':
                        error = time_ - true_time
                        self.series_error_data[name].append(error)

                self.queue.task_done()

        except KeyboardInterrupt:
            print('Test interrupted via KeyboardInterrupt')

        self.save_data()
                    
    def save_data(self):
        '''
        Formats data into time series and saves to .csv
        '''
        data_range = len(next(iter(self.series_error_data.values())))
        iteration_list = list(range(data_range))
        approx_runtime_list = [(iteration_list[i]-1)*self.truth_interval for i in iteration_list]

        self.series_error_data['iteration'] = iteration_list
        self.series_error_data['approx_runtime'] = approx_runtime_list

        df = pd.DataFrame(self.series_error_data)
        metadata_cols = ['iteration', 'approx_runtime'] # make it so metadata is on the left
        endpoint_cols = [col for col in df.columns if col not in metadata_cols]
        df = df[metadata_cols + endpoint_cols]

        df.to_csv(self.save_path, index=False)



if __name__ == '__main__':
    #all_targets = get_all_endpoints()
    all_targets = {
        'Simple': endpoints.SimpleEndpoint(),
        'Unadjusted': endpoints.UnadjustedEndpoint(),
        'UseLastError': endpoints.UseLastErrorEndpoint(900)
    }
    tester = EndpointTester(30,900,14400,all_targets)
    #tester = EndpointTester(1,3,30,all_targets)

