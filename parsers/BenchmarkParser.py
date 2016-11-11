from parsers.Parser import Parser
import pandas as pd


class BenchmarkParser (Parser):
    columns = [Parser.TIMESTAMP_START_STR, Parser.TIMESTAMP_END_STR, 'Run', 'TotClients',
               'XavgTot', 'RavgTot', 'UavgTot', 'DemandCpu']

    columns_detailed = [Parser.TIMESTAMP_START_STR, Parser.TIMESTAMP_END_STR, 'Run', 'Node', 'Clients',
                        'Xavg', 'Ravg', 'UtilCpu', 'TotClients',
                        'XavgTot', 'RavgTot', 'UavgTot', 'DemandCpu']

    # Pass type = detailed if parsing a detailed benchmark report file
    def parse(self, file, type=None):
        csvfile = open(file, 'rb')
        dataframe = pd.read_csv(csvfile, sep=';', header=None, skiprows=1,
                                names=(self.columns_detailed if type == "detailed" else self.columns), decimal='.', index_col=False,
                                parse_dates=[0,1], na_values='NaN')

        #print(dataframe.dtypes)
        #print(dataframe.index.values)

        csvfile.close()
        return dataframe