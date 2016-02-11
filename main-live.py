#!/usr/bin/python3.4
import argparse
import sqlite3
import pandas as pd
from database import DBConstants
from datasets.LiveReportDataset import LiveReportDataset
from parsers.Parser import Parser
from parsers.SarParser import SarParser
from parsers.PerfParser import PerfParser
from parsers.SysConfigParser import SysConfigParser
from statistics.LiveHTLinearModel import LiveHTLinearModel
from config.SUTConfig import SUTConfig
import config.BenchmarkAnalysisConfig as bac

__author__ = 'francesco'

parser = argparse.ArgumentParser(description='HTperf tool: parse, aggregate, select and plot data.')
parser.add_argument('inputdirpath', metavar='inputdirpath', help='path to directory containing sar.csv and perf.csv report files')
parser.add_argument('interval', metavar='interval', help='sampling interval')
parser.add_argument('-sysconfig', help='indicates if a sysConfig.csv file must be parsed', dest='sysconfig', action='store_true')
args = parser.parse_args()

# Settings
using_sysconfig = args.sysconfig
interval = int(args.interval)
path_to_reports = args.inputdirpath

sar_file = "/sar.csv"
perf_file = "/perf.csv"
sysconfig_file = "/sysConfig.csv"

# Data structures
system_config = {}
live_report_datasets = {}

# ======================= DATA IMPORT =============================
if using_sysconfig:
    system_config = SysConfigParser().parse(path_to_reports + sysconfig_file)
    my_sut_config = SUTConfig()
    my_sut_config.set(system_config)
else:
    my_sut_config = SUTConfig()
    my_sut_config.set_manual()

sar_dataframe = SarParser().parse(path_to_reports + sar_file)
perf_dataframe = PerfParser().parse(path_to_reports + perf_file)

start_TS = sar_dataframe[Parser.TIMESTAMP_STR].iloc[0]
end_TS = sar_dataframe[Parser.TIMESTAMP_STR].iloc[-1]

# ======================= PERSIST DATA IN SQLITE ====================
#os.remove(DBConstants.DB_NAME) # Remove DB file and reconstruct it
conn = sqlite3.connect(DBConstants.DB_NAME)
c = conn.cursor()

sar_dataframe.to_sql(DBConstants.SAR_TABLE, conn, if_exists='append')
perf_dataframe.to_sql(DBConstants.PERF_TABLE, conn, if_exists='append')

conn.commit()

i = 0
while start_TS + pd.Timedelta(seconds=interval) < end_TS:
    live_report_datasets[i] = LiveReportDataset().create(conn, start_TS, start_TS + pd.Timedelta(seconds=interval))
    start_TS = start_TS + pd.Timedelta(seconds=interval)
    i += 1

conn.close()

# ======================= STATISTICS =====================================

print('{:>20}\t{:>20}\t{:>28}\t{:>28}\t{:>20}\t{:>20}\t{:>20}\t{:>22}\t{:>20}\t'.format(
    Parser.TIMESTAMP_START_STR,
    Parser.TIMESTAMP_END_STR,
    "Sys Mean Forecasted IPC_TD1",
    "Sys Mean Forecasted IPC_TD2",
    "S0-C0 Instructions_max",
    "Sys Productivity",
    "Sys Utilization (Sar)",
    "Sys Avg Thread Density",
    "Sys Mean Frequency"
    ))
for i in range(0,len(live_report_datasets)):
    model = LiveHTLinearModel().init(my_sut_config)

    if not model.my_sut_config.CPU_HT_ACTIVE: # Hyperthreading OFF
        model.Ci_unhalted_clk_td1 = model.compute_td1(live_report_datasets[i])
        model.Ci_instr = model.compute_instr(live_report_datasets[i])

        model.linear_model = model.estimate_IPCs(model.Ci_unhalted_clk_td1, model.Ci_instr)
    else : # Hyperthreading ON
        model.Ci_unhalted_clk_td2 = model.compute_td2(live_report_datasets[i])
        model.Ci_unhalted_clk_td1 = model.compute_td1(live_report_datasets[i], model.Ci_unhalted_clk_td2)
        model.Ci_instr = model.compute_instr(live_report_datasets[i])

        model.linear_model = model.estimate_IPCs(model.Ci_unhalted_clk_td1, model.Ci_instr, model.Ci_unhalted_clk_td2)

    model.Ci_instr_max = model.compute_instr_max(model.linear_model)
    model.Ci_productivity = model.compute_productivity(model.Ci_instr, model.Ci_instr_max)
    model.Sys_mean_productivity = model.compute_sys_mean_productivity(model.Ci_productivity)

    model.Ci_IPC_max_td_max = model.compute_IPC_at_run_with_td_max(live_report_datasets[i], bac.START_RUN, bac.END_RUN)
    model.Sys_mean_IPC_td_max = model.compute_sys_mean_IPC_at_td_max(model.Ci_IPC_max_td_max)
    model.Sys_mean_estimated_IPC = model.compute_sys_mean_estimated_IPC(model.linear_model)

    if not model.my_sut_config.CPU_HT_ACTIVE: # Hyperthreading OFF
        model.Ci_atd = model.compute_atd(live_report_datasets[i], model.Ci_unhalted_clk_td1)
    else : # Hyperthreading ON
        model.Ci_atd = model.compute_atd(live_report_datasets[i], model.Ci_unhalted_clk_td1, model.Ci_unhalted_clk_td2)

    model.Sys_mean_atd = model.compute_sys_mean_atd(model.Ci_atd)

    model.Ci_cbt = model.compute_core_busy_time(live_report_datasets[i])
    model.Sys_mean_cbt = model.compute_sys_mean_core_busy_time(model.Ci_cbt)
    model.Sys_mean_utilization = model.compute_sys_mean_utilization(live_report_datasets[i])

    model.Ci_frequency = model.compute_mean_frequencies(live_report_datasets[i])
    model.Sys_mean_frequency = model.compute_sys_mean_frequency(model.Ci_frequency)

    print('{:>20}\t{:>20}\t{:>28}\t{:>28}\t{:>20}\t{:>20}\t{:>20}\t{:>22}\t{:>20}\t'.format(
        str(live_report_datasets[i]['sar-stats']['mean'][Parser.TIMESTAMP_START_STR][0]),
        str(live_report_datasets[i]['sar-stats']['mean'][Parser.TIMESTAMP_END_STR][0]),
        # str(model.linear_model['S0-C0']['coefficients'][0][0]),
        # (str(model.linear_model['S0-C0']['coefficients'][0][1]) if model.my_sut_config.CPU_HT_ACTIVE else "-"),
        (str(model.Sys_mean_estimated_IPC[0]) if not model.my_sut_config.CPU_HT_ACTIVE else "HT ON"),
        (str(model.Sys_mean_estimated_IPC[0]) if model.my_sut_config.CPU_HT_ACTIVE else "HT OFF"),
        (str(model.Ci_instr_max['S0-C0'][0][0]) if not model.my_sut_config.CPU_HT_ACTIVE else str(model.Ci_instr_max['S0-C0'][0][1])),
        str(model.Sys_mean_productivity[0] * 100),
        str(model.Sys_mean_utilization[0]),
        str(model.Sys_mean_atd[0]),
        str(model.Sys_mean_frequency[0])
    ))
