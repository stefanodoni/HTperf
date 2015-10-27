import sys
from parsers.SarParser import SarParser
from parsers.PCMParser import PCMParser
from parsers.RUBBoSParser import RUBBoSParser
from parsers.PerfParser import PerfParser
from statistics.LinearRegression import LinearRegression
from statistics.RANSACRegressor import RANSACRegressor

__author__ = 'francesco'

if len(sys.argv) < 5:
    print("Need csv file params!")
    sys.exit()

sar_file = sys.argv[1]
pcm_file = sys.argv[2]
rubbos_file = sys.argv[3]
perf_file = sys.argv[4]

sar_dataframe1 = SarParser().parse(sar_file)

sar_dataframe2 = SarParser().select_dataframe_interval_by_timestap(sar_dataframe1, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

pcm_dataframe1 = PCMParser().parse(pcm_file)
pcm_dataframe2 = PCMParser().select_dataframe_interval_by_timestap(pcm_dataframe1, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

rubbos_dataframe = RUBBoSParser().parse(rubbos_file)

perf_dataframe = PerfParser().parse(perf_file)

#LinearRegression().print_diag("rubbos", "rubbos", rubbos_dataframe, rubbos_dataframe)
RANSACRegressor().print_diag("rubbos", "rubbos", rubbos_dataframe, rubbos_dataframe)

#print(rubbos_dataframe)