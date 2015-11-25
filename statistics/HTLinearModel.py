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

        Ci_atd = {}
        Sys_mean_atd = {}

        if sut.CPU_HT_ACTIVE == 0 : # Hyperthreading OFF
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
        Ci_productivity = self.compute_productivity(Ci_instr, Ci_instr_max, sut.CPU_HT_ACTIVE)
        Sys_mean_productivity = self.compute_sys_mean_productivity(Ci_productivity)

        # print(linear_model['S0-C0'])
        # print(Ci_instr_max['S0-C0'])
        # print(Ci_productivity)
        # print(Sys_mean_productivity)

        Ci_atd = self.compute_atd(dataset, Ci_td1, Ci_td2)
        Sys_mean_atd = self.compute_sys_mean_atd(Ci_atd)

        # print(Ci_atd)
        # print(Sys_mean_atd)

        # Linear Regression parameters
        num_samples = 4 # Number of the first runs to use in the Linear Regression (e.g. first 4 over 10)
        num_runs = 10 # Number of runs in one test

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        X_line = [[i] for i in range(0, 1600)] # Used to plot streched estimated line
        ax1.axhline(y=100, c="yellow", linestyle='--', linewidth=2) # Plot dashed yellow line to show 100 limit

        # Plot X vs Productivity
        X = dataset['runs']['XavgTot']
        X = X.reshape(len(X), 1)

        X_lr = X.reshape(-1, num_runs)[:,:num_samples].reshape(-1, 1) # Samples used to estimate the Linear Regression

        y = Sys_mean_productivity * 100
        y = y.reshape(len(y), 1)

        y_lr = y.reshape(-1, num_runs)[:,:num_samples].reshape(-1, 1) # Samples used to estimate the Linear Regression

        regr = lm.LinearRegression()
        regr.fit(X_lr, y_lr)

        ax1.scatter(X, y, color='blue')
        plot1 = ax1.plot(X_line, regr.predict(X_line), linewidth=2, label="C0 Productivity\n" +
                                                                          "R^2: " + str(regr.score(X, y)) + "\n"
                                                                          "MAE: " + str(mae(y, regr.predict(X))))

        # Plot X vs U
        y = dataset['runs']['UavgTot']
        y = y.reshape(len(y), 1)

        y_lr = y.reshape(-1, num_runs)[:,:num_samples].reshape(-1, 1) # Samples used to estimate the Linear Regression

        regr = lm.LinearRegression()
        regr.fit(X_lr, y_lr)

        ax1.scatter(X, y, color='green')
        plot2 = ax1.plot(X_line, regr.predict(X_line), linewidth=2, label="Tot Avg Utilization\n" +
                                                                          "R^2: " + str(regr.score(X, y)) + "\n"
                                                                          "MAE: " + str(mae(y, regr.predict(X))))

        # Plot X vs R
        y = dataset['runs']['RavgTot']
        y = y.reshape(len(y), 1)

        plot3 = ax2.scatter(X, y, color='red')

        # Set plot title and labels
        plt.title(sut.TEST_NAME + '\nLinear Regressions considering first ' + str(num_samples) + ' samples')
        ax1.set_xlabel('Throughput')
        ax1.set_ylabel('Utilization')
        ax2.set_ylabel('Response Time')

        # Set plot legend
        plots = plot1 + plot2
        labels = [p.get_label() for p in plots]
        lgd = ax1.legend(plots + [plot3], labels + ['Tot Avg Response Time'], scatterpoints=1, loc='upper center', bbox_to_anchor=(0.5,-0.1))

        # Set axes limits
        ax1.set_xlim(xmin=0)
        ax1.set_ylim(ymin=0)
        # ax1.set_ylim(ymin=0, ymax=100)
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
        return result

    # For each Socket and for each Core i in Socket, compute Ci_instr_max at td1 and td2
    def compute_instr_max(self, linear_model):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                result['S' + str(s) + '-C' + str(c)] = sut.CPU_NOMINAL_FREQUENCY * linear_model['S' + str(s) + '-C' + str(c)]['coefficients']
        return result

    # For each Socket and for each Core i in Socket, compute Productivity as Ci_instr / Ci_instr_max during each time interval
    def compute_productivity(self, Ci_instr, Ci_instr_max, HT):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if HT == 1: # Hyperthreading ON, compute Productivity w.r.t. td2
                    result['S' + str(s) + '-C' + str(c)] = Ci_instr['S' + str(s) + '-C' + str(c)] / Ci_instr_max['S' + str(s) + '-C' + str(c)][0][1]
                else: # Hyperthreading OFF, compute Productivity w.r.t. td1
                    result['S' + str(s) + '-C' + str(c)] = Ci_instr['S' + str(s) + '-C' + str(c)] / Ci_instr_max['S' + str(s) + '-C' + str(c)][0][0]
        return result

    # Compute the system global mean of Ci_productivity
    def compute_sys_mean_productivity(self, Ci_productivity):
        result = pd.Series()
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_productivity['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_productivity['S' + str(s) + '-C' + str(c)])

        result = result / sut.CPU_PHYSICAL_CORES
        return result

    # Compute Average Thread Density
    # Ci_td1 / cpu_clk_unhalted_thread_any + 2 * Ci_td2 / cpu_clk_unhalted_thread_any
    def compute_atd(self, dataset, Ci_td1, Ci_td2=None):
        result = {}
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                tmp_atd = Ci_td1['S' + str(s) + '-C' + str(c)].copy()
                # Calculate using unhalted clocks of the first logical core of cpu c
                tmp_atd = tmp_atd.div(dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])

                tmp_td2 = Ci_td2['S' + str(s) + '-C' + str(c)].div(dataset['perf-stats']['mean']['CPU' + str(sut.CPU_PHYSICAL_TO_LOGICAL_CORES_MAPPING['CPU' + str(c)][0]) + '_cpu_clk_unhalted_thread_any'])\
                                                                .multiply(2)
                tmp_atd = tmp_atd.add(tmp_td2)

                result['S' + str(s) + '-C' + str(c)] = tmp_atd

        return result

    # Compute the system global mean of Ci_atd
    def compute_sys_mean_atd(self, Ci_atd):
        result = pd.Series()
        for s in range(sut.CPU_SOCKETS):
            for c in range(sut.CPU_PHYSICAL_CORES_PER_SOCKET):
                if len(result) == 0:
                    result = result.append(Ci_atd['S' + str(s) + '-C' + str(c)])
                else:
                    result = result.add(Ci_atd['S' + str(s) + '-C' + str(c)])

        result = result / sut.CPU_PHYSICAL_CORES
        return result

    # Generate csv file with graph data
    def gen_csv(self):
        return 'asd'