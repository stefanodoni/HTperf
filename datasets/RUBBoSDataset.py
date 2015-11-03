from database import DBConstants
from datasets.HTDataset import HTDataset
from parsers.Parser import Parser
from parsers.RUBBoSParser import RUBBoSParser
import pandas as pd
import numpy as np

__author__ = 'francesco'

class RUBBoSDataset (HTDataset):
    def create(self, dataframe, DBconn):
        mydataset = []

        # Extract and aggregate PCM data for each run
        for row in dataframe.iterrows(): # Warning: iterrows possibily changes dtype of elements! Use itertuples instead
            run = row[1]

            df = pd.read_sql_query("SELECT * "
                              "FROM " + DBConstants.PCM_TABLE + " "
                              "WHERE " + Parser.TIMESTAMP_STR + " >= '" + str(run[Parser.TIMESTAMP_START_STR]) + "' " +
                              "AND " + Parser.TIMESTAMP_STR + " <= '" + str(run[Parser.TIMESTAMP_END_STR]) + "' ", DBconn)

            df.drop(['index', Parser.TIMESTAMP_STR], axis=1, inplace=True) # Remove first two cols, unused in stats

            # Replace negative values with NaN, for statistical purpose
            # tmp = df._get_numeric_data()
            # tmp[tmp < 0] = np.nan
            # tmp.insert(1, Parser.TIMESTAMP_STR, df[Parser.TIMESTAMP_STR])
            df[df < 0] = np.nan

            # Calculate mean, std and max of columns
            mean = df.mean()
            std = df.std()
            max = df.max()

            break
        return "asd"