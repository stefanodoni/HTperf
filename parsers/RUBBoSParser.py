from parsers.Parser import Parser
import pandas as pd

__author__ = 'francesco'

class RUBBoSParser (Parser):
    columns = [Parser.TIMESTAMP_STR, 'Run', 'Node', 'Clients',
               'Xavg', 'Ravg', 'UtilCpu', 'TotClients',
               'XavgTot', 'RavgTot', 'UavgTot', 'DemandCpu']

    def parse(self, file):
        csvfile = open(file, 'rb')
        dataframe = pd.read_csv(csvfile, sep=';', header=None, skiprows=1,
                                names=self.columns, decimal='.', index_col=False,
                                parse_dates=[0], na_values='NaN')

        #print(dataframe.dtypes)
        #print(dataframe.index.values)

        csvfile.close()
        return dataframe