from database import DBConstants
from parsers.Parser import Parser
import pandas as pd
import numpy as np
import sys


class LiveStatsGenerator:
    # The normalize_perf parameter is needed to correctly compute the number of perf metrics accordingly to the measurement interval
    def extract(self, table, DBconn, startTS, endTS, user_interval, normalize_perf=False):
        # Get column names from DB
        # Compute the measurement interval
        df = pd.read_sql_query("SELECT * "
                          "FROM " + table + " "
                          "LIMIT 2", DBconn)

        if table == DBConstants.SAR_TABLE:
            firstTs = pd.datetime.strptime(df[Parser.TIMESTAMP_STR][0], '%Y-%m-%d %H:%M:%S')
            secondTs = pd.datetime.strptime(df[Parser.TIMESTAMP_STR][1], '%Y-%m-%d %H:%M:%S')
            interval = int((secondTs - firstTs).seconds)
            if interval > int(user_interval): # Exit if the measurement interval is greater than the user interval
                print("Warning: SAR measurement interval (" + str(interval) + " seconds) is greater than requested sampling interval (" + str(user_interval) + " seconds). Increase interval argument.")
                sys.exit()
        elif table == DBConstants.PERF_TABLE:
            firstTs = pd.datetime.strptime(df[Parser.TIMESTAMP_STR][0], '%Y-%m-%d %H:%M:%S.%f')
            secondTs = pd.datetime.strptime(df[Parser.TIMESTAMP_STR][1], '%Y-%m-%d %H:%M:%S.%f')
            interval = int((secondTs - firstTs).seconds)
            if interval > int(user_interval): # Exit if the measurement interval is greater than the user interval
                print("Warning: PERF measurement interval (" + str(interval) + " seconds) is greater than requested sampling interval (" + str(user_interval) + " seconds). Increase interval argument.")
                sys.exit()

        df.drop(['index', Parser.TIMESTAMP_STR], axis=1, inplace=True)
        mycolumns = df.columns

        for start, end in zip(startTS, endTS):
            # Extract dataframe
            df = pd.read_sql_query("SELECT * "
                                    "FROM " + table + " "
                                    "WHERE " + Parser.TIMESTAMP_STR + " >= '" + str(start) + "' " +
                                        "AND " + Parser.TIMESTAMP_STR + " <= '" + str(end) + "' ", DBconn)
            df.drop(['index'], axis=1, inplace=True) # Remove first two cols, unused in stats

            # Replace negative values with NaN, for statistical purpose, exclude timestamp column
            if table == DBConstants.PERF_TABLE:
                df[df.iloc[:, 1:] < 0] = np.nan

            if len(df) > 0: # We extracted collected data
                # Divide all values by the perf measurement interval
                if normalize_perf:
                    df.iloc[:, 1:] = df.iloc[:, 1:].div(interval)
            else: # No data was collected during this interval
                zeros = pd.DataFrame(data=np.zeros((0,len(mycolumns))), columns=mycolumns)
                df = df.append(zeros)

            # Rename Sar column timestamp
            if table == DBConstants.SAR_TABLE:
                df.rename(columns = {Parser.TIMESTAMP_STR: Parser.TIMESTAMP_START_STR}, inplace = True)

        return df