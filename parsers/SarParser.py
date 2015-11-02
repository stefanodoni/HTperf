import pandas as pd
from parsers.Parser import Parser

__author__ = 'francesco'

class SarParser (Parser):
    columns = ['Host', 'Interval', Parser.TIMESTAMP_STR,
               'CPU', 'User', 'Nice', 'System',
               'Iowait', 'Steal', 'Idle']

    #def __init__(self):
        #Parser.__init__(self)
        #print("init sarParser")

    def parse(self, file):
        csvfile = open(file, 'rb')
        dataframe = pd.read_csv(csvfile, sep=';', header=None, names=self.columns,
                                decimal=',', index_col=False,
                                parse_dates=[2]) #DataFrame obj

        #dataframe.columns = self.columns
        #dataframe['Timestamp'] = dataframe['Timestamp'].apply(pd.to_datetime)
        #print(dataframe.dtypes)
        #print(dataframe.index.values)

        csvfile.close()
        return dataframe