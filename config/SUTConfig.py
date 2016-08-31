__author__ = 'francesco'

# ==========================================================================
# General settings of the System Under Test (SUT)
# ==========================================================================

class SUTConfig:

    def __init__(self):
        self.CPU_BUS_CLOCK_FREQUENCY = 0
        self.CPU_BASE_OPERATING_FREQUENCY = 0
        self.CPU_BASE_FREQUENCY = 0
        self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 0
        self.CPU_SOCKETS = 0
        self.CPU_PHYSICAL_CORES_PER_SOCKET = 0
        self.CPU_PHYSICAL_CORES = 0
        self.CPU_LOGICAL_CORES = 0
        self.CPU_HT_ACTIVE = True # Default HT is ON
        self.CPU_THREADS_PER_CORE = 0
        self.CPU_SOCKET_TO_PHYSICAL_CORES_MAPPING = {}
        self.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {}

    # Set parameters using the input config file
    def set(self, system_config):
        # PROCESSOR SETTINGS
        if system_config['Model'] == 60 or system_config['Model'] == 63 or system_config['Model'] == 69 or system_config['Model'] == 70:
            self.CPU_BUS_CLOCK_FREQUENCY = 100000000 # BCLK for Intel Haswell Architecture (model number 0x3c = 60, 0x3f = 63, 0x45 = 69 or 0x46 = 70)
        elif system_config['Model'] == 42 or system_config['Model'] == 45 or system_config['Model'] == 58:
            self.CPU_BUS_CLOCK_FREQUENCY = 100000000 # BCLK for Intel SandyBridge (model number 0x2a = 42 or 0x2d = 45) and IvyBridge (0x3a = 58) Architecture
        elif system_config['Model'] == 26 or system_config['Model'] == 30 or system_config['Model'] == 46:
            self.CPU_BUS_CLOCK_FREQUENCY = 133330000 # BCLK for Nehalem Architecture (model number 0x1a = 26 or 0x1e = 30 or 0x2e = 46)

        self.CPU_BASE_OPERATING_FREQUENCY = system_config['BaseOperatingRatio'] * self.CPU_BUS_CLOCK_FREQUENCY # Is the TSC Reference Frequency, used to compute the Core Busy Time and the system mean frequency. CPU_BASE_OPERATING_FREQUENCY = CPU_BASE_OPERATING_RATIO (Max Non Turbo Ratio) * CPU_BUS_CLOCK_FREQUENCY

        self.CPU_BASE_FREQUENCY = system_config['BaseFrequency'] * 1000000000 # The one advertised in CPU Model Name

        # Determine the maximum frequency if using TB or not
        if int(system_config['TurboBoost']) == 0: # TB ON
            print("TurboBoost ON")
            self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = system_config['TurboRatioLimit4Cores'] * self.CPU_BUS_CLOCK_FREQUENCY # Max Frequency when all cores are working, used to estimate the productivity
        else: # TB OFF
            print("TurboBoost OFF")
            self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = self.CPU_BASE_FREQUENCY

        # If the TSC is different from the advertised frequency we warn the user
        if self.CPU_BASE_OPERATING_FREQUENCY != self.CPU_BASE_FREQUENCY:
            print("Warning: frequencies are not equal! CPU_BASE_OPERATING_FREQUENCY: " + str(self.CPU_BASE_OPERATING_FREQUENCY) + " while CPU_BASE_FREQUENCY: " + str(self.CPU_BASE_FREQUENCY))

        print("CPU_BASE_FREQUENCY: " + str(self.CPU_BASE_FREQUENCY))
        print("CPU_BASE_OPERATING_FREQUENCY: " + str(self.CPU_BASE_OPERATING_FREQUENCY))
        print("CPU_MAX_FREQUENCY_ALL_CORES_BUSY: " + str(self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY))

        self.CPU_SOCKETS = int(system_config['Sockets'])
        self.CPU_PHYSICAL_CORES_PER_SOCKET = int(system_config['CoresPerSocket'])
        self.CPU_PHYSICAL_CORES = self.CPU_SOCKETS * self.CPU_PHYSICAL_CORES_PER_SOCKET
        self.CPU_THREADS_PER_CORE = int(system_config['ThreadsPerCore'])
        self.CPU_LOGICAL_CORES = self.CPU_PHYSICAL_CORES * self.CPU_THREADS_PER_CORE

        # Determine if HT is active or not
        if self.CPU_LOGICAL_CORES == system_config['OnlineCPUs']:
            print("HyperThreading ACTIVE")
            self.CPU_HT_ACTIVE = True
        elif (self.CPU_LOGICAL_CORES / 2) == system_config['OnlineCPUs']:
            print("Warning: HyperThreading seems not to be active, number of online CPUs is half the number of logical cores. Setting HT to NOT active.")
            self.CPU_HT_ACTIVE = False
            self.CPU_THREADS_PER_CORE = 1
            self.CPU_LOGICAL_CORES = self.CPU_PHYSICAL_CORES * self.CPU_THREADS_PER_CORE
        else:
            # TODO: Case in which HT is Enabled but not all the logical cores are online
            print("Warning: HyperThreading seems not to be active, different number of online CPUs. Setting HT to NOT active.")
            self.CPU_HT_ACTIVE = False
            self.CPU_THREADS_PER_CORE = 1
            self.CPU_LOGICAL_CORES = self.CPU_PHYSICAL_CORES * self.CPU_THREADS_PER_CORE

        # Determine the topology of processor
        siblings_cpus = system_config['Siblings'].split(" ")
        siblings_cpus.pop() # Remove last element that is a not useful string
        for socket_num in range(int(self.CPU_SOCKETS)): # TODO: associate cpus of multi socket architecture
            self.CPU_SOCKET_TO_PHYSICAL_CORES_MAPPING['S' + str(socket_num)] = []
            for cpu_couple in siblings_cpus:
                self.CPU_SOCKET_TO_PHYSICAL_CORES_MAPPING['S' + str(socket_num)].append(cpu_couple[0])

        if self.CPU_HT_ACTIVE:
            for core_num, cpu_couple in zip(range(int(self.CPU_PHYSICAL_CORES)), siblings_cpus):
                self.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(core_num)] = [cpu_couple[0], cpu_couple[2]]
        else:
            for core_num in range(int(self.CPU_PHYSICAL_CORES)):
                self.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(core_num)] = [core_num]

        print("CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING: " + str(self.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING) + "\n")

    # Set parameters manually
    def set_manual(self):
        # CPU SETTINGS
        # CPU_BASE_OPERATING_RATIO = 25 # RDMSR: Bits 15:8 of register 0xCEH, is the Max Non Turbo Ratio
        # CPU_BUS_CLOCK_FREQUENCY = 100000000 # BCLK for Intel SandyBridge and IvyBridge Architecture
        # CPU_BUS_CLOCK_FREQUENCY = 133330000 # BCLK for Nehalem Architecture
        # CPU_BASE_OPERATING_FREQUENCY = CPU_BASE_OPERATING_RATIO * CPU_BUS_CLOCK_FREQUENCY # Is the Reference Frequency

        self.CPU_BASE_FREQUENCY = 2000000000 # That is the advertised nominal frequency
        self.CPU_BASE_OPERATING_FREQUENCY = 2500000000 # Is the TSC Reference Frequency, used to compute the Core Busy Time and the system mean frequency.

        # self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 800000000
        # self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 1200000000
        # self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 1600000000
        # self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 2000000000 # If HT ON TB OFF
        self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 2500000000 # If HT ON and TB ON
        # self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 2900000000 # If HT OFF and TB ON
        # self.CPU_MAX_FREQUENCY_ALL_CORES_BUSY = 3100000000 # If single core ? and TB ON

        self.CPU_SOCKETS = 1
        self.CPU_PHYSICAL_CORES_PER_SOCKET = 2
        self.CPU_PHYSICAL_CORES = self.CPU_SOCKETS * self.CPU_PHYSICAL_CORES_PER_SOCKET

        self.CPU_HT_ACTIVE = True

        if self.CPU_HT_ACTIVE:
            self.CPU_THREADS_PER_CORE = 2
            self.CPU_SOCKET_TO_PHYSICAL_CORES_MAPPING = {'S' + str(i) : [i, i+1] for i in range(self.CPU_SOCKETS)} # Both CPUs belong to Socket 0
            self.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {'CPU' + str(i) : [i, i+2] for i in range(self.CPU_PHYSICAL_CORES)} # Alterned Logical CPUs
        else:
            self.CPU_THREADS_PER_CORE = 1
            self.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING = {'CPU' + str(i) : [i] for i in range(self.CPU_PHYSICAL_CORES)}

        self.CPU_LOGICAL_CORES = self.CPU_PHYSICAL_CORES * self.CPU_THREADS_PER_CORE