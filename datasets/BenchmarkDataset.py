from database import DBConstants
from datasets.HTDataset import HTDataset
from parsers.Parser import Parser
from statistics.StatsGenerator import StatsGenerator
import config.SUTConfig as sut


class BenchmarkDataset (HTDataset):
    def create(self, dataframe, DBconn, output_dir, test_name, using_pcm):

        # The returned dataset is a dictionary that contains the following fields:
        #   - runs: Pandas DataFrame, contains the benchmark report of each run
        #   - perf-stats: Dictionary of Pandas DataFrame, contains the mean, stdev and max of Perf data
        #   - sar-stats: Dictionary of Pandas DataFrame, contains the mean, stdev and max of Sar data
        #   - (optional) pcm-stats: Dictionary of Pandas DataFrame, contains the mean, stdev and max of PCM PCs
        mydataset = {}
        mydataset['runs'] = dataframe.copy()

        # Extract and aggregate PCM data and Perf data for each run
        if using_pcm:
            mydataset['pcm-stats'] = StatsGenerator().extract(DBConstants.PCM_TABLE, DBconn,
                                                            dataframe[Parser.TIMESTAMP_START_STR],
                                                            dataframe[Parser.TIMESTAMP_END_STR])


        mydataset['perf-stats'] = StatsGenerator().extract(DBConstants.PERF_TABLE, DBconn,
                                                           dataframe[Parser.TIMESTAMP_START_STR],
                                                           dataframe[Parser.TIMESTAMP_END_STR],
                                                           True)

        mydataset['sar-stats'] = StatsGenerator().extract(DBConstants.SAR_TABLE, DBconn,
                                                           dataframe[Parser.TIMESTAMP_START_STR],
                                                           dataframe[Parser.TIMESTAMP_END_STR])
        # Print csv reports
        if using_pcm:
            for i in mydataset['pcm-stats']:
                mydataset['pcm-stats'][i].to_csv(output_dir + test_name + '/pcm-' + i + '.csv', sep=';')

        for i in mydataset['perf-stats']:
            mydataset['perf-stats'][i].to_csv(output_dir + test_name + '/perf-' + i + '.csv', sep=';')

        for i in mydataset['sar-stats']:
            mydataset['sar-stats'][i].to_csv(output_dir + test_name + '/sar-' + i + '.csv', sep=';')

        return mydataset