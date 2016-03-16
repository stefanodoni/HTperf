#!/usr/bin/python3.4
import os
import argparse
import sqlite3
import sqlalchemy as sqlal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from database import DBConstants
from datasets.BenchmarkDataset import BenchmarkDataset
from graph_plotters.HTModelPlotter import HTModelPlotter
from parsers.SarParser import SarParser
from parsers.PCMParser import PCMParser
from parsers.BenchmarkParser import BenchmarkParser
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

# benchmark_detailed_file = "/benchmark-detailed.csv"
benchmark_file = "/benchmark.csv"
sar_file = "/sar.csv"
pcm_file = "/pcm.csv"
perf_file = "/perf.csv"
sysconfig_file = "/sysConfig.csv"

# Create output directory
for test in test_names:
    os.makedirs(os.path.dirname(OUTPUT_DIR + test + '/'), exist_ok=True)

# Create DB file and empty it
open(DBConstants.DB_NAME, 'w').close()

# Data structures
system_config = {}
benchmark_dataframes = {}
sar_dataframes = {}
pcm_dataframes = {}
perf_dataframes = {}

benchmark_datasets = {}

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
    # benchmark_detailed_dataframe = BenchmarkParser().parse(benchmark_detailed_file, "detailed") # Only if using the detailed version of benchmark report file
    benchmark_dataframes[test] = BenchmarkParser().parse(path_to_tests + '/' + test + benchmark_file)
    sar_dataframes[test] = SarParser().parse(path_to_tests + '/' + test + sar_file)
    perf_dataframes[test] = PerfParser().parse(path_to_tests + '/' + test + perf_file)

    if using_pcm:
        pcm_dataframes[test] = PCMParser().parse(path_to_tests + '/' + test + pcm_file)

# ======================= PERSIST DATA IN SQLITE ====================
conn = sqlite3.connect(DBConstants.DB_NAME)
c = conn.cursor()

for test in test_names:
    #benchmark_detailed_dataframe.to_sql(DBConstants.BENCHMARK_DETAILED_TABLE, conn)
    benchmark_dataframes[test].to_sql(DBConstants.BENCHMARK_TABLE, conn, if_exists='append')
    sar_dataframes[test].to_sql(DBConstants.SAR_TABLE, conn, if_exists='append')
    perf_dataframes[test].to_sql(DBConstants.PERF_TABLE, conn, if_exists='append')

    if using_pcm:
        pcm_dataframes[test].to_sql(DBConstants.PCM_TABLE, conn, if_exists='append')

conn.commit()

# c.execute("DROP TABLE IF EXISTS " + DBConstants.BENCHMARK_DETAILED_TABLE)

# Query to show table fields: PRAGMA table_info(tablename)
# for row in c.execute("PRAGMA table_info(perf)"):
#     print(row)

# for row in c.execute("SELECT * FROM " + DBConstants.PERF_TABLE):
#     print(row)

# c.execute("SELECT * FROM prova")
# print(c.fetchone())

#print(pd.read_sql_query("SELECT * FROM " + DBConstants.BENCHMARK_TABLE, conn))
#print(pd.read_sql_query("SELECT * FROM benchmark WHERE \"Timestamp Start\" < \"2015-10-11 08:14:18\"", conn))

# c.execute("DROP TABLE IF EXISTS prova")
# c.execute("CREATE TABLE prova (c1, c2, asd TEXT)")
# c.execute("INSERT INTO prova VALUES (5,3,4)")

for test in test_names:
    benchmark_datasets[test] = BenchmarkDataset().create(benchmark_dataframes[test], conn, OUTPUT_DIR, test, using_pcm)

conn.close()

# Alternative to sqlite3: SQLAlchemy in order to use pd.read_sql_table
#engine = sqlal.create_engine('sqlite:///htperf.db')
#print(pd.read_sql_table('benchmark', engine))
#print(pd.read_sql_query("SELECT * FROM benchmark WHERE \"Timestamp Start\" <= \"2015-10-11 08:14:18\"", engine))

# ======================= STATISTICS =====================================
for test in test_names:
    ht_linear_models[test] = HTLinearModel().estimate(benchmark_datasets[test], OUTPUT_DIR, test, my_sut_config)

# ======================= PLOT GRAPHS =====================================
# colors = ['#E12727', '#504FAF', '#088DA5', '#FE9900', '#12AD2A'] #281D46
colors = ['#0041CC', '#FF0000', '#E6C700', '#FF00BF', '#00CC22']

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0, color, (None if len(test_names) > 1 else "Utilizzo Tradizionale"), False, False, 0, 100)

# Then use the x_max value to print the lr lines
for test, color in zip(test_names, colors):
    color = (colors[1] if len(test_names) == 1 else color)
    plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0, color, (test if len(test_names) > 1 else "Utilization Law"), False, False, 0, 100)

plotter.gen_graph("U-vs-X", "Stima dell'Utilizzo Tradizionale (" + str(bac.NUM_SAMPLES) + " campioni)" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'System Throughput'}, {0: 'Utilizzo Tradizionale'}, None, None, True)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 1, 0, color, (None if len(test_names) > 1 else "Productivity"), False, True, 0, 100)

# Then use the x_max value to print the lr lines
for test, color in zip(test_names, colors):
    color = (colors[1] if len(test_names) == 1 else color)
    plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 1, 0, color, (test if len(test_names) > 1 else "Regressione Lineare"), False, True, 0, 100)

plotter.gen_graph("P-vs-X", "Stima della Productivity (" + str(bac.NUM_SAMPLES) + " campioni)" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'System Throughput'}, {0: 'Productivity'}, None, None, True)

# plotter = HTModelPlotter().init(OUTPUT_DIR, 2)
# # First plot scatter and standard points in order to determinate the maximum X value
# for test, color in zip(test_names, colors):
#     plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], benchmark_datasets[test]['runs']['RavgTot'], 0, 0, color, test + '\nTot Avg Response Time (ms)')
#     plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_atd, 1, 0, color, test + '\nTot Avg Thread Density', False, False, 1, 2)
#
# plotter.gen_graph("R,atd-vs-X", bac.TITLE, {0: 'System Throughput', 1: 'System Throughput'}, {0: 'Tot Avg Response Time (ms)', 1: 'Tot Avg Thread Density'})

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_atd, 0, 0, color, (test if len(test_names) > 1 else "Average Thread Density"), False, False, 1, 2)

plotter.gen_graph("Atd-vs-X", "Andamento dell'Average Thread Density" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'System Throughput'}, {0: 'Average Thread Density'}, None, None, True)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(ht_linear_models[test].Sys_mean_utilization, benchmark_datasets[test]['runs']['RavgTot'], 0, 0, color, (test if len(test_names) > 1 else "Response Time (ms)"))

plotter.gen_graph("R-vs-U", "Andamento del Response Time rispetto all'Utilizzo Tradizionale" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'Utilizzo Tradizionale'}, {0: 'Response Time (ms)'}, None, 100, True)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(ht_linear_models[test].Sys_mean_productivity, benchmark_datasets[test]['runs']['RavgTot'], 0, 0, color, (test if len(test_names) > 1 else "Response Time (ms)"), True)

plotter.gen_graph("R-vs-P", "Andamento del Response Time rispetto alla Productivity" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'Productivity'}, {0: 'Response Time (ms)'}, None, 100, True)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_active_frequency, 0, 0, color, (None if len(test_names) > 1 else "Active Frequency (GHz)"), False, False, 0, 3500000000)

plotter.gen_graph("AFREQ-vs-X", "Andamento della AFREQ" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'System Throughput'}, {0: 'Active Frequency (GHz)'}, None, None, True, "lower right")

plotter = HTModelPlotter().init(OUTPUT_DIR, 1, True)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0,
                         (colors[0] if len(test_names) == 1 else color), (None if len(test_names) > 1 else "Utilizzo Tradizionale"),
                         False, False, 0, 100)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_active_frequency, 0, 1,
                        (colors[2] if len(test_names) == 1 else color), (None if len(test_names) > 1 else "Active Frequency (GHz)"),
                         False, False, 0, 3500000000)

# Then use the x_max value to print the lr lines
for test, color in zip(test_names, colors):
    plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0,
                          (colors[1] if len(test_names) == 1 else color), (test if len(test_names) > 1 else "Utilization Law"),
                          False, False, 0, 100)

plotter.gen_graph("U,AFREQ-vs-X", "Stima dell'Utilizzo Tradizionale (" + str(bac.NUM_SAMPLES) + " campioni)" + "\n" + bac.BENCHMARK + "\n" + bac.SUT,
                  {0: 'System Throughput'}, {0: 'Utilizzo Tradizionale'}, {0: 'Active Frequency (GHz)'}, None, True, "lower right")