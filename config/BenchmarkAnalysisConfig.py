
# ==========================================================================
# Benchmark Results Analysis Settings
# ==========================================================================

# Test parameters (used for Linear Regression and others)
NUM_SAMPLES = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
NUM_RUNS = 10 # Number of runs in one test, usually 10 (i.e. number of steps in one growing load ladder)
NUM_TESTS = 10 # Number of test repetitions, usually 10 (i.e. number of growing load ladders). Globally we have a number of single runs equal to NUM_RUNS * NUM_TESTS

# BENCHMARK = "RUBBoS Benchmark"
# BENCHMARK = "CBench Benchmark"
BENCHMARK = "SPECpower\_ssj 2008 Benchmark"

# SUT = "SUT: HT on, TB on, Governor powersave"
SUT = "SUT: HT on, TB on, Governor performance"
# SUT = "SUT: HT on, TB off, Governor powersave"
# SUT = "SUT: HT on, TB off, Governor performance"
# SUT = "SUT: HT off, TB on, Governor powersave"
# SUT = "SUT: HT off, TB on, Governor performance"
# SUT = "SUT: HT off, TB off, Governor powersave"
# SUT = "SUT: HT off, TB off, Governor performance"

# Runs to be considered in computing real IPC
START_RUN = 1
END_RUN = 10

# Value added to x_max to plot streched line
# X_MAX_PADDING = 20 # Graphs without LR to strech
# X_MAX_PADDING = 50 # CBench
# X_MAX_PADDING = 100 # Rubbos
X_MAX_PADDING = 20000 # SPECpower
