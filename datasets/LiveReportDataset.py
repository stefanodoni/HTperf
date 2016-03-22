from database import DBConstants
from datasets.HTDataset import HTDataset
from parsers.Parser import Parser
from statistics.LiveStatsGenerator import LiveStatsGenerator
import pandas as pd

__author__ = 'francesco'

class LiveReportDataset (HTDataset):
    def create(self, DBconn, startTS, endTS, user_interval):
        mydataset = {}
        start_ts_series = pd.Series(startTS, name=Parser.TIMESTAMP_START_STR)
        end_ts_series = pd.Series(endTS, name=Parser.TIMESTAMP_END_STR)

        mydataset['perf-stats'] = LiveStatsGenerator().extract(DBConstants.PERF_TABLE, DBconn,
                                                           start_ts_series,
                                                           end_ts_series,
                                                           user_interval,
                                                           True)

        mydataset['sar-stats'] = LiveStatsGenerator().extract(DBConstants.SAR_TABLE, DBconn,
                                                           start_ts_series,
                                                           end_ts_series,
                                                           user_interval)

        return mydataset