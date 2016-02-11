from database import DBConstants
from datasets.HTDataset import HTDataset
from parsers.Parser import Parser
from statistics.StatsGenerator import StatsGenerator
import pandas as pd

__author__ = 'francesco'

class LiveReportDataset (HTDataset):
    def create(self, DBconn, startTS, endTS):
        mydataset = {}
        start_ts_series = pd.Series(startTS, name=Parser.TIMESTAMP_START_STR)
        end_ts_series = pd.Series(endTS, name=Parser.TIMESTAMP_END_STR)

        mydataset['perf-stats'] = StatsGenerator().extract(DBConstants.PERF_TABLE, DBconn,
                                                           start_ts_series,
                                                           end_ts_series,
                                                           True)

        mydataset['sar-stats'] = StatsGenerator().extract(DBConstants.SAR_TABLE, DBconn,
                                                           start_ts_series,
                                                           end_ts_series)

        return mydataset