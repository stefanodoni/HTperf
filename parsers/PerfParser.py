from parsers.Parser import Parser
import pandas as pd
import dateutil.parser as dparser
import datetime as dt


class PerfParser (Parser):
    columns = [Parser.TIMESTAMP_STR, 'HWElem', 'Value', 'Blank', 'Event']

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

        # Pivot the dataframe in order to have columns divided by HW Elements and by Events monitored by perf
        # pivot_table uses a default mean function over the values! Be careful.
        vals = ['Value']
        index = [Parser.TIMESTAMP_STR]
        cols = ['HWElem', 'Event']

        dataframe = pd.pivot_table(dataframe, values=vals, index=index, columns=cols).reset_index()

        # Change dataframe columns names in order to import it into sqlite without complex columns names, i.e. ('Timestamp', '', '')
        # New column name format: HWElement_Event
        old_columns = dataframe.columns.tolist()
        new_columns = ['{}_{}'.format(hw_elem, event) for value, hw_elem, event in old_columns[1:]] # Skip first item ('Timestamp', '', '')
        new_columns.insert(0, Parser.TIMESTAMP_STR)
        dataframe.columns = new_columns

        return dataframe