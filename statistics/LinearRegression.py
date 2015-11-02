from sklearn import linear_model
import  numpy as np
import matplotlib.pyplot as plt

__author__ = 'francesco'

class LinearRegression:
    def print_diag(self, y_type, x_type, y_dataframe, x_dataframe):
        if y_type == "sar":
            y = y_dataframe.User.values + y_dataframe.Nice.values + y_dataframe.System.values # Total CPU Utilization
            y_label = "Total CPU Utilization"
        elif y_type == "rubbos":
            y = y_dataframe.UavgTot.values # Total RUBBoS average Utilization
            y = y[~np.isnan(y)]
            y_label = "Total CPU Utilization"

        if x_type == "rubbos":
            X = x_dataframe.XavgTot.values # Total RUBBoS average Throughput
            X = X[~np.isnan(X)]
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
        plt.legend(loc='lower right')

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