__author__ = 'francesco'

# ==========================================================================
# Benchmark Results Analysis Settings
# ==========================================================================

# Test parameters (used for Linear Regression and others)
NUM_SAMPLES = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
NUM_RUNS = 10 # Number of runs in one test, usually 10 (i.e. number of steps in one growing load ladder)
NUM_TESTS = 10 # Number of test repetitions, usually 10 (i.e. number of growing load ladders). Globally we have a number of single runs equal to NUM_RUNS * NUM_TESTS

# TITLE = "RUBBoS Benchmark variable frequencies test\n" \
#         "Fixed maximum frequencies: 800MHz, 1200MHz, 1600MHz, 2000MHz and 2900MHz\n" \
#         "Linear Regressions consider first " + str(NUM_SAMPLES) + " samples"

# TITLE = "RUBBoS Benchmark\n" \
#         "Linear Regression consider first " + str(NUM_SAMPLES) + " samples"

TITLE = "CBench Benchmark\n" \
        "Linear Regression consider first " + str(NUM_SAMPLES) + " samples"

# TITLE = "SPECpower\_ssj2008 v1.10 Benchmark\n" \
#         "Linear Regression consider first " + str(NUM_SAMPLES) + " samples"

# Runs to be considered in computing real IPC
START_RUN = 1
END_RUN = 10

# Value added to x_max to plot streched line
X_MAX_PADDING = 50 # CBench
# X_MAX_PADDING = 100 # Rubbos
# X_MAX_PADDING = 20000 # SPECpower

