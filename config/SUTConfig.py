__author__ = 'francesco'

# General settings to be changed according to the System Under Test (SUT) configuration

# CPU SETTINGS
CPU_NOMINAL_FREQUENCY = 2500000000 # Oppure 2000000000 ??
CPU_SOCKETS = 1
CPU_PHYSICAL_CORES_PER_SOCKET = 2
CPU_THREADS_PER_CORE = 2 # HT ON
# CPU_THREADS_PER_CORE = 1 # HT OFF

CPU_HT_ACTIVE = CPU_THREADS_PER_CORE // 2 # 1 = HT Active, 0 = HT Disabled

CPU_PHYSICAL_CORES = CPU_SOCKETS * CPU_PHYSICAL_CORES_PER_SOCKET
CPU_LOGICAL_CORES = CPU_PHYSICAL_CORES * CPU_THREADS_PER_CORE

# HT ON
CPU_SOCKET_TO_PHYSICAL_CORES_MAPPING = {'S' + str(i) : [i, i+1] for i in range(CPU_SOCKETS)} # Both CPUs belong to Socket 0
CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {'CPU' + str(i) : [i, i+2] for i in range(CPU_PHYSICAL_CORES)} # Alterned Logical CPUs

# HT OFF
# CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {'CPU' + str(i) : [i] for i in range(CPU_PHYSICAL_CORES)}


# Miscellaneous
TEST_NAME = 'RUBBoS-5500-HT1-GPERF-TB1'
OUTPUT_DIR = '/home/francesco/Scrivania/' + TEST_NAME + '/'
