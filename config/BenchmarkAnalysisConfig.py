__author__ = 'francesco'

# ==========================================================================
# Benchmark Results Analysis Settings
# ==========================================================================

# Test parameters (used for Linear Regression and others)
NUM_SAMPLES = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
NUM_RUNS = 10 # Number of runs in one test, usually 10 (i.e. number of steps in one growing load ladder)
NUM_TESTS = 1 # Number of test repetitions, usually 10 (i.e. number of growing load ladders). Globally we have a number of single runs equal to NUM_RUNS * NUM_TESTS

# Runs to be considered in computing real IPC
START_RUN = 1
END_RUN = 10

# Value added to x_max to plot streched line
MAX_THROUGHPUT_PADDING = 100

LIMIT_Y_AXIS_TO_100 = True


