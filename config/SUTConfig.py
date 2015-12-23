__author__ = 'francesco'

# General settings to be changed according to the System Under Test (SUT) configuration

# CPU SETTINGS
# CPU_BASE_OPERATING_RATIO = 25 # RDMSR: Bits 15:8 of register 0xCEH, is the Max Non Turbo Ratio
# CPU_BUS_CLOCK_FREQUENCY = 100000000 # BCLK for Intel SandyBridge and IvyBridge Architecture
# CPU_BUS_CLOCK_FREQUENCY = 133330000 # BCLK for Nehalem Architecture
# CPU_BASE_OPERATING_FREQUENCY = CPU_BASE_OPERATING_RATIO * CPU_BUS_CLOCK_FREQUENCY # Is the Reference Frequency

CPU_NOMINAL_FREQUENCY = 2500000000 # That is the CPU Ref TSC

# CPU_ACTUAL_MAX_FREQUENCY = 800000000
# CPU_ACTUAL_MAX_FREQUENCY = 1200000000
# CPU_ACTUAL_MAX_FREQUENCY = 1600000000
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
# Benchmark Results Analysis Settings
# TEST_NAME = 'RUBBoS-20151210-test-2600-HT1-GPOW-TB0-F1200'
# OUTPUT_DIR = '/home/francesco/Scrivania/' + TEST_NAME + '/'
OUTPUT_DIR = '/home/francesco/Scrivania/HTReports'

# Test parameters (used for Linear Regression and others)
NUM_SAMPLES = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
NUM_RUNS = 10 # Number of runs in one test, usually 10 (i.e. number of steps in one growing load ladder)
NUM_TESTS = 1 # Number of test repetitions, usually 10 (i.e. number of growing load ladders). Globally we have a number of single runs equal to NUM_RUNS * NUM_TESTS

# Values to plot streched line
# MAX_THROUGHPUT = 700 # Rubbos 2000 load
# MAX_THROUGHPUT = 900 # Rubbos 2600 load
# MAX_THROUGHPUT = 1200 # Rubbos 3400 load
MAX_THROUGHPUT = 1500 # Rubbos 4400 load
# MAX_THROUGHPUT = 1600 # Rubbos 5500 load
# MAX_THROUGHPUT = 1800 # Rubbos 5500 load higher throughput

# Runs to be considered in computing real IPC
START_RUN = 9
END_RUN = 10