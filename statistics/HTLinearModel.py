from sklearn import linear_model as lm
from sklearn.metrics import mean_absolute_error as mae
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import config.SUTConfig as sut

__author__ = 'francesco'

class HTLinearModel:
    # Estimate multivariate linear regression model for each physical CPU and compute CPU productivity.
    # Parameters:
    #   - Ci_instr: sum of CPUi_(thread i) instructons, where i belongs to physical CPU Ci
    #   - Ci_td2 = sum of CPUi_cpu_clk_unhalted_thread - CPUi_cpu_clk_unhalted_thread_any, where i belongs to physical CPU Ci => clock cycles with Thread Density 2
    #   - Ci_td1: CPUi_cpu_clk_unhalted_thread_any - Ci_td2 => clock cycles with Thread Density 1
    #
    # Unknowns (Multivariate Linear Regression coefficients):
    #   - IPC_td1
    #   - IPC_td2 (= IPC_td1 * S, with S = Speedup w.r.t. IPC_td1)
    #
    # Equation:
    #   Ci_instr = IPC_td1 * Ci_td1 + IPC_td2 * Ci_td2
    #
    # To compute CPU productivity we need the max number of instructions with td2.
    #   - Ci_instr_max = Nominal CPU Frequency * IPC_td2
    #   - Ci_productivity = Ci_instr / Ci_instr_max
    #
    # Finally we compute Sys_mean_productivity as the global system mean of all Ci_productivity
    #
    # We can then correlate the run throughput with productivity and run utilization, plotting graphs and computing R^2

    def estimate(self, dataset):
        Ci_td1 = {}
        Ci_td2 = {}
        Ci_instr = {}

        linear_model = {}
        Ci_instr_max = {}
        Ci_productivity = {}
        Sys_mean_productivity = pd.Series()

        Ci_IPC_max_td_max = {}
        Sys_mean_IPC_td_max = pd.Series()
        Sys_mean_estimated_IPC = pd.Series()

        Ci_atd = {}
        Sys_mean_atd = {}

        Ci_cbt = {}
        Sys_mean_cbt = {}

        if not sut.CPU_HT_ACTIVE: # Hyperthreading OFF
            Ci_td1 = self.compute_td1(dataset)
            Ci_instr = self.compute_instr(dataset)

            linear_model = self.estimate_IPCs(Ci_td1, Ci_instr)
        else : # Hyperthreading ON
            Ci_td2 = self.compute_td2(dataset)
            Ci_td1 = self.compute_td1(dataset, Ci_td2)
            Ci_instr = self.compute_instr(dataset)

            linear_model = self.estimate_IPCs(Ci_td1, Ci_instr, Ci_td2)

        # print(Ci_td2['S0-C0'])
        # print(Ci_td2)
        # print(Ci_instr['S0-C0'])

        Ci_instr_max = self.compute_instr_max(linear_model)
        Ci_productivity = self.compute_productivity(Ci_instr, Ci_instr_max)
        Sys_mean_productivity = self.compute_sys_mean_productivity(Ci_productivity)

        # print(linear_model['S0-C0'])
        # print(Ci_instr_max['S0-C0'])
        # print(Ci_productivity)
        # print(Sys_mean_productivity)

        Ci_IPC_max_td_max = self.compute_IPC_at_run_with_td_max(dataset, sut.START_RUN, sut.END_RUN)
        Sys_mean_IPC_td_max = self.compute_sys_mean_IPC_at_td_max(Ci_IPC_max_td_max)
        Sys_mean_estimated_IPC = self.compute_sys_mean_estimated_IPC(linear_model)

        # print(Ci_max_IPC_td_max)
        # print(Sys_max_IPC_td_max)
        # print(Sys_mean_estimated_IPC)

        if not sut.CPU_HT_ACTIVE: # Hyperthreading OFF
            Ci_atd = self.compute_atd(dataset, Ci_td1)
        else : # Hyperthreading ON
            Ci_atd = self.compute_atd(dataset, Ci_td1, Ci_td2)

        Sys_mean_atd = self.compute_sys_mean_atd(Ci_atd)

        # print(Ci_atd)
        # print(Sys_mean_atd)

        Ci_cbt = self.compute_core_busy_time(dataset)
        Sys_mean_cbt = self.compute_sys_mean_core_busy_time(Ci_cbt)

        # print(Ci_cbt)
        # print(Sys_mean_cbt)

        # Export csv file with plotted data
        self.gen_csv(dataset, linear_model, Ci_IPC_max_td_max, Sys_mean_productivity, Sys_mean_atd, Sys_mean_cbt, Sys_mean_IPC_td_max, Sys_mean_estimated_IPC)

        # Plot results
        fig, axarr = plt.subplots(2, figsize=(8,8), sharex=True)
        ax2 = axarr[0].twinx()

        X_line = [[i] for i in range(0, 1600)] # Used to plot streched estimated line
        axarr[0].axhline(y=100, c="yellow", linestyle='--', linewidth=2) # Plot dashed yellow line to show 100 limit

        # Plot X vs Productivity on primary y axis axarr[0]
        X = dataset['runs']['XavgTot']
        X = X.reshape(len(X), 1)

        X_lr = X.reshape(-1, sut.NUM_RUNS)[:,:sut.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        y = Sys_mean_productivity * 100
        y = y.reshape(len(y), 1)

        y_lr = y.reshape(-1, sut.NUM_RUNS)[:,:sut.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        regr = lm.LinearRegression()
        regr.fit(X_lr, y_lr)

        axarr[0].scatter(X, y, color='blue')
        plot1 = axarr[0].plot(X_line, regr.predict(X_line), linewidth=2, label="C0 Productivity\n" +
                                                                          "R^2: " + str(regr.score(X, y)) + "\n"
                                                                          "MAE: " + str(mae(y, regr.predict(X))))

        # Plot X vs U on primary y axis axarr[0]
        y = dataset['runs']['UavgTot']
        y = y.reshape(len(y), 1)

        y_lr = y.reshape(-1, sut.NUM_RUNS)[:,:sut.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        regr = lm.LinearRegression()
        regr.fit(X_lr, y_lr)

        axarr[0].scatter(X, y, color='green')
        plot2 = axarr[0].plot(X_line, regr.predict(X_line), linewidth=2, label="Tot Avg Utilization\n" +
                                                                          "R^2: " + str(regr.score(X, y)) + "\n"
                                                                          "MAE: " + str(mae(y, regr.predict(X))))

        # Plot X vs Core Busy Time on primary y axis axarr[0]
        y = Sys_mean_cbt * 100
        y = y.reshape(len(y), 1)

        plot3 = axarr[0].scatter(X, y, color='black')

        # Plot X vs Avg Thread Density on primary y axis axarr[1]
        y = Sys_mean_atd
        y = y.reshape(len(y), 1)

        plot4 = axarr[1].scatter(X, y, color='violet')

        # Plot X vs R on secondary y axis ax2
        y = dataset['runs']['RavgTot']
        y = y.reshape(len(y), 1)

        plot5 = ax2.plot(X, y, '-o', color='red', label="Tot Avg Response Time")

        # Set plot title and labels
        plt.title(sut.TEST_NAME + '\nLinear Regressions considering first ' + str(sut.NUM_SAMPLES) + ' samples')
        axarr[1].set_xlabel('Throughput')
        axarr[0].set_ylabel('Utilization')
        axarr[1].set_ylabel('Tot Avg Thread Density')
        ax2.set_ylabel('Response Time')

        # Set plot legend
        plots = plot1 + plot2 + plot5
        labels = [p.get_label() for p in plots]
        lgd = axarr[1].legend(plots + [plot3] + [plot4], labels + ['Tot Avg Core Busy Time (C0 state)'] + ['Tot Avg Thread Density'], scatterpoints=1, loc='upper center', bbox_to_anchor=(0.5,-0.2))

        # Set axes limits
        axarr[0].set_xlim(xmin=0)
        axarr[0].set_ylim(ymin=0)
        # axarr[0].set_ylim(ymin=0, ymax=100)
        ax2.set_ylim(ymin=0)

        # Print plot to file: png, pdf, ps, eps and svg
        # with legend under the graph
        plt.savefig(sut.OUTPUT_DIR + sut.TEST_NAME + '.eps', format = 'eps', bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.savefig(sut.OUTPUT_DIR + sut.TEST_NAME + '.png', format = 'png', bbox_extra_artists=(lgd,), bbox_inches='tight')

        plt.show()


    # For each Socket and for each Core i in Socket, calculate Ci_td2
    def compute_td2(self, dataset):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_td2 = pd.Series()

                for j in sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_td2) == 0:
                        tmp_td2 = tmp_td2.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_thread'])
                    else:
                        tmp_td2 = tmp_td2.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_thread'])

                # Calculate Ci_td2 using unhalted clocks of the first logical core of cpu c
                result['S' + str(s) + '-C' + str(c)]  = tmp_td2.sub(dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])
        return result

    # For each Socket and for each Core i in Socket, calculate Ci_td1
    def compute_td1(self, dataset, Ci_td2=None):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_td1 = dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'].copy()

                if Ci_td2 == None:
                    result['S' + str(s) + '-C' + str(c)] = tmp_td1
                else:
                    result['S' + str(s) + '-C' + str(c)] = tmp_td1.sub(Ci_td2['S' + str(s) + '-C' + str(c)])
        return result

    # For each Socket and for each Core i in Socket, calculate Ci_instr
    def compute_instr(self, dataset):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_instr = pd.Series()

                for j in sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_instr) == 0:
                        tmp_instr = tmp_instr.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_instructions'])
                    else:
                        tmp_instr = tmp_instr.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_instructions'])

                result['S' + str(s) + '-C' + str(c)]  = tmp_instr.copy()
        return result

    # For each Socket and for each Core i in Socket, compute IPC_td1 and IPC_td2 with Multivariate Linear Regression
    def estimate_IPCs(self, Ci_td1, Ci_instr, Ci_td2=None):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                # y = one element per row [Ci_istr]
                y = np.array(Ci_instr['S' + str(s) + '-C' + str(c)])
                y = y.reshape(len(y), 1)

                if Ci_td2 == None:
                    X = [[i] for i in Ci_td1['S' + str(s) + '-C' + str(c)]]
                else:
                    # X = two elems per row [Ci_td1, Ci_td2]
                    X = [[i, j] for i, j in zip(Ci_td1['S' + str(s) + '-C' + str(c)], Ci_td2['S' + str(s) + '-C' + str(c)])]

                regr = lm.LinearRegression(fit_intercept=False) # fit_intercept=False is equivalent to "+ 0" in R
                regr.fit(X, y)
                result['S' + str(s) + '-C' + str(c)] = {'model' : regr, 'coefficients': regr.coef_}
                # print(regr.coef_)
                # print(result)
        return result

    # For each Socket and for each Core i in Socket, compute Ci_instr_max at td1 and td2
    def compute_instr_max(self, linear_model):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                # result['S' + str(s) + '-C' + str(c)] = sut.CPU_NOMINAL_FREQUENCY * linear_model['S' + str(s) + '-C' + str(c)]['coefficients']
                result['S' + str(s) + '-C' + str(c)] = sut.CPU_ACTUAL_MAX_FREQUENCY * linear_model['S' + str(s) + '-C' + str(c)]['coefficients']

        return result

    # For each Socket and for each Core i in Socket, compute Productivity as Ci_instr / Ci_instr_max during each time interval
    # If Hyperthreading ON, compute Productivity w.r.t. td2
    # If Hyperthreading OFF, compute Productivity w.r.t. td1
    def compute_productivity(self, Ci_instr, Ci_instr_max):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                result['S' + str(s) + '-C' + str(c)] = Ci_instr['S' + str(s) + '-C' + str(c)] / Ci_instr_max['S' + str(s) + '-C' + str(c)][0][sut.CPU_HT_ACTIVE]

        return result

    # Compute the system global mean of Ci_productivity
    def compute_sys_mean_productivity(self, Ci_productivity):
        result = pd.Series(name='Sys_mean_productivity')
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_productivity['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_productivity['S' + str(s) + '-C' + str(c)])

        result = result / sut.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_productivity"
        return result

    # Compute Average Thread Density
    # Ci_atd = Ci_td1 / cpu_clk_unhalted_thread_any + 2 * Ci_td2 / cpu_clk_unhalted_thread_any
    def compute_atd(self, dataset, Ci_td1, Ci_td2=None):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_atd = Ci_td1['S' + str(s) + '-C' + str(c)].copy()
                # Calculate using unhalted clocks of the first logical core of cpu c
                tmp_atd = tmp_atd.div(dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])

                if Ci_td2 != None:
                    tmp_td2 = Ci_td2['S' + str(s) + '-C' + str(c)].div(dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])\
                                                            .multiply(2)
                    tmp_atd = tmp_atd.add(tmp_td2)

                result['S' + str(s) + '-C' + str(c)] = tmp_atd

        return result

    # Compute the system global mean of Ci_atd
    def compute_sys_mean_atd(self, Ci_atd):
        result = pd.Series(name='Sys_mean_atd')
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_atd['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_atd['S' + str(s) + '-C' + str(c)])

        result = result / sut.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_atd"
        return result

    # Compute the core busy time (C0 state residency)
    # Ci_cbt = cpu_clk_unhalted.ref_tsc / CPU_NOMINAL_FREQUENCY (that is TSC ?)
    def compute_core_busy_time(self, dataset):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_ref_tsc = pd.Series()

                for j in sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                    if len(tmp_ref_tsc) == 0:
                        tmp_ref_tsc = tmp_ref_tsc.append(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_ref_tsc'])
                    else:
                        tmp_ref_tsc = tmp_ref_tsc.add(dataset['perf-stats']['mean']['CPU' + str(j) + '_cpu_clk_unhalted_ref_tsc'])

                tmp_ref_tsc = tmp_ref_tsc.div(sut.CPU_THREADS_PER_CORE)
                result['S' + str(s) + '-C' + str(c)]  = tmp_ref_tsc.div(sut.CPU_NOMINAL_FREQUENCY)
        return result

    # Compute the system global mean of Ci_cbt
    def compute_sys_mean_core_busy_time(self, Ci_cbt):
        result = pd.Series(name='Sys_mean_cbt')
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_cbt['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_cbt['S' + str(s) + '-C' + str(c)])

        result = result / sut.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_cbt"
        return result

    # For each Socket and for each Core i in Socket, calculate real IPC at TD depending on the specified run
    def compute_IPC_at_run_with_td_max(self, dataset, startRun, endRun):
        startRun = startRun - 1

        result = {}

        # Compute and sort positions to be changed
        positions = [i + 10 * times for i in range(startRun, endRun) for times in range(sut.NUM_RUNS)]
        positions.sort()

        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                result['S' + str(s) + '-C' + str(c)] = pd.Series([0 for i in range(len(dataset['perf-stats']['mean']))], dtype=float) # Set all to zero

                for i in positions:
                    for j in sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)]:
                        result['S' + str(s) + '-C' + str(c)][i] = result['S' + str(s) + '-C' + str(c)][i] + dataset['perf-stats']['mean']['CPU' + str(j) + '_instructions'][i]

                    # Calculate IPC at TD max using unhalted clocks of the first logical core of cpu c
                    result['S' + str(s) + '-C' + str(c)][i] = result['S' + str(s) + '-C' + str(c)][i] / dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread'][i]

        return result

    # Compute the system global mean of Ci_max_IPC_td_max
    def compute_sys_mean_IPC_at_td_max(self, Ci_IPC_max_td_max):
        result = pd.Series(name='Sys_mean_IPC')
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_IPC_max_td_max['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_IPC_max_td_max['S' + str(s) + '-C' + str(c)])

        result = result / sut.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_IPC"
        return result

    # Compute the system global mean of estimated IPC
    # If HT is ON then the mean uses IPC estimation at TD = 2
    # If HT is OFF then the mean uses IPC estimation at TD = 1
    def compute_sys_mean_estimated_IPC(self, linear_model):
        result = pd.Series(name='Sys_mean_estimated_IPC_TD' + str(2 if sut.CPU_HT_ACTIVE else 1))

        inserted = False
        index = 0

        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if not inserted :
                    result = result.set_value(index, linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][sut.CPU_HT_ACTIVE])
                    inserted = True
                else:
                    result[index] = result[index] + linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][sut.CPU_HT_ACTIVE]
            index += 1
            inserted = False

        result = result / sut.CPU_PHYSICAL_CORES
        result.name = "Sys_mean_estimated_IPC_TD" + str(2 if sut.CPU_HT_ACTIVE else 1)
        return result

    # Generate csv file with graph data
    def gen_csv(self, dataset, linear_model, Ci_max_IPC_td_max, *args):
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
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                df['S' + str(s) + '-C' + str(c) + '-EST-IPC-TD1'] = linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][0]

                if sut.CPU_HT_ACTIVE: # Hyperthreading ON
                    df['S' + str(s) + '-C' + str(c) + '-EST-IPC-TD2'] = linear_model['S' + str(s) + '-C' + str(c)]['coefficients'][0][1]

                df['S' + str(s) + '-C' + str(c) + '-REAL-IPC-TD' + str(2 if sut.CPU_HT_ACTIVE else 1)] = Ci_max_IPC_td_max['S' + str(s) + '-C' + str(c)]

        df.to_csv(sut.OUTPUT_DIR + 'LRModel.csv', sep=';')