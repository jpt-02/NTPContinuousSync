'''
Used for testing the accuracy of endpoints and saving/plotting data
'''

# Imports

import endpoints
from endpoints import TruthEndpoint
import inspect
from ntpfunctions import NTPUpdater

# Helper Function

def get_all_endpoints():
    '''
    Used to initiate an EndpointTester object with one of each endpoint

    Returns list of tuples (name:str, endpoint object)
    '''
    returnlist = []
    all_classes = inspect.getmembers(endpoints, inspect.isclass)
    for name, obj in all_classes:
        # only keep classes that are from endpoints and not TruthEndpoint
        if (obj.__module__ == endpoints.__name__) and (name != 'TruthEndpoint'):
            returnlist.append((name,obj()))
    return returnlist


# Class

class EndpointTester:
    '''
    
    '''
    def __init__(self, 
                 truth_interval:int, 
                 test_interval:int, 
                 interval_limit:int,
                 endpoint_list:list[(str,object)]):
        '''
        truth_interval: seconds between each true time point
        test_interval: seconds between each NTP sync for endpoints
            being tested
        interval_limit: time limit for the entire test, in terms of how
            many test_interval to elapse before shuting down.
        endpoint_list: list of tuples (name:str, endpoint object) to be tested
        '''
        self.endpoint_list = endpoint_list

        self.truth_updater = NTPUpdater(truth_interval)
        self.truth_endpoint = TruthEndpoint(self.push_reciever)
        self.truth_updater.subscribe(self.truth_endpoint.callback)

        self.test_updater = NTPUpdater(test_interval)
        for endpoint in endpoint_list:
            self.test_updater.subscribe(endpoint.callback)

        #self.truth_updater.run_threaded()
        #self.test_updater.run_threaded() # switch these

        self.run_test()

    def push_reciever(self, true_time):
        pass

    def run_test(self):
        pass

    def save_data(self):
        # maybe use one of the real-time plotters like streamlit 
        pass




if __name__ == '__main__':
    tester = EndpointTester(5,300,10)
