from sklearn import linear_model
import matplotlib.pyplot as plt

__author__ = 'francesco'

class LinearRegression:
     def print_diag(self, dataframe):
        x = dataframe.User.values + dataframe.Nice.values + dataframe.System.values # Total CPU Utilization
        y = dataframe.Idle.values
        x = x.reshape(len(x), 1)
        y = y.reshape(len(x), 1)

        regr = linear_model.LinearRegression()
        regr.fit(x, y)

        plt.scatter(x, y)
        plt.plot(x, regr.predict(x), 'r-', linewidth=2, label="Linear Regression")
        plt.legend(loc='lower right')
        plt.xlim(xmin=0)
        plt.ylim(ymin=0)
        plt.xlabel("Asse x")
        plt.ylabel("Asse y")
        #plt.xticks(())
        #plt.yticks(())
        plt.show()