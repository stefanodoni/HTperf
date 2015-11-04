from sklearn import linear_model
import numpy as np
import matplotlib.pyplot as plt

__author__ = 'francesco'

class LinearRegression:
    def print_diag(self, y_type, x_type, dataset):
        if y_type == "U":
            myarr = np.empty(shape=(1,len(dataset)))
            for i in range(len(dataset)):
                myarr[0][i] = dataset[i]['run'].UavgTot # Total RUBBoS average Utilization
            y = myarr[0]
            y_label = "Total CPU Utilization"
        elif y_type == "R":
            myarr = np.empty(shape=(1,len(dataset)))
            for i in range(len(dataset)):
                myarr[0][i] = dataset[i]['run'].RavgTot # Total RUBBoS average Response Time
            y = myarr[0]
            y_label = "Total average Response Time"
        elif y_type == "IPC":
            myarr = np.empty(shape=(1,len(dataset)))
            for i in range(len(dataset)):
                myarr[0][i] = dataset[i]['mean'].SysIPC # Mean PCM SysIPC
            y = myarr[0]
            y_label = "Average System IPC"

        if x_type == "X":
            myarr = np.empty(shape=(1,len(dataset)))
            for i in range(len(dataset)):
                myarr[0][i] = dataset[i]['run'].XavgTot # Total RUBBoS average Throughput
            X = myarr[0]
            X_label = "Total average Throughput"

        # Reshape in order to have (length, 1) shape elements needed to use fitting
        X = X.reshape(len(X), 1)
        y = y.reshape(len(y), 1)

        regr = linear_model.LinearRegression()
        regr.fit(X, y)

        plt.scatter(X, y)
        plt.plot(X, regr.predict(X), 'r-', linewidth=2, label="Linear Regression")

        plt.title('Titolo')
        plt.xlabel(X_label)
        plt.ylabel(y_label)
        plt.legend(loc='upper left')

        #plt.axes([0, 1500, 0, 100]) # Genera dei problemi
        plt.xlim(xmin=0)
        plt.ylim(ymin=0)
        #plt.xticks(X[:10])
        #plt.yticks(y[:10])
        plt.show()

        # Alternativa della linear regression con Scipy
        # w = np.linalg.lstsq(X[:5], y[:5])
        # line = w[0]*X
        # plt.plot(X, line, 'r-',X,y,'o')
        # plt.show()