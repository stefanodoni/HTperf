from sklearn import linear_model
import  numpy as np
import matplotlib.pyplot as plt

__author__ = 'francesco'

class RANSACRegressor:
    def print_diag(self, y_type, x_type, y_dataframe, x_dataframe):
        if y_type == "sar":
            y = y_dataframe.User.values + y_dataframe.Nice.values + y_dataframe.System.values # Total CPU Utilization
            y_label = "Total CPU Utilization"
        elif y_type == "rubbos":
            y = y_dataframe.RavgTot.values # Total RUBBoS average Utilization
            y = y[~np.isnan(y)]
            y_label = "Total CPU R"

        if x_type == "rubbos":
            X = x_dataframe.XavgTot.values # Total RUBBoS average Throughput
            X = X[~np.isnan(X)]
            X_label = "Total average Throughput"

        X = X.reshape(len(X), 1)
        y = y.reshape(len(y), 1)

        regr = linear_model.LinearRegression()
        regr.fit(X, y)

        # Robustly fit linear model with RANSAC algorithm
        model_ransac = linear_model.RANSACRegressor(linear_model.LinearRegression())
        model_ransac.fit(X, y)
        inlier_mask = model_ransac.inlier_mask_
        outlier_mask = np.logical_not(inlier_mask)

        # Predict data of estimated models
        line_X = np.arange(-5, 5)
        line_y = regr.predict(line_X[:, np.newaxis])
        line_y_ransac = model_ransac.predict(line_X[:, np.newaxis])

        plt.plot(X[inlier_mask], y[inlier_mask], '.g', label='Inliers')
        plt.plot(X[outlier_mask], y[outlier_mask], '.r', label='Outliers')
        plt.plot(X, regr.predict(X), 'r-', linewidth=2, label="Linear Regression")
        plt.plot(X, model_ransac.predict(X), '-b', label='RANSAC regressor')
        plt.legend(loc='upper left')
        plt.xlabel(X_label)
        plt.ylabel(y_label)
        plt.show()
