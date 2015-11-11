from sklearn import linear_model
from sklearn.metrics import r2_score
import numpy as np
import matplotlib.pyplot as plt

__author__ = 'francesco'

class LinearRegression:
    run_labels = {
        'XavgTot' : 'Total average Throughput',
        'UavgTot' : 'Total CPU Utilization',
        'RavgTot' : 'Total average Response Time'
    }

    pcm_labels = {
        # 'SysEXEC' : 'Average System EXEC',
        'SysIPC' : 'Average System IPC',
        'SysFREQ' : 'Average System FREQ',
        'SysAFREQ' : 'Average System AFREQ',
        'SysINST' : 'Average System INST',
        # 'SysACYC' : 'Average System ACYC',
        # 'SysTIMEticks' : 'Average System TIME ticks',
        'SysPhysIPC' : 'Average System PhysIPC',
        'SysPhysIPCPerc' : 'Average System PhysIPC %',
        'SysINSTnom' : 'Average System INSTnom',
        'SysINSTnomPerc' : 'Average System INSTnom %'
    }

    def print_diag(self, y_type, y_metric, x_type, x_metric,  dataset):

        # np.ndarray to keep y and X data
        myarr = np.empty(shape=(2,len(dataset)))

        # Get X axis data
        for i in range(len(dataset)):
            myarr[1][i] = dataset[i][x_type][x_metric]
        X = myarr[1]
        X_label = self.run_labels[x_metric]

        for label in self.pcm_labels:
            y_metric = label

            # Get y axis data
            for i in range(len(dataset)):
                myarr[0][i] = dataset[i][y_type][y_metric]
            y = myarr[0]
            y_label = self.pcm_labels[y_metric]

            # Reshape in order to have (length, 1) shape elements needed to use fitting
            X = X.reshape(len(X), 1)
            y = y.reshape(len(y), 1)

            regr = linear_model.LinearRegression()
            regr.fit(X, y)

            plt.scatter(X, y)
            plt.plot(X, regr.predict(X), linewidth=2, label=y_metric + " Linear Regression")

            # Print R^2
            print(y_metric + " R^2: " + str(r2_score(y, regr.predict(X))))

        plt.title('Titolo')
        plt.xlabel(X_label)
        plt.ylabel('y Axis')
        #plt.ylabel(y_label)
        plt.legend(loc='upper right')

        plt.xlim(xmin=0)
        plt.ylim(ymin=0)
        plt.show()

        # Alternativa della linear regression con Scipy
        # w = np.linalg.lstsq(X[:5], y[:5])
        # line = w[0]*X
        # plt.plot(X, line, 'r-',X,y,'o')
        # plt.show()