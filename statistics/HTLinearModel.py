from sklearn import linear_model as lm
import numpy as np
import pandas as pd
import config.BenchmarkAnalysisConfig as bac

__author__ = 'francesco'

class HTLinearModel:
    # Estimate multivariate linear regression model for each physical CPU and compute CPU productivity.
    # Parameters:
    #   - Ci_instr: sum of CPUi_(thread i) instructons, where i belongs to physical CPU Ci
    #   - Ci_unhalted_clk_td2 = sum of CPUi_cpu_clk_unhalted_thread - CPUi_cpu_clk_unhalted_thread_any, where i belongs to physical CPU Ci => clock cycles with Thread Density 2
    #   - Ci_unhalted_clk_td1: CPUi_cpu_clk_unhalted_thread_any - Ci_unhalted_clk_td2 => clock cycles with Thread Density 1
    #
    # Unknowns (Multivariate Linear Regression coefficients):
    #   - IPC_td1
    #   - IPC_td2 (= IPC_td1 * S, with S = Speedup w.r.t. IPC_td1)
    #
    # Equation:
    #   Ci_instr = IPC_td1 * Ci_unhalted_clk_td1 + IPC_td2 * Ci_unhalted_clk_td2
    #
    # To compute CPU productivity we need the max number of instructions with td2.
    #   - Ci_instr_max = Nominal CPU Frequency * IPC_td2
    #   - Ci_productivity = Ci_instr / Ci_instr_max
    #
    # Finally we compute Sys_mean_productivity as the global system mean of all Ci_productivity
    #
    # We can then correlate the run throughput with productivity and run utilization, plotting graphs and computing R^2

    output_dir = ''
    test_name = ''
    my_sut_config = None

    Ci_unhalted_clk_td1 = {}
    Ci_unhalted_clk_td2 = {}
    Ci_instr = {}

    linear_model = {}
    Ci_instr_max = {}
    Ci_productivity = {}
    Sys_mean_productivity = pd.Series()

    Ci_real_IPCs = {}
    Sys_mean_real_IPC = pd.Series()
    Sys_mean_estimated_IPC = pd.Series()

    Ci_atd = {}
    Sys_mean_atd = {}

    Ci_cbt = {}
    Sys_mean_cbt = {}
    Sys_mean_utilization = pd.Series()

    Ci_active_frequency = {}
    Sys_mean_active_frequency = pd.Series()

    def estimate(self, dataset, output_dir, test_name, my_sut_config):
        self.output_dir = output_dir
        self.test_name = test_name
        self.my_sut_config = my_sut_config

        if not self.my_sut_config.CPU_HT_ACTIVE: # Hyperthreading OFF
            self.Ci_unhalted_clk_td1 = self.compute_unhalted_clk_td1(dataset)
            self.Ci_instr = self.compute_instr(dataset)

            self.linear_model = self.estimate_IPCs(self.Ci_unhalted_clk_td1, self.Ci_instr)
        else : # Hyperthreading ON
            self.Ci_unhalted_clk_td2 = self.compute_unhalted_clk_td2(dataset)
            self.Ci_unhalted_clk_td1 = self.compute_unhalted_clk_td1(dataset, self.Ci_unhalted_clk_td2)
            self.Ci_instr = self.compute_instr(dataset)

            self.linear_model = self.estimate_IPCs(self.Ci_unhalted_clk_td1, self.Ci_instr, self.Ci_unhalted_clk_td2)

        # print(self.Ci_unhalted_clk_td2)
        # print(self.Ci_unhalted_clk_td1)
        # print(self.Ci_instr)
        # print(self.linear_model)

        self.Ci_instr_max = self.compute_instr_max(self.linear_model)
        self.Ci_productivity = self.compute_productivity(self.Ci_instr, self.Ci_instr_max)
        self.Sys_mean_productivity = self.compute_sys_mean_productivity(self.Ci_productivity)

        # print(self.Ci_instr_max)
        # print(self.Ci_productivity)
        # print(self.Sys_mean_productivity)

        self.Ci_real_IPCs = self.compute_real_IPCs(dataset, bac.START_RUN, bac.END_RUN)
        self.Sys_mean_real_IPC = self.compute_sys_mean_real_IPC(self.Ci_real_IPCs)
        self.Sys_mean_estimated_IPC = self.compute_sys_mean_estimated_IPC(self.linear_model)

        # print(Ci_max_IPC_td_max)
        # print(Sys_max_IPC_td_max)
        # print(Sys_mean_estimated_IPC)

        if not self.my_sut_config.CPU_HT_ACTIVE: # Hyperthreading OFF
            self.Ci_atd = self.compute_atd(dataset, self.Ci_unhalted_clk_td1)
        else : # Hyperthreading ON
            self.Ci_atd = self.compute_atd(dataset, self.Ci_unhalted_clk_td1, self.Ci_unhalted_clk_td2)

        self.Sys_mean_atd = self.compute_sys_mean_atd(self.Ci_atd)

        # print(Ci_atd)
        # print(Sys_mean_atd)

        self.Ci_cbt = self.compute_core_busy_time(dataset)
        self.Sys_mean_cbt = self.compute_sys_mean_core_busy_time(self.Ci_cbt)
        self.Sys_mean_utilization = self.compute_sys_mean_utilization(dataset)

        # print(Ci_cbt)
        # print(self.Sys_mean_cbt)
        # print(self.Sys_mean_utilization)

        self.Ci_active_frequency = self.compute_mean_active_frequencies(dataset)
        self.Sys_mean_active_frequency = self.compute_sys_mean_active_frequency(self.Ci_active_frequency)

        # Export csv file with plotted data
        self.gen_csv(dataset, self.linear_model, self.Ci_real_IPCs,
                     self.Ci_instr, self.Ci_instr_max,
                     self.Sys_mean_productivity, self.Sys_mean_atd, self.Sys_mean_cbt, self.Sys_mean_utilization,
                     self.Sys_mean_active_frequency, self.Sys_mean_real_IPC, self.Sys_mean_estimated_IPC)

        return self # In order to chain estimate() with class constructor

    # For each Socket and for each Core i in Socket, calculate Ci_unhalted_clk_td2
    def compute_unhalted_clk_td2(self, dataset):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_td2 = pd.Series()

                for j in self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_td2) == 0:
                        tmp_td2 = tmp_td2.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_thread'])
                    else:
                        tmp_td2 = tmp_td2.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_thread'])

                # Calculate Ci_unhalted_clk_td2 using unhalted clocks of the first logical core of cpu c
                result['S' + str(s) + '-C' + str(c)]  = tmp_td2.sub(dataset['perf-stats']['mean']['CPU' + str(self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])
        return result

    # For each Socket and for each Core i in Socket, calculate Ci_unhalted_clk_td1
    def compute_unhalted_clk_td1(self, dataset, Ci_unhalted_clk_td2=None):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_td1 = dataset['perf-stats']['mean']['CPU' + str(self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'].copy()

                if Ci_unhalted_clk_td2 == None:
                    result['S' + str(s) + '-C' + str(c)] = tmp_td1
                else:
                    result['S' + str(s) + '-C' + str(c)] = tmp_td1.sub(Ci_unhalted_clk_td2['S' + str(s) + '-C' + str(c)])
        return result

    # For each Socket and for each Core i in Socket, calculate Ci_instr
    def compute_instr(self, dataset):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_instr = pd.Series()

                for j in self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_instr) == 0:
                        tmp_instr = tmp_instr.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_instructions'])
                    else:
                        tmp_instr = tmp_instr.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_instructions'])

                result['S' + str(s) + '-C' + str(c)]  = tmp_instr.copy()
        return result

    # For each Socket and for each Core i in Socket, compute IPC_td1 and IPC_td2 with Multivariate Linear Regression
    def estimate_IPCs(self, Ci_unhalted_clk_td1, Ci_instr, Ci_unhalted_clk_td2=None):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                # y = one element per row [Ci_istr], getting only the first NUM_SAMPLES elements for each NUM_RUNS
                y = Ci_instr['S' + str(s) + '-C' + str(c)].reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1)

                if Ci_unhalted_clk_td2 == None:
                    # Reshape to get only the first NUM_SAMPLES elements
                    clk_td1_column = Ci_unhalted_clk_td1['S' + str(s) + '-C' + str(c)].reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1)

                    X = [i for i in clk_td1_column]
                else:
                    # Reshape to get only the first NUM_SAMPLES elements
                    clk_td1_column = Ci_unhalted_clk_td1['S' + str(s) + '-C' + str(c)].reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1)
                    clk_td2_column = Ci_unhalted_clk_td2['S' + str(s) + '-C' + str(c)].reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1)

                    # X = two elems per row [Ci_unhalted_clk_td1, Ci_unhalted_clk_td2]
                    X = np.column_stack((clk_td1_column, clk_td2_column))

                regr = lm.LinearRegression(fit_intercept=False) # fit_intercept=False is equivalent to "+ 0" in R
                regr.fit(X, y)
                result['S' + str(s) + '-C' + str(c)] = {'model' : regr, 'coefficients': regr.coef_}
                # print(regr.coef_)
        return result

    # For each Socket and for each Core i in Socket, compute Ci_instr_max at td1 and td2
    def compute_instr_max(self, linear_model):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                result['S' + str(s) + '-C' + str(c)] = self.my_sut_config.CPU_MAX_FREQUENCY_ALL_CORES_BUSY * linear_model['S' + str(s) + '-C' + str(c)]['coefficients']

        return result

    # For each Socket and for each Core i in Socket, compute Productivity as Ci_instr / Ci_instr_max during each time interval
    # If Hyperthreading ON, compute Productivity w.r.t. td2
    # If Hyperthreading OFF, compute Productivity w.r.t. td1
    def compute_productivity(self, Ci_instr, Ci_instr_max):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                result['S' + str(s) + '-C' + str(c)] = Ci_instr['S' + str(s) + '-C' + str(c)] / Ci_instr_max['S' + str(s) + '-C' + str(c)][0][self.my_sut_config.CPU_HT_ACTIVE]

        return result

    # Compute the system global mean of Ci_productivity
    def compute_sys_mean_productivity(self, Ci_productivity):
        result = pd.Series(name='Sys_mean_productivity')
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_productivity['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_productivity['S' + str(s) + '-C' + str(c)])

        result = result / self.my_sut_config.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_productivity"
        return result

    # Compute Average Thread Density
    # Ci_atd = Ci_unhalted_clk_td1 / cpu_clk_unhalted_thread_any + 2 * Ci_unhalted_clk_td2 / cpu_clk_unhalted_thread_any
    def compute_atd(self, dataset, Ci_unhalted_clk_td1, Ci_unhalted_clk_td2=None):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_atd = Ci_unhalted_clk_td1['S' + str(s) + '-C' + str(c)].copy()
                # Calculate using unhalted clocks of the first logical core of cpu c
                tmp_atd = tmp_atd.div(dataset['perf-stats']['mean']['CPU' + str(self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])

                if Ci_unhalted_clk_td2 != None:
                    tmp_td2 = Ci_unhalted_clk_td2['S' + str(s) + '-C' + str(c)].div(dataset['perf-stats']['mean']['CPU' + str(self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any']) \
                        .multiply(2)
                    tmp_atd = tmp_atd.add(tmp_td2)

                result['S' + str(s) + '-C' + str(c)] = tmp_atd

        return result

    # Compute the system global mean of Ci_atd
    def compute_sys_mean_atd(self, Ci_atd):
        result = pd.Series(name='Sys_mean_atd')
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_atd['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_atd['S' + str(s) + '-C' + str(c)])

        result = result / self.my_sut_config.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_atd"
        return result

    # Compute the core busy time (C0 state residency)
    # Ci_cbt = cpu_clk_unhalted.ref_tsc / CPU_BASE_OPERATING_FREQUENCY (that is TSC)
    def compute_core_busy_time(self, dataset):
        result = {}
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_ref_tsc = pd.Series()

                for j in self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_ref_tsc) == 0:
                        tmp_ref_tsc = tmp_ref_tsc.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_ref_tsc'])
                    else:
                        tmp_ref_tsc = tmp_ref_tsc.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_ref_tsc'])

                tmp_ref_tsc = tmp_ref_tsc.div(self.my_sut_config.CPU_THREADS_PER_CORE)
                result['S' + str(s) + '-C' + str(c)] = tmp_ref_tsc.div(self.my_sut_config.CPU_BASE_OPERATING_FREQUENCY)
        return result

    # Compute the system global mean of Ci_cbt
    def compute_sys_mean_core_busy_time(self, Ci_cbt):
        result = pd.Series(name='Sys_mean_cbt')
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_cbt['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_cbt['S' + str(s) + '-C' + str(c)])

        result = result / self.my_sut_config.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_cbt"
        return result

    def compute_sys_mean_utilization(self, dataset):
        result = pd.Series(name='Sys_mean_utilization')

        result = result.append(dataset['sar-stats']['mean']['User'])
        result = result.add(dataset['sar-stats']['mean']['Nice'])
        result = result.add(dataset['sar-stats']['mean']['System'])

        result.name = "Sys_mean_utilization"
        return result

    # For each Socket and for each Core i in Socket, calculate real IPC depending on the specified runs
    # Notice this is IPC relative to physical cores, hence it's computed as:
    # sum of instr_logical_cores divided by unhalted_clk_cycles_any of first logical core of physical cpu c
    def compute_real_IPCs(self, dataset, startRun, endRun):
        startRun = startRun - 1

        result = {}

        # Compute and sort positions to be changed
        positions = [i + 10 * times for i in range(startRun, endRun) for times in range(bac.NUM_TESTS)]
        positions.sort()

        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                result['S' + str(s) + '-C' + str(c)] = pd.Series([0 for i in range(len(dataset['perf-stats']['mean']))], dtype=float) # Set all to zero

                for i in positions:
                    for j in self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                     result['S' + str(s) + '-C' + str(c)][i] = result['S' + str(s) + '-C' + str(c)][i] + dataset['perf-stats']['mean']['CPU' + str(j) + '_instructions'][i]

                    # Calculate IPC using unhalted clocks any of the first logical core of cpu c
                    result['S' + str(s) + '-C' + str(c)][i] = result['S' + str(s) + '-C' + str(c)][i] / dataset['perf-stats']['mean']['CPU' + str(self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'][i]
        return result

    # Compute the system global mean of Ci_real_IPCs
    def compute_sys_mean_real_IPC(self, Ci_real_IPCs):
        result = pd.Series(name='Sys_mean_real_IPC')
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_real_IPCs['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_real_IPCs['S' + str(s) + '-C' + str(c)])

        result = result / self.my_sut_config.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_real_IPC"
        return result

    # Compute the system global mean of estimated IPC
    # If HT is ON then the mean uses IPC estimation at TD = 2
    # If HT is OFF then the mean uses IPC estimation at TD = 1
    def compute_sys_mean_estimated_IPC(self, linear_model):
        result = pd.Series(name='Sys_mean_estimated_IPC_TD' + str(2 if self.my_sut_config.CPU_HT_ACTIVE else 1))

        inserted = False
        index = 0

        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                if not inserted :
                    result = result.set_value(index, linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][self.my_sut_config.CPU_HT_ACTIVE])
                    inserted = True
                else:
                    result[index] = result[index] + linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][self.my_sut_config.CPU_HT_ACTIVE]
            index += 1
            inserted = False

        result = result / self.my_sut_config.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_estimated_IPC_TD" + str(2 if self.my_sut_config.CPU_HT_ACTIVE else 1)
        return result

    # Compute the mean active frequencies for each core
    # frequency = (cpu_clk_unhalted_thread / cpu_clk_unhalted.ref_tsc) * CPU_BASE_OPERATING_FREQUENCY
    def compute_mean_active_frequencies(self, dataset):
        result = {}

        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_freq = pd.Series()
                tmp_ref_tsc = pd.Series()

                for j in self.my_sut_config.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_freq) == 0 and len(tmp_ref_tsc) == 0:
                        tmp_freq = tmp_freq.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_thread'])
                        tmp_ref_tsc = tmp_ref_tsc.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_ref_tsc'])
                    else:
                        tmp_freq = tmp_freq.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_thread'])
                        tmp_ref_tsc = tmp_ref_tsc.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_ref_tsc'])

                # Divide by number of threads per core
                tmp_freq = tmp_freq.div(self.my_sut_config.CPU_THREADS_PER_CORE)
                tmp_ref_tsc = tmp_ref_tsc.div(self.my_sut_config.CPU_THREADS_PER_CORE)

                result['S' + str(s) + '-C' + str(c)] = tmp_freq.div(tmp_ref_tsc).multiply(self.my_sut_config.CPU_BASE_OPERATING_FREQUENCY)

        return result

    # Compute the system global mean active frequency
    def compute_sys_mean_active_frequency(self, Ci_active_frequency):
        result = pd.Series(name='Sys_mean_AFREQ')
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_active_frequency['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_active_frequency['S' + str(s) + '-C' + str(c)])

        result = result / self.my_sut_config.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_AFREQ"

        return result

    # Generate csv file with graph data
    def gen_csv(self, dataset, linear_model, Ci_max_IPC_td_max, Ci_instr, Ci_instr_max, *args):
        df = pd.DataFrame()
        df = df.append(dataset['runs']['TotClients'])
        df = df.append(dataset['runs']['XavgTot'])
        df = df.append(dataset['runs']['UavgTot'])
        df = df.append(dataset['runs']['RavgTot'])

        for i in args:
            df = df.append(i) # Each Pandas Series must have a name setted! e.g. result.name = "myname"

        df = df.T

        # After the transposition, add columns
        # Print estimated IPC and computed real IPC
        for s in range(self.my_sut_config.CPU_SOCKETS):
            for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
                df['S' + str(s) + '-C' + str(c) + '-EST-IPC-TD1'] = linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][0]

                if self.my_sut_config.CPU_HT_ACTIVE: # Hyperthreading ON
                    df['S' + str(s) + '-C' + str(c) + '-EST-IPC-TD2'] = linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][1]

                df['S' + str(s) + '-C' + str(c) + '-REAL-IPC-TD' + str(2 if self.my_sut_config.CPU_HT_ACTIVE else 1)] = Ci_max_IPC_td_max['S' + str(s) + '-C' + str(c)]

        # for s in range(self.my_sut_config.CPU_SOCKETS):
        #     for c in range(self.my_sut_config.CPU_PHYSICAL_CORES_PER_SOCKET):
        #         df['S' + str(s) + '-C' + str(c) + '-INSTRUCTIONS'] = Ci_instr['S' + str(s) + '-C' + str(c)]
        #         df['S' + str(s) + '-C' + str(c) + '-MAX-INSTRUCTIONS'] = Ci_instr_max['S' + str(s) + '-C' + str(c)]

        df.to_csv(self.output_dir + self.test_name + '/LRModel.csv', sep=';')