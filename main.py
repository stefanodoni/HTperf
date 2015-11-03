import sys
import argparse
import sqlite3
import sqlalchemy as sqlal
import pandas as pd
from parsers.Parser import Parser
from parsers.SarParser import SarParser
from parsers.PCMParser import PCMParser
from parsers.RUBBoSParser import RUBBoSParser
from parsers.PerfParser import PerfParser
from statistics.LinearRegression import LinearRegression
from statistics.RANSACRegressor import RANSACRegressor

__author__ = 'francesco'

parser = argparse.ArgumentParser(description='HTperf tool: parse, aggregate, select and plot data.')
parser.add_argument('dir', metavar='dir', help='directory containing all csv report files')
args = parser.parse_args()

sar_file = args.dir + "/sar.csv"
pcm_file = args.dir + "/pcm.csv"
rubbos_file = args.dir + "/rubbos.csv"
rubbos_global_file = args.dir + "/rubbos-global.csv"
perf_file = args.dir + "/perf.csv"

# ======================= DATA IMPORT =============================
rubbos_dataframe = RUBBoSParser().parse(rubbos_file)

rubbos_global_dataframe = RUBBoSParser().parse(rubbos_global_file, "global")

sar_dataframe = SarParser().parse(sar_file)
#sar_dataframe = SarParser().select_dataframe_interval_by_timestap(sar_dataframe, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

pcm_dataframe = PCMParser().parse(pcm_file)
#pcm_dataframe2 = PCMParser().select_dataframe_interval_by_timestap(pcm_dataframe, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

perf_dataframe = PerfParser().parse(perf_file)

# ======================= PERSIST DATA IN SQLITE ====================
conn = sqlite3.connect('htperf.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS rubbos")
c.execute("DROP TABLE IF EXISTS rubbos_global")
c.execute("DROP TABLE IF EXISTS sar")
c.execute("DROP TABLE IF EXISTS pcm")
c.execute("DROP TABLE IF EXISTS perf")

rubbos_dataframe.to_sql('rubbos', conn)
rubbos_global_dataframe.to_sql('rubbos_global', conn)
sar_dataframe.to_sql('sar', conn)
pcm_dataframe.to_sql('pcm', conn)
perf_dataframe.to_sql('perf', conn)

conn.commit()

# Query to show table fields: PRAGMA table_info(tablename)

# for row in c.execute("SELECT * FROM pcm"):
#     print(row)

# c.execute("SELECT * FROM prova")
# print(c.fetchone())

print(pd.read_sql_query("SELECT * FROM rubbos_global", conn))
#print(pd.read_sql_query("SELECT * FROM rubbos WHERE \"Timestamp Start\" < \"2015-10-11 08:14:18\"", conn))

# c.execute("DROP TABLE IF EXISTS prova")
# c.execute("CREATE TABLE prova (c1, c2, asd TEXT)")
# c.execute("INSERT INTO prova VALUES (5,3,4)")

conn.close()

# Alternative to sqlite3: SQLAlchemy in order to use pd.read_sql_table
#engine = sqlal.create_engine('sqlite:///htperf.db')
#print(pd.read_sql_table('rubbos', engine))
#print(pd.read_sql_query("SELECT * FROM rubbos WHERE \"Timestamp Start\" <= \"2015-10-11 08:14:18\"", engine))



# ======================= STATISTICS =====================================
#LinearRegression().print_diag("rubbos", "rubbos", rubbos_dataframe, rubbos_dataframe)
#RANSACRegressor().print_diag("rubbos", "rubbos", rubbos_dataframe, rubbos_dataframe)









