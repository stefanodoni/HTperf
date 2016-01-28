__author__ = 'francesco'

# ==========================================================================
# Benchmark Results Analysis Settings
# ==========================================================================

# Test parameters (used for Linear Regression and others)
NUM_SAMPLES = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
NUM_RUNS = 10 # Number of runs in one test, usually 10 (i.e. number of steps in one growing load ladder)
NUM_TESTS = 1 # Number of test repetitions, usually 10 (i.e. number of growing load ladders). Globally we have a number of single runs equal to NUM_RUNS * NUM_TESTS

# Values to plot streched line
# MAX_THROUGHPUT = 700 # Rubbos 2000 load
# MAX_THROUGHPUT = 1100 # Rubbos 2900 load
# MAX_THROUGHPUT = 1400 # Rubbos 3800 load
MAX_THROUGHPUT = 1500 # Rubbos 4400 load
# MAX_THROUGHPUT = 1600 # Rubbos 5500 load
# MAX_THROUGHPUT = 1800 # Rubbos 5500 load higher throughput
# MAX_THROUGHPUT = 150 # CBench Throughput 10ms
# MAX_THROUGHPUT = 400 # CBench Throughput 1ms
# MAX_THROUGHPUT = 160000 # SPECpower Throughput

# Runs to be considered in computing real IPC
START_RUN = 1
END_RUN = 10