from parsers.Parser import Parser
import pandas as pd
import numpy as np


class StatsGenerator:
    # The normalize_perf parameter is needed to correctly compute the number of perf metrics accordingly to the measurement interval
    def extract(self, table, DBconn, startTS, endTS, normalize_perf=False):
        mydf = pd.DataFrame(startTS)
        mydf.loc[:, endTS.name] = endTS # Add new column

        # The returned dataset is a dictionary containing the following fields:
        #   - mean: Pandas DataFrame, contains the mean of all PCs
        #   - std: Pandas DataFrame, contains the stdev of all PCs
        #   - max: Pandas DataFrame, contains the max element of all PCs
        result = {}
        result['mean'] = mydf.copy()
        result['std'] = mydf.copy()
        result['max'] = mydf.copy()

        # Get column names from DB
        df = pd.read_sql_query("SELECT * "
                              "FROM " + table + " "
                              "LIMIT 1", DBconn)
        df.drop(['index', Parser.TIMESTAMP_STR], axis=1, inplace=True)
        mycolumns = df.columns

        # Compute the measurement interval
        if normalize_perf:
            df = pd.read_sql_query("SELECT * "
                              "FROM " + table + " "
                              "LIMIT 2", DBconn)
            firstTs = pd.datetime.strptime(df[Parser.TIMESTAMP_STR][0], '%Y-%m-%d %H:%M:%S.%f')
            secondTs = pd.datetime.strptime(df[Parser.TIMESTAMP_STR][1], '%Y-%m-%d %H:%M:%S.%f')
            interval = int((secondTs - firstTs).seconds)


        # Empty DataFrame just to have columns names
        tmp_mean = pd.DataFrame(columns=mycolumns)
        tmp_std = pd.DataFrame(columns=mycolumns)
        tmp_max = pd.DataFrame(columns=mycolumns)

        for start, end in zip(startTS, endTS):
            # Extract dataframe
            df = pd.read_sql_query("SELECT * "
                                   "FROM " + table + " "
                                                     "WHERE " + Parser.TIMESTAMP_STR + " >= '" + str(start) + "' " +
                                   "AND " + Parser.TIMESTAMP_STR + " <= '" + str(end) + "' ", DBconn)

            df.drop(['index', Parser.TIMESTAMP_STR], axis=1, inplace=True) # Remove first two cols, unused in stats

            # Replace negative values with NaN, for statistical purpose
            df[df < 0] = np.nan

            if len(df) > 0: # Query returned more than zero rows
                # Divide all values by the perf measurement interval
                if normalize_perf:
                    df = df.div(interval)

                # Calculate mean of columns
                mean = df.mean().reset_index().T
                mean.columns = mycolumns

                tmp_mean = tmp_mean.append(mean[1:])

                # Calculate std of columns
                std = df.std().reset_index().T
                std.columns = mycolumns

                tmp_std = tmp_std.append(std[1:])

                # Calculate max of columns
                max = df.max().reset_index().T
                max.columns = mycolumns

                tmp_max = tmp_max.append(max[1:])
            else:
                # Set all dataframes to zero
                mean = pd.DataFrame(data=np.zeros((0,len(mycolumns))), columns=mycolumns)
                tmp_mean = tmp_mean.append(mean)

                std = pd.DataFrame(data=np.zeros((0,len(mycolumns))),columns=mycolumns)
                tmp_std = tmp_std.append(std)

                max = pd.DataFrame(data=np.zeros((0,len(mycolumns))),columns=mycolumns)
                tmp_max = tmp_max.append(max)

        # Move index as column and drop it in order to have default integer index
        tmp_mean.reset_index(inplace=True)
        tmp_mean.drop(['index'], axis=1, inplace=True)

        result['mean'] = pd.concat([result['mean'], tmp_mean], axis=1)

        tmp_std.reset_index(inplace=True)
        tmp_std.drop(['index'], axis=1, inplace=True)

        result['std'] = pd.concat([result['std'], tmp_std], axis=1)

        tmp_max.reset_index(inplace=True)
        tmp_max.drop(['index'], axis=1, inplace=True)

        result['max'] = pd.concat([result['max'], tmp_max], axis=1)

        return result