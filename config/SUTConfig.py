__author__ = 'francesco'

# General settings to be changed according to the System Under Test (SUT) configuration

# CPU SETTINGS
CPU_NOMINAL_FREQUENCY = 2500000000 # That is the CPU Ref TSC

# CPU_ACTUAL_MAX_FREQUENCY = 2000000000 # If HT ON TB OFF
CPU_ACTUAL_MAX_FREQUENCY = 2500000000 # If HT ON and TB ON
# CPU_ACTUAL_MAX_FREQUENCY = 2900000000 # If HT OFF and TB ON
# CPU_ACTUAL_MAX_FREQUENCY = 3100000000 # If single core ? and TB ON

CPU_SOCKETS = 1
CPU_PHYSICAL_CORES_PER_SOCKET = 2
CPU_PHYSICAL_CORES = CPU_SOCKETS * CPU_PHYSICAL_CORES_PER_SOCKET

CPU_HT_ACTIVE = True

if CPU_HT_ACTIVE:
    CPU_THREADS_PER_CORE = 2
    CPU_SOCKET_TO_PHYSICAL_CORES_MAPPING = {'S' + str(i) : [i, i+1] for i in range(CPU_SOCKETS)} # Both CPUs belong to Socket 0
    CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {'CPU' + str(i) : [i, i+2] for i in range(CPU_PHYSICAL_CORES)} # Alterned Logical CPUs
else:
    CPU_THREADS_PER_CORE = 1
    CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {'CPU' + str(i) : [i] for i in range(CPU_PHYSICAL_CORES)}

CPU_LOGICAL_CORES = CPU_PHYSICAL_CORES * CPU_THREADS_PER_CORE

# ==========================================================================
# Benchmark Analysis Settings
TEST_NAME = 'RUBBoS-20151208-5500-HT1-GPERF-TB1'
OUTPUT_DIR = '/home/francesco/Scrivania/' + TEST_NAME + '/'

# Linear Regression parameters
NUM_SAMPLES = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
NUM_RUNS = 10 # Number of runs in one test

# Runs to be considered in computing real IPC
START_RUN = 9
END_RUN = 10