import sys
from parsers.SarParser import SarParser
from parsers.PCMParser import PCMParser
from parsers.RUBBoSParser import RUBBoSParser
from statistics.LinearRegression import LinearRegression

__author__ = 'francesco'

if len(sys.argv) < 4:
    print("Need csv file params!")
    sys.exit()

sar_file = sys.argv[1]
pcm_file = sys.argv[2]
rubbos_file = sys.argv[3]

sar_dataframe1 = SarParser().parse(sar_file)
#LinearRegression().print_diag(sar_dataframe1)

sar_dataframe2 = SarParser().select_dataframe_interval_by_timestap(sar_dataframe1, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

pcm_dataframe1 = PCMParser().parse(pcm_file)
pcm_dataframe2 = PCMParser().select_dataframe_interval_by_timestap(pcm_dataframe1, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

rubbos_dataframe = RUBBoSParser().parse(rubbos_file)

print(rubbos_dataframe)