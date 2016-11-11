#!/usr/bin/python3
import os
import argparse
import csv
import sqlite3
import sqlalchemy as sqlal
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
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


parser = argparse.ArgumentParser(description='HTperf tool: parse, aggregate, select and plot data.')
parser.add_argument('benchmarkdirpath', metavar='benchmarkdirpath', help='path to directory containing n benchmark report directories, each one containing the csv report files')
parser.add_argument('reportdirpath', metavar='reportdirpath', help='path to directory in which the tool generates the reports')
parser.add_argument('-pcm', help='indicates if a pcm.csv file must be parsed', dest='pcm', action='store_true')
parser.add_argument('-sysconfig', help='indicates if a sysConfig.csv file must be parsed', dest='sysconfig', action='store_true')
parser.add_argument('--chart-no-legend', help='do not include legend in charts', action='store_true', default=False)
parser.add_argument('--chart-no-model', help='do not include regression model in charts', action='store_true')
parser.add_argument('--chart-xmax', help='max value of the throughput axis in charts', type=int, default=None)
parser.add_argument('--chart-umax', help='max value of the utilization axis in charts', type=int, default=None)
parser.add_argument('--chart-line-p-max', help='max value of the extrapolation line for productivity in charts', type=int, default=None)
parser.add_argument('--chart-line-u-max', help='max value of the extrapolation line for utilization in charts', type=int, default=None)
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
benchmark_SUTconfigs = {}
sar_dataframes = {}
pcm_dataframes = {}
perf_dataframes = {}

benchmark_datasets = {}

ht_linear_models = {}

# ======================= DATA IMPORT =============================
if not using_sysconfig:
    my_sut_config = SUTConfig()
    my_sut_config.set_manual()

for test in test_names:
    # benchmark_detailed_dataframe = BenchmarkParser().parse(benchmark_detailed_file, "detailed") # Only if using the detailed version of benchmark report file
    benchmark_dataframes[test] = BenchmarkParser().parse(path_to_tests + '/' + test + benchmark_file)
    sar_dataframes[test] = SarParser().parse(path_to_tests + '/' + test + sar_file)
    perf_dataframes[test] = PerfParser().parse(path_to_tests + '/' + test + perf_file)

    if using_sysconfig:
        print("Setting SysConfig file of test: " + test)
        system_config = SysConfigParser().parse(path_to_tests + '/' + test + sysconfig_file)
        benchmark_SUTconfigs[test] = SUTConfig()
        benchmark_SUTconfigs[test].set(system_config)

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
    if using_sysconfig:
        ht_linear_models[test] = HTLinearModel().estimate(benchmark_datasets[test], OUTPUT_DIR, test, benchmark_SUTconfigs[test])
    else:
        ht_linear_models[test] = HTLinearModel().estimate(benchmark_datasets[test], OUTPUT_DIR, test, my_sut_config)

### Full Dump of benchmark, perf and models data to CSV
for test in test_names:
    benchmark_datasets[test]['perf-stats']['mean'].to_csv("mtperf-perf-dump-" + test + ".csv", sep=";")
    benchmark_datasets[test]['runs']['XavgTot'].to_csv("mtperf-bench-dump-" + test + ".csv", sep=";")
    ht_linear_models[test].Sys_mean_real_IPC.to_csv("mtperf-models-realIPC-dump-" + test + ".csv", sep=";")

# ======================= PLOT GRAPHS =====================================
# colors = ['#E12727', '#504FAF', '#088DA5', '#FE9900', '#12AD2A'] #281D46
colors = ['#0041CC', '#FF0000', '#E6C700', '#FF00BF', '#00CC22']
colors_second_ax = ['#f0f465', '#9cec5b', '#50c5b7', '#6184d8', '#533a71']

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0, color, (None if len(test_names) > 1 else "CPU Utilization \\%"), False, False, 0, 100)

if not args.chart_no_model:
    # Then use the x_max value to print the lr lines
    for test, color in zip(test_names, colors):
        color = (colors[1] if len(test_names) == 1 else color)
        plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0, color, (test if len(test_names) > 1 else "Utilization Law"), False, False, 0, 100)

plotter.gen_graph("U-vs-X", "",
                  #"Stima dell'Utilizzo (sui primi " + str(bac.NUM_SAMPLES) + " campioni)" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
                  {0: 'Throughput (req/sec)'}, {0: 'Utilization \\%'}, X_axis_max=args.chart_xmax, include_legend=not args.chart_no_legend)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 1, 0, color, (None if len(test_names) > 1 else "Productivity"), False, True)#, 0, 100)

# Then use the x_max value to print the lr lines
for test, color in zip(test_names, colors):
    color = (colors[1] if len(test_names) == 1 else color)
    plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 1, 0, color, (test if len(test_names) > 1 else "Linear Regression"), False, True)#, 0, 100)

plotter.gen_graph("P-vs-X", "",
                  #""Stima della Productivity (sui primi " + str(bac.NUM_SAMPLES) + " campioni)" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
                  {0: 'Throughput (req/sec)'}, {0: 'Productivity \\%'}, None, None, True)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0,
                        (colors[0] if len(test_names) == 1 else color), (None if len(test_names) > 1 else "Utilization"),
                        False, False)#, 0, 100)

    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 0, 0,
                        (colors[1] if len(test_names) == 1 else color), (None if len(test_names) > 1 else "Productivity"),
                         False, True)#, 0, 100)

if not args.chart_no_model:
# Then use the x_max value to print the lr lines
    for test, color in zip(test_names, colors):
        plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_utilization, 0, 0,
                          (colors[0] if len(test_names) == 1 else color),
                          (test if len(test_names) > 1 else "Utilization Law"), False, False, x_line_max=args.chart_line_u_max)#, 0, 100)#, False)

        plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_productivity, 0, 0,
                      (colors[1] if len(test_names) == 1 else color),
                      (test if len(test_names) > 1 else "Extrapolated Prod."), False, True, x_line_max=args.chart_line_p_max)

plotter.gen_graph("U,P-vs-X", "",
                  #"Stima dell'Utilizzo (sui primi " + str(bac.NUM_SAMPLES) + " campioni)" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
                  {0: 'Throughput (req/sec)'}, {0: 'Utilization \\%, Productivity \\%'}, X_axis_max=args.chart_xmax, legend_inside_graph=True, include_legend=not args.chart_no_legend)

## plotter = HTModelPlotter().init(OUTPUT_DIR, 2)
# # First plot scatter and standard points in order to determinate the maximum X value
# for test, color in zip(test_names, colors):
#     plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], benchmark_datasets[test]['runs']['RavgTot'], 0, 0, color, test + '\nTot Avg Response Time (ms)')
#     plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_atd, 1, 0, color, test + '\nTot Avg Thread Concurrency', False, False, 1, 2)
#
# plotter.gen_graph("R,atc-vs-X", bac.TITLE, {0: 'Throughput', 1: 'Throughput'}, {0: 'Tot Avg Response Time (ms)', 1: 'Tot Avg Thread Concurrency'})

#plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
## First plot scatter and standard points in order to determinate the maximum X value
#for test, color in zip(test_names, colors):
#    color = (colors[0] if len(test_names) == 1 else color)
#    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_atd, 0, 0, color, (test if len(test_names) > 1 else "ATC"), False, False, 1, 2)
#
#plotter.gen_graph("Atc-vs-X", "",
#                  #"Andamento dell'Average Thread Concurrency" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
#                  {0: 'Throughput'}, {0: 'Average Thread Concurrency'}, None, None, True)
#
plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
# First plot scatter and standard points in order to determinate the maximum X value
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(ht_linear_models[test].Sys_mean_utilization, benchmark_datasets[test]['runs']['RavgTot'], 0, 0, color, (test if len(test_names) > 1 else "Response Time (ms)"))

plotter.gen_graph("R-vs-U", "",
                  #"Andamento del Response Time rispetto all'Utilizzo" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
                  {0: 'Utilization \\%'}, {0: 'Response Time (ms)'}, X_axis_max=args.chart_umax, include_legend=not args.chart_no_legend)
#
#plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
## First plot scatter and standard points in order to determinate the maximum X value
#for test, color in zip(test_names, colors):
#    color = (colors[0] if len(test_names) == 1 else color)
#    plotter.plot_scatter(ht_linear_models[test].Sys_mean_productivity, benchmark_datasets[test]['runs']['RavgTot'], 0, 0, color, (test if len(test_names) > 1 else "Response Time (ms)"), True)
#
#plotter.gen_graph("R-vs-P", "",
#                  #"Andamento del Response Time rispetto alla Productivity" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
#                  {0: 'Productivity'}, {0: 'Response Time (ms)'}, None, 140, True)
#
#plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
## First plot scatter and standard points in order to determinate the maximum X value
#for test, color in zip(test_names, colors):
#    if using_sysconfig:
#        my_sut_config = benchmark_SUTconfigs[test]
#
#    color = (colors[0] if len(test_names) == 1 else color)
#    plotter.plot_scatter( ht_linear_models[test].Sys_mean_active_frequency, 0, 0,
#                         color, (test if len(test_names) > 1 else "AFREQ (GHz)"),
#                         False, False, 0, (my_sut_config.CPU_MAX_FREQUENCY_ALL_CORES_BUSY + 600000000))
#
#plotter.gen_graph("AFREQ-vs-X", "",
#                  #"Andamento dell'Active Frequency" + "\n" + bac.BENCHMARK,# + "\n" + bac.SUT,
#                  {0: 'Throughput'}, {0: 'Active Frequency (GHz)'}, None, None, True, "lower right")
#

benchX = pd.Series([15633,30742,45689,60752,75282,90151,105483,120570,136335,148312])
#afreq = pd.Series([1.2863893771,1.7623052723,2.1674793625,2.4566290458,2.6498259159,2.7822519266,2.8569867656,2.896732531,2.9050008713,2.8996203862])
#core_busy_time = pd.Series([ 0.112894609, 0.2221528827, 0.3224394861, 0.4312730359, 0.539689001, 0.6395914782, 0.7470188007, 0.8404833952, 0.9391003009, 1])
instr = pd.Series([188.7400993175, 368.113962475, 542.7210293267, 718.3456908025, 892.9922278983, 1061.2639747475, 1246.3635704375, 1423.1804586467, 1610.9732021967, 1754.9474657242])

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
for test, color in zip(test_names, colors):
    color = (colors[0] if len(test_names) == 1 else color)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_active_frequency, 0, 0, color, "test chart", False, False, 0, None)
    if not args.chart_no_model:
        plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_active_frequency, 0, 0, color, "AFREQ", False, False, 0, None)
plotter.gen_graph("AFREQ-vs-X", "", {0: 'Throughput'}, {0: 'Active Frequency (GHz)'}, X_axis_max=args.chart_xmax, include_legend=not args.chart_no_legend)



for test in test_names:
    plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_active_frequency, 0, 0, colors[0] , "test chart", False, False, 0, None)
    if not args.chart_no_model:
        plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_active_frequency, 0, 0, colors[1], "AFREQ", False, False, 0, None)
    plotter.gen_graph(test + "-AFREQ-vs-X", "", {0: 'Throughput'}, {0: 'Active Frequency (GHz)'}, X_axis_max=args.chart_xmax, include_legend=not args.chart_no_legend)

    plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], benchmark_datasets[test]['perf-stats']['mean']['CPU0_cpu_clk_unhalted_thread_any'] , 0, 0, colors[0] , "test chart", False, False, 0, None)
    plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], benchmark_datasets[test]['perf-stats']['mean']['CPU0_cpu_clk_unhalted_thread_any'], 0, 0, colors[1], "Core unhalted cycles", False, False, 0, None)
    plotter.gen_graph(test + "-CUC-vs-X", "", {0: 'Throughput'}, {0: 'Core Unhalted Cycles'}, None, None, True, "lower right", False)

    plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
    plotter.plot_scatter(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_real_IPC, 0, 0, colors[0], "chart", False, False, 0, None)
    plotter.plot_lin_regr(benchmark_datasets[test]['runs']['XavgTot'], ht_linear_models[test].Sys_mean_real_IPC, 0, 0, colors[1], "Instructions per cycle", False, False, 0, None)
    plotter.gen_graph(test + "-IPC-vs-X", "", {0: 'Throughput'}, {0: 'Instructions per cycle'}, None, None, True, "lower right", False)

plotter = HTModelPlotter().init(OUTPUT_DIR, 1)
plotter.plot_scatter(benchX, instr, 0, 0, colors[0] , "test chart", False, False, 0, None)
if not args.chart_no_model:
    plotter.plot_lin_regr(benchX, instr, 0, 0, colors[1], "Retired instructions (Millions/sec)", False, False, 0, None)
#plotter.gen_graph("INSTR-vs-X", "", {0: 'Throughput'}, {0: 'Retired instructions (Millions/sec)'}, None, None, True, "lower right", False)
plotter.gen_graph("INSTR-vs-X", "", {0: 'Throughput'}, {0: 'Retired instructions (Millions/sec)'}, X_axis_max=args.chart_xmax, include_legend=not args.chart_no_legend)
