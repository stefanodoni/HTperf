import datetime as dt
import pandas as pd
import numpy as np
from sklearn import linear_model
import matplotlib.pyplot as plt
from Parser import Parser

__author__ = 'francesco'

class SarParser (Parser):
    valore = 0
    columns = ['Host', 'Interval', 'Timestamp', 'CPU', 'User', 'Nice', 'System', 'Iowait', 'Steal', 'Idle']

    #def __init__(self):
        #Parser.__init__(self)
        #print("init sarParser")

    def hello(self):
        print("sono figlio")
        #print("{} sono figlio").format(valore)

    def parse(self, file):
        csvfile = open(file, 'rb')
        dataset = pd.read_csv(csvfile, sep=';', header=None, decimal=',') #DataFrame obj
        dataset.columns = self.columns

        dataset['Timestamp'] = dataset['Timestamp'].apply(pd.to_datetime)
        #print(dataset.dtypes)

        return dataset

    def printDiag(self, dataset):
        x = dataset.User.values + dataset.Nice.values + dataset.System.values # Total CPU Utilization
        y = dataset.Idle.values # TODO
        x = x.reshape(len(x), 1)
        y = y.reshape(len(x), 1)

        regr = linear_model.LinearRegression()
        regr.fit(x, y)

        # plot it as in the example at http://scikit-learn.org/
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