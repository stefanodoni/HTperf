from sklearn.metrics import mean_absolute_error as mae
import matplotlib.pyplot as plt
import config.BenchmarkAnalysisConfig as bac
from sklearn import linear_model as lm

__author__ = 'francesco'

class HTModelPlotter:
    output_dir = ''
    fig, axarr, ax2 = None, None, None
    X_line = [[i] for i in range(0, bac.MAX_THROUGHPUT)] # Used to plot streched estimated line
    plots = []
    scatters = []
    scatter_labels = []

    def init(self, output_dir):
        self.output_dir = output_dir

        # Initialize plots
        self.fig, self.axarr = plt.subplots(2, figsize=(8,8), sharex=True)
        self.ax2 = self.axarr[0].twinx() # Secondary y axis in first subplot

        self.axarr[0].axhline(y=100, c="yellow", linestyle='--', linewidth=2) # Plot dashed yellow line to show 100 limit

        return self

    # Plot Linear Regression of X_dataset vs [percentual] y_dataset on given X_axis and y_axis
    def plot_lin_regr(self, X_dataset, y_dataset, X_axis, y_axis, color, label, percentual=False):
        X = X_dataset.reshape(len(X_dataset), 1)
        X_lr = X.reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        if percentual:
            y = y_dataset * 100
        else:
            y = y_dataset

        y = y.reshape(len(y), 1)
        y_lr = y.reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        regr = lm.LinearRegression()
        regr.fit(X_lr, y_lr)

        if y_axis == 1: # Use secondary y axis on primary X axis
            tmp_plot, = self.ax2.plot(self.X_line, regr.predict(self.X_line), color=color, linewidth=2, label=label + "\n" +
                                                                                                             "R^2: " + str(regr.score(X, y)) + "\n"
                                                                                                                                               "MAE: " + str(mae(y, regr.predict(X))))
        else: # Use primary y axis on X_axis
            tmp_plot, = self.axarr[X_axis].plot(self.X_line, regr.predict(self.X_line), color=color, linewidth=2, label=label + "\n" +
                                                                                                                       "R^2: " + str(regr.score(X, y)) + "\n"
                                                                                                                                                         "MAE: " + str(mae(y, regr.predict(X))))
        self.plots.append(tmp_plot)

    # Plot scatter X_dataset vs [percentual] y_dataset on given X_axis and y_axis
    def plot_scatter(self, X_dataset, y_dataset, X_axis, y_axis, color, label, percentual=False):
        X = X_dataset.reshape(len(X_dataset), 1)

        if percentual:
            y = y_dataset * 100
        else:
            y = y_dataset

        y = y.reshape(len(y), 1)

        if y_axis == 1: # Use secondary y axis on primary X axis
            tmp_scatter = self.ax2.scatter(X, y, color=color, label=label)
        else: # Use primary y axis on X_axis
            tmp_scatter = self.axarr[X_axis].scatter(X, y, color=color, label=label)

        self.scatters.append(tmp_scatter)
        self.scatter_labels.append(label)

    # Standard plot X_dataset vs [percentual] y_dataset on given X_axis and y_axis
    def plot_standard(self, X_dataset, y_dataset, X_axis, y_axis, color, label, percentual=False, style=''):
        X = X_dataset.reshape(len(X_dataset), 1)

        if percentual:
            y = y_dataset * 100
        else:
            y = y_dataset

        y = y.reshape(len(y), 1)

        if y_axis == 1: # Use secondary y axis on primary X axis
            tmp_plot, = self.ax2.plot(X, y, style, color=color, label=label)
        else: # Use primary y axis on X_axis
            tmp_plot, = self.axarr[X_axis].plot(X, y, style, color=color, label=label)

        self.plots.append(tmp_plot)

    # Set plot title, labels, legend and generate graph
    def gen_graph(self, title, second_X_axis_label,
                  first_X_axis_primary_y_axis_label, first_X_axis_secondary_y_axis_label,
                  second_X_axis_primary_y_axis_label,
                  first_X_axis_label=None):

        # Set title and labels
        self.axarr[0].set_title(title)

        if first_X_axis_label != None:
            self.axarr[0].set_xlabel(first_X_axis_label)
        self.axarr[1].set_xlabel(second_X_axis_label)
        self.axarr[0].set_ylabel(first_X_axis_primary_y_axis_label)
        self.axarr[1].set_ylabel(second_X_axis_primary_y_axis_label)

        self.ax2.set_ylabel(first_X_axis_secondary_y_axis_label)

        # Set plot legend
        plot_labels = [p.get_label() for p in self.plots]
        lgd = self.axarr[1].legend(self.plots + self.scatters, plot_labels + self.scatter_labels, scatterpoints=1, loc='upper center', bbox_to_anchor=(0.5,-0.2))

        # Set axes limits
        self.axarr[0].set_xlim(xmin=0, xmax=bac.MAX_THROUGHPUT)
        self.axarr[0].set_ylim(ymin=0)
        # self.axarr[0].set_ylim(ymin=0, ymax=100)
        self.ax2.set_ylim(ymin=0)

        # Print plot to file: png, pdf, ps, eps and svg
        # with legend under the graph
        plt.savefig(self.output_dir + 'graph.eps', format = 'eps', bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.savefig(self.output_dir + 'graph.png', format = 'png', bbox_extra_artists=(lgd,), bbox_inches='tight')

        plt.show()