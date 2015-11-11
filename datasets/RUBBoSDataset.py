from database import DBConstants
from datasets.HTDataset import HTDataset
from parsers.Parser import Parser
from statistics.StatsGenerator import StatsGenerator

__author__ = 'francesco'

class RUBBoSDataset (HTDataset):
    def create(self, dataframe, DBconn):

        # The returned dataset is a dictionary that contains the following fields:
        #   - runs: Pandas DataFrame, contains the RUBBoS report of each run
        #   - pcm-stats: Dictionary of Pandas DataFrame, contains the mean, stdev and max of PCM PCs
        #   - perf-stats: Dictionary of Pandas DataFrame, contains the mean, stdev and max of Perf PCs
        mydataset = {}
        mydataset['runs'] = dataframe.copy()

        # Extract and aggregate PCM data and Perf data for each run
        mydataset['pcm-stats'] = StatsGenerator().extract(DBConstants.PCM_TABLE, DBconn,
                                                          dataframe[Parser.TIMESTAMP_START_STR],
                                                          dataframe[Parser.TIMESTAMP_END_STR])


        mydataset['perf-stats'] = StatsGenerator().extract(DBConstants.PERF_TABLE, DBconn,
                                                           dataframe[Parser.TIMESTAMP_START_STR],
                                                           dataframe[Parser.TIMESTAMP_END_STR])
        # Print csv reports
        for i in mydataset['pcm-stats']:
            mydataset['pcm-stats'][i].to_csv('pcm-' + i + '.csv', sep=';')

        for i in mydataset['perf-stats']:
            mydataset['perf-stats'][i].to_csv('perf-' + i + '.csv', sep=';')

        return mydataset