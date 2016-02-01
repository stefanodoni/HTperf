#!/usr/bin/python3.4
import os
import argparse
import sqlite3
import sqlalchemy as sqlal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from database import DBConstants
from datasets.RUBBoSDataset import RUBBoSDataset
from graph_plotters.HTModelPlotter import HTModelPlotter
from parsers.SarParser import SarParser
from parsers.PCMParser import PCMParser
from parsers.RUBBoSParser import RUBBoSParser
from parsers.PerfParser import PerfParser
from parsers.SysConfigParser import SysConfigParser
from statistics.HTLinearModel import HTLinearModel
from config.SUTConfig import SUTConfig
import config.BenchmarkAnalysisConfig as bac

__author__ = 'francesco'

parser = argparse.ArgumentParser(description='HTperf tool: parse, aggregate, select and plot data.')
parser.add_argument('benchmarkdirpath', metavar='benchmarkdirpath', help='path to directory containing n benchmark report directories, each one containing the csv report files')
parser.add_argument('reportdirpath', metavar='reportdirpath', help='path to directory in which the tool generates the reports')
parser.add_argument('-pcm', help='indicates if a pcm.csv file must be parsed', dest='pcm', action='store_true')
parser.add_argument('-sysconfig', help='indicates if a sysConfig.csv file must be parsed', dest='sysconfig', action='store_true')
args = parser.parse_args()

# Settings
using_pcm = args.pcm
using_sysconfig = args.sysconfig

# Get the chosen output dir and create it if necessary
OUTPUT_DIR = os.path.join(args.reportdirpath, '')
os.makedirs(os.path.dirname(OUTPUT_DIR), exist_ok=True)

# Set path and file names
path_to_tests = args.benchmarkdirpath

test_names = [name for name in os.listdir(path_to_tests) if not os.path.isfile(path_to_tests + "/" + name)]
test_names.sort()
test_numbers = [i + 1 for i in range(len(test_names))]

# rubbos_detailed_file = "/rubbos-detailed.csv"
rubbos_file = "/rubbos.csv"
sar_file = "/sar-client0.csv"
pcm_file = "/pcm.csv"
perf_file = "/perf.csv"
sysconfig_file = "/sysConfig.csv"

# Create output directory
for test in test_names:
    os.makedirs(os.path.dirname(OUTPUT_DIR + test + '/'), exist_ok=True)

# Data structures
system_config = {}
rubbos_dataframes = {}
sar_dataframes = {}
pcm_dataframes = {}
perf_dataframes = {}

rubbos_datasets = {}

ht_linear_models = {}

# ======================= DATA IMPORT =============================
if using_sysconfig:
    system_config = SysConfigParser().parse(path_to_tests + '/' + sysconfig_file)
    my_sut_config = SUTConfig()
    my_sut_config.set(system_config)
else:
    my_sut_config = SUTConfig()
    my_sut_config.set_manual()

for test in test_names:
    # rubbos_detailed_dataframe = RUBBoSParser().parse(rubbos_detailed_file, "detailed") # Only if using the detailed version of rubbos report file
    rubbos_dataframes[test] = RUBBoSParser().parse(path_to_tests + '/' + test + rubbos_file)
    sar_dataframes[test] = SarParser().parse(path_to_tests + '/' + test + sar_file)
    perf_dataframes[test] = PerfParser().parse(path_to_tests + '/' + test + perf_file)

    if using_pcm:
        pcm_dataframes[test] = PCMParser().parse(path_to_tests + '/' + test + pcm_file)

# ======================= PERSIST DATA IN SQLITE ====================
os.remove(DBConstants.DB_NAME) # Remove DB file and reconstruct it
conn = sqlite3.connect(DBConstants.DB_NAME)
c = conn.cursor()

for test in test_names:
    #rubbos_detailed_dataframe.to_sql(DBConstants.RUBBOS_DETAILED_TABLE, conn)
    rubbos_dataframes[test].to_sql(DBConstants.RUBBOS_TABLE, conn, if_exists='append')
    sar_dataframes[test].to_sql(DBConstants.SAR_TABLE, conn, if_exists='append')
    perf_dataframes[test].to_sql(DBConstants.PERF_TABLE, conn, if_exists='append')

    if using_pcm:
        pcm_dataframes[test].to_sql(DBConstants.PCM_TABLE, conn, if_exists='append')

conn.commit()

# c.execute("DROP TABLE IF EXISTS " + DBConstants.RUBBOS_DETAILED_TABLE)

# Query to show table fields: PRAGMA table_info(tablename)
# for row in c.execute("PRAGMA table_info(perf)"):
#     print(row)

# for row in c.execute("SELECT * FROM " + DBConstants.PERF_TABLE):
#     print(row)

# c.execute("SELECT * FROM prova")
# print(c.fetchone())

#print(pd.read_sql_query("SELECT * FROM " + DBConstants.RUBBOS_TABLE, conn))
#print(pd.read_sql_query("SELECT * FROM rubbos WHERE \"Timestamp Start\" < \"2015-10-11 08:14:18\"", conn))

# c.execute("DROP TABLE IF EXISTS prova")
# c.execute("CREATE TABLE prova (c1, c2, asd TEXT)")
# c.execute("INSERT INTO prova VALUES (5,3,4)")

for test in test_names:
    rubbos_datasets[test] = RUBBoSDataset().create(rubbos_dataframes[test], conn, OUTPUT_DIR, test, using_pcm)

conn.close()

# Alternative to sqlite3: SQLAlchemy in order to use pd.read_sql_table
#engine = sqlal.create_engine('sqlite:///htperf.db')
#print(pd.read_sql_table('rubbos', engine))
#print(pd.read_sql_query("SELECT * FROM rubbos WHERE \"Timestamp Start\" <= \"2015-10-11 08:14:18\"", engine))

# ======================= STATISTICS =====================================
for test in test_names:
    ht_linear_models[test] = HTLinearModel().estimate(rubbos_datasets[test], OUTPUT_DIR, test, my_sut_config)

# ======================= PLOT GRAPHS =====================================
plotter = HTModelPlotter().init(OUTPUT_DIR)

# cmap = plt.get_cmap('gnuplot')
# colors = [cmap(i) for i in np.linspace(0, 1, len(test_numbers))]

# First plot scatter and standard points in order to determinate the maximum X value
# for test, num, color in zip(test_names, test_numbers, colors):
for test, num in zip(test_names, test_numbers):
    plotter.plot_scatter(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 0, 0, 'blue', str(num) + ') C0 Productivity', True)
    plotter.plot_scatter(rubbos_datasets[test]['runs']['XavgTot'], rubbos_datasets[test]['runs']['UavgTot'], 0, 0, 'green', str(num) + ') Tot Avg Utilization (Benchmark)')
    plotter.plot_scatter(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_cbt, 0, 0, 'black', str(num) + ') Tot Avg Core Busy Time (C0 state)', True)
    plotter.plot_scatter(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0, 'purple', str(num) + ') Tot Avg Utilization (Sar)')
    plotter.plot_scatter(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_atd, 1, 0, 'violet', str(num) + ') Tot Avg Thread Density')
    plotter.plot_scatter(rubbos_datasets[test]['runs']['XavgTot'], rubbos_datasets[test]['runs']['RavgTot'], 0, 1, 'red', str(num) + ') Tot Avg Response Time')

# Then use the x_max value to print the lr lines
# for test, num, color in zip(test_names, test_numbers, colors):
for test, num in zip(test_names, test_numbers):
    plotter.plot_lin_regr(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 0, 0, 'blue', str(num) + ') C0 Productivity LR', True)
    plotter.plot_lin_regr(rubbos_datasets[test]['runs']['XavgTot'], rubbos_datasets[test]['runs']['UavgTot'], 0, 0, 'green', str(num) + ') Tot Avg Utilization (Benchmark) LR')
    plotter.plot_lin_regr(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_cbt, 0, 0, 'black', str(num) + ') Tot Avg Core Busy Time (C0 state) LR', True)
    plotter.plot_lin_regr(rubbos_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0, 'purple', str(num) + ') Tot Avg Utilization (Sar) LR')

title = ''
for test, num in zip(test_names, test_numbers):
    title = title + str(num) + ') ' + test + ('\n' if num != test_numbers[-1] else '')

plotter.gen_graph(title + '\nLinear Regressions considering first ' + str(bac.NUM_SAMPLES) + ' samples',
                  'Throughput', 'Utilization', 'Response Time', 'Tot Avg Thread Density')

