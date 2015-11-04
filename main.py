import sys
import argparse
import sqlite3
import sqlalchemy as sqlal
import pandas as pd
import numpy as np
from database import DBConstants
from datasets.RUBBoSDataset import RUBBoSDataset
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

sar_file = args.dir + "/sar-client0.csv"
pcm_file = args.dir + "/pcm.csv"
rubbos_detailed_file = args.dir + "/rubbos-detailed.csv"
rubbos_file = args.dir + "/rubbos.csv"
perf_file = args.dir + "/perf.csv"

# ======================= DATA IMPORT =============================
rubbos_detailed_dataframe = RUBBoSParser().parse(rubbos_detailed_file, "detailed")

rubbos_dataframe = RUBBoSParser().parse(rubbos_file)

sar_dataframe = SarParser().parse(sar_file)
#sar_dataframe = SarParser().select_dataframe_interval_by_timestap(sar_dataframe, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

pcm_dataframe = PCMParser().parse(pcm_file)
#pcm_dataframe2 = PCMParser().select_dataframe_interval_by_timestap(pcm_dataframe, '2015-10-11 02:44:00', '2015-10-11 02:46:15')

perf_dataframe = PerfParser().parse(perf_file)

# ======================= PERSIST DATA IN SQLITE ====================
conn = sqlite3.connect(DBConstants.DB_NAME)
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS " + DBConstants.RUBBOS_DETAILED_TABLE)
c.execute("DROP TABLE IF EXISTS " + DBConstants.RUBBOS_TABLE)
c.execute("DROP TABLE IF EXISTS " + DBConstants.SAR_TABLE)
c.execute("DROP TABLE IF EXISTS " + DBConstants.PCM_TABLE)
c.execute("DROP TABLE IF EXISTS " + DBConstants.PERF_TABLE)

rubbos_detailed_dataframe.to_sql(DBConstants.RUBBOS_DETAILED_TABLE, conn)
rubbos_dataframe.to_sql(DBConstants.RUBBOS_TABLE, conn)
sar_dataframe.to_sql(DBConstants.SAR_TABLE, conn)
pcm_dataframe.to_sql(DBConstants.PCM_TABLE, conn)
perf_dataframe.to_sql(DBConstants.PERF_TABLE, conn)

conn.commit()

# Query to show table fields: PRAGMA table_info(tablename)

# for row in c.execute("SELECT * FROM pcm"):
#     print(row)

# c.execute("SELECT * FROM prova")
# print(c.fetchone())

#print(pd.read_sql_query("SELECT * FROM " + DBConstants.RUBBOS_TABLE, conn))
#print(pd.read_sql_query("SELECT * FROM rubbos WHERE \"Timestamp Start\" < \"2015-10-11 08:14:18\"", conn))

# c.execute("DROP TABLE IF EXISTS prova")
# c.execute("CREATE TABLE prova (c1, c2, asd TEXT)")
# c.execute("INSERT INTO prova VALUES (5,3,4)")

rubbos_dataset = RUBBoSDataset().create(rubbos_dataframe, conn)

conn.close()

# Alternative to sqlite3: SQLAlchemy in order to use pd.read_sql_table
#engine = sqlal.create_engine('sqlite:///htperf.db')
#print(pd.read_sql_table('rubbos', engine))
#print(pd.read_sql_query("SELECT * FROM rubbos WHERE \"Timestamp Start\" <= \"2015-10-11 08:14:18\"", engine))



# ======================= STATISTICS =====================================
LinearRegression().print_diag("IPC", "X", rubbos_dataset)
#RANSACRegressor().print_diag("rubbos", "rubbos", rubbos_dataframe, rubbos_dataframe)









