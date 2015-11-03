import pandas as pd

__author__ = 'francesco'

class Parser:
    TIMESTAMP_STR = "Timestamp"
    TIMESTAMP_START_STR = "TimestampStart"
    TIMESTAMP_END_STR = "TimestampEnd"

    #def __init__(self):
        #print("init parser")

    def hello(self):
        print("sono Parser")
        #print("{} sono figlio").format(valore)

    # Timestamp string format: YYYY-MM-DD hh:mm:ss
    def select_dataframe_interval_by_timestap(self, dataframe, start_ts, end_ts):
        dataframe.set_index(self.TIMESTAMP_STR, inplace=True)
        dataframe.sort_index()
        return dataframe.loc[pd.to_datetime(start_ts) : pd.to_datetime(end_ts)]