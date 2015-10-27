from parsers.Parser import Parser
import pandas as pd
import dateutil.parser as dparser
import datetime as dt

__author__ = 'francesco'

class PerfParser (Parser):
    columns = [Parser.TIMESTAMP_STR, 'CPU', 'Value', 'Blank', 'Event']

    def parse(self, file):
        csvfile = open(file, 'rb')

        datetime = pd.read_csv(csvfile, nrows=1, index_col=False, header=None)[0].values
        datetime = dparser.parse(datetime[0],fuzzy=True) # Gets the datetime from the perf file first row
        csvfile.seek(0) # Brings file pointer back to file start

        dataframe = pd.read_csv(csvfile, sep=';', header=None, skiprows=2,
                                names=self.columns, decimal='.', index_col=False,
                                parse_dates=[0],
                                date_parser = lambda x: datetime + dt.timedelta(seconds=float(x)),
                                na_values='NaN')

        csvfile.close()
        return dataframe