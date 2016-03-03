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
import sys

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

print('{:>19}\t{:>27}\t{:>27}\t{:>23}\t{:>20}\t{:>22}\t{:>23}\t{:>26}'.format(
    Parser.TIMESTAMP_START_STR,
    "Sys Mean Estimated IPC_TD1",
    "Sys Mean Estimated IPC_TD2",
    "S0-C0 Instructions_max",
    "Sys Productivity",
    "Sys Utilization (Sar)",
    "Sys Avg Thread Density",
    "Sys Mean Active Frequency"
    ))

models = {}
# Compute only Ci_unhalted_clk_td2, Ci_unhalted_clk_td1 and Ci_instr of first element and skip the remaining
# For i > 1 do the linear regression using current element and previous one
for i in range(0,len(live_report_datasets)):
    models[i] = LiveHTLinearModel().init(my_sut_config)

    if not models[i].my_sut_config.CPU_HT_ACTIVE: # Hyperthreading OFF
        models[i].Ci_unhalted_clk_td1 = models[i].compute_unhalted_clk_td1(live_report_datasets[i])
        models[i].Ci_instr = models[i].compute_instr(live_report_datasets[i])

        if i != 0:
            models[i].linear_model = models[i].estimate_IPCs(models[i-1].Ci_unhalted_clk_td1, models[i-1].Ci_instr, models[i].Ci_unhalted_clk_td1, models[i].Ci_instr)
    else : # Hyperthreading ON
        models[i].Ci_unhalted_clk_td2 = models[i].compute_unhalted_clk_td2(live_report_datasets[i])
        models[i].Ci_unhalted_clk_td1 = models[i].compute_unhalted_clk_td1(live_report_datasets[i], models[i].Ci_unhalted_clk_td2)
        models[i].Ci_instr = models[i].compute_instr(live_report_datasets[i])

        if i != 0:
            models[i].linear_model = models[i].estimate_IPCs(models[i-1].Ci_unhalted_clk_td1, models[i-1].Ci_instr, models[i].Ci_unhalted_clk_td1, models[i].Ci_instr, models[i-1].Ci_unhalted_clk_td2, models[i].Ci_unhalted_clk_td2)

    if i != 0:
        models[i].Ci_instr_max = models[i].compute_instr_max(models[i].linear_model)
        models[i].Ci_productivity = models[i].compute_productivity(models[i].Ci_instr, models[i].Ci_instr_max)
        models[i].Sys_mean_productivity = models[i].compute_sys_mean_productivity(models[i].Ci_productivity)

        models[i].Ci_IPC_max_td_max = models[i].compute_IPC_at_run_with_td_max(live_report_datasets[i], bac.START_RUN, bac.END_RUN)
        models[i].Sys_mean_IPC_td_max = models[i].compute_sys_mean_IPC_at_td_max(models[i].Ci_IPC_max_td_max)
        models[i].Sys_mean_estimated_IPC = models[i].compute_sys_mean_estimated_IPC(models[i].linear_model)

        if not models[i].my_sut_config.CPU_HT_ACTIVE: # Hyperthreading OFF
            models[i].Ci_atd = models[i].compute_atd(live_report_datasets[i], models[i].Ci_unhalted_clk_td1)
        else : # Hyperthreading ON
            models[i].Ci_atd = models[i].compute_atd(live_report_datasets[i], models[i].Ci_unhalted_clk_td1, models[i].Ci_unhalted_clk_td2)

        models[i].Sys_mean_atd = models[i].compute_sys_mean_atd(models[i].Ci_atd)

        models[i].Ci_cbt = models[i].compute_core_busy_time(live_report_datasets[i])
        models[i].Sys_mean_cbt = models[i].compute_sys_mean_core_busy_time(models[i].Ci_cbt)
        models[i].Sys_mean_utilization = models[i].compute_sys_mean_utilization(live_report_datasets[i])

        models[i].Ci_active_frequency = models[i].compute_mean_active_frequencies(live_report_datasets[i])
        models[i].Sys_mean_active_frequency = models[i].compute_sys_mean_active_frequency(models[i].Ci_active_frequency)

        print('{:>19}\t{:>27}\t{:>27}\t{:>23}\t{:>20}\t{:>22}\t{:>23}\t{:>26}'.format(
            str(live_report_datasets[i]['sar-stats']['mean'][Parser.TIMESTAMP_START_STR][0]),
            # str(models[i].linear_model['S0-C0']['coefficients'][0][0]),
            # (str(models[i].linear_model['S0-C0']['coefficients'][0][1]) if models[i].my_sut_config.CPU_HT_ACTIVE else "-"),
            (str(models[i].Sys_mean_estimated_IPC[0]) if not models[i].my_sut_config.CPU_HT_ACTIVE else "HT ON: see IPC_TD2"),
            (str(models[i].Sys_mean_estimated_IPC[0]) if models[i].my_sut_config.CPU_HT_ACTIVE else "HT OFF: see IPC_TD1"),
            (str(models[i].Ci_instr_max['S0-C0'][0][0]) if not models[i].my_sut_config.CPU_HT_ACTIVE else str(models[i].Ci_instr_max['S0-C0'][0][1])),
            str(models[i].Sys_mean_productivity[0] * 100),
            str(models[i].Sys_mean_utilization[0]),
            str(models[i].Sys_mean_atd[0]),
            str(models[i].Sys_mean_active_frequency[0])
        ))
