from sklearn.metrics import mean_absolute_error as mae
import matplotlib.pyplot as plt
import pylab
import config.BenchmarkAnalysisConfig as bac
from sklearn import linear_model as lm
import numpy as np

__author__ = 'francesco'

class HTModelPlotter:
    output_dir = ''
    fig, axarr = None, None
    ax2 = {}
    num_subplots = 0
    secondary_axes = []
    percentual_axes = []
    x_max = 0 # Used to limit the X axis
    plots = []
    scatters = []
    scatter_labels = []

    # Initialize plots
    def init(self, output_dir, num_subplots, secondary_axes=None):
        self.output_dir = output_dir
        self.num_subplots = num_subplots
        if secondary_axes != None:
            self.secondary_axes = secondary_axes

        if self.num_subplots == 1:
            self.fig, self.axarr = plt.subplots(figsize=(8, self.num_subplots * 4))

            if secondary_axes != None:
                self.ax2[0] = self.axarr.twinx() # Secondary y axis in first subplot

            # self.axarr.axhline(y=100, c="yellow", linestyle='--', linewidth=2) # Plot dashed yellow line to show 100 limit

        else:
            self.fig, self.axarr = plt.subplots(self.num_subplots, figsize=(8, self.num_subplots * 4))

            if secondary_axes != None:
                for i in self.secondary_axes:
                    self.ax2[i] = self.axarr[i].twinx() # Secondary y axis in i-th subplot

            # self.axarr[0].axhline(y=100, c="yellow", linestyle='--', linewidth=2) # Plot dashed yellow line to show 100 limit
        return self

    # Plot scatter X_dataset vs [percentual] y_dataset on given X_axis and y_axis
    def plot_scatter(self, X_dataset, y_dataset, X_axis, y_axis, color, label=None, percentual=False, axis_percentual_scale=False):
        X = X_dataset.reshape(len(X_dataset), 1)
        self.x_max = np.amax(X) if self.x_max < np.amax(X) else self.x_max # Update the x_max with the highes X value

        if percentual:
            y = y_dataset * 100
        else:
            y = y_dataset

        y = y.reshape(len(y), 1)

        if y_axis == 1: # Use secondary y axis on X_axis
            if label != None:
                tmp_scatter = self.ax2[X_axis].scatter(X, y, color=color, label=label)
            else:
                tmp_scatter = self.ax2[X_axis].scatter(X, y, color=color)

            self.add_axis_to_percentual_list(self.ax2[X_axis], axis_percentual_scale)
        else: # Use primary y axis on X_axis
            if isinstance(self.axarr, np.ndarray):
                if label != None:
                    tmp_scatter = self.axarr[X_axis].scatter(X, y, color=color, label=label)
                else:
                    tmp_scatter = self.axarr[X_axis].scatter(X, y, color=color)

                self.add_axis_to_percentual_list(self.axarr[X_axis], axis_percentual_scale)
            else:
                if label != None:
                    tmp_scatter = self.axarr.scatter(X, y, color=color, label=label)
                else:
                    tmp_scatter = self.axarr.scatter(X, y, color=color)

                self.add_axis_to_percentual_list(self.axarr, axis_percentual_scale)

        if label != None:
            self.scatters.append(tmp_scatter)
            self.scatter_labels.append(label)

    # Standard plot X_dataset vs [percentual] y_dataset on given X_axis and y_axis
    def plot_standard(self, X_dataset, y_dataset, X_axis, y_axis, color, label=None, style='', percentual=False, axis_percentual_scale=False):
        X = X_dataset.reshape(len(X_dataset), 1)
        self.x_max = np.amax(X) if self.x_max < np.amax(X) else self.x_max # Update the x_max with the highes X value

        if percentual:
            y = y_dataset * 100
        else:
            y = y_dataset

        y = y.reshape(len(y), 1)

        if y_axis == 1: # Use secondary y axis on X_axis
            if label != None:
                tmp_plot, = self.ax2[X_axis].plot(X, y, style, color=color, label=label)
            else:
                tmp_plot, = self.ax2[X_axis].plot(X, y, style, color=color)

            self.add_axis_to_percentual_list(self.ax2[X_axis], axis_percentual_scale)
        else: # Use primary y axis on X_axis
            if isinstance(self.axarr, np.ndarray):
                if label != None:
                    tmp_plot, = self.axarr[X_axis].plot(X, y, style, color=color, label=label)
                else:
                    tmp_plot, = self.axarr[X_axis].plot(X, y, style, color=color)

                self.add_axis_to_percentual_list(self.axarr[X_axis], axis_percentual_scale)
            else:
                if label != None:
                    tmp_plot, = self.axarr.plot(X, y, style, color=color, label=label)
                else:
                    tmp_plot, = self.axarr.plot(X, y, style, color=color)

                self.add_axis_to_percentual_list(self.axarr, axis_percentual_scale)

        if label != None:
            self.plots.append(tmp_plot)

    # Plot Linear Regression of X_dataset vs [percentual] y_dataset on given X_axis and y_axis
    def plot_lin_regr(self, X_dataset, y_dataset, X_axis, y_axis, color, label, percentual=False, axis_percentual_scale=False):
        X = X_dataset.reshape(len(X_dataset), 1)
        X_lr = X.reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        X_line = [[i] for i in range(0, self.x_max + bac.X_MAX_PADDING)] # Used to plot streched estimated line

        if percentual:
            y = y_dataset * 100
        else:
            y = y_dataset

        y = y.reshape(len(y), 1)
        y_lr = y.reshape(-1, bac.NUM_RUNS)[:,:bac.NUM_SAMPLES].reshape(-1, 1) # Samples used to estimate the Linear Regression

        regr = lm.LinearRegression()
        regr.fit(X_lr, y_lr)

        if y_axis == 1: # Use secondary y axis on X_axis
            tmp_plot, = self.ax2[X_axis].plot(X_line, regr.predict(X_line), color=color, linewidth=2, label=label + "\n" +
                                                                                                             r"$R^2: " + str(regr.score(X, y)) + "$\n"
                                                                                                             r"$MAE: " + str(mae(y, regr.predict(X))) + "$")
            self.add_axis_to_percentual_list(self.ax2[X_axis], axis_percentual_scale)
        else: # Use primary y axis on X_axis
            if isinstance(self.axarr, np.ndarray):
                tmp_plot, = self.axarr[X_axis].plot(X_line, regr.predict(X_line), color=color, linewidth=2, label=label + "\n" +
                                                                                                            r"$R^2: " + str(regr.score(X, y)) + "$\n"
                                                                                                            r"$MAE: " + str(mae(y, regr.predict(X))) + "$")
                self.add_axis_to_percentual_list(self.axarr[X_axis], axis_percentual_scale)
            else:
                tmp_plot, = self.axarr.plot(X_line, regr.predict(X_line), color=color, linewidth=2, label=label + "\n" +
                                                                                                            r"$R^2: " + str(regr.score(X, y)) + "$\n"
                                                                                                            r"$MAE: " + str(mae(y, regr.predict(X))) + "$")
                self.add_axis_to_percentual_list(self.axarr, axis_percentual_scale)
        self.plots.append(tmp_plot)

    # Set plot title, labels, legend and generate graph
    def gen_graph(self, filename, title,
                  X_axis_labels, y_axis_primary_labels, y_axis_secondary_labels=None):

        params = {'text.usetex': True,
                  'text.latex.unicode': True,
                  'backend': 'ps',
                  'legend.fancybox': True,
                  'font.family': 'serif',
                  'savefig.dpi': '300',
                  'savefig.format': 'eps',
                  'path.simplify': True,
                  'ps.usedistiller': 'xpdf'}
        pylab.rcParams.update(params)

        # Set title and labels
        if isinstance(self.axarr, np.ndarray):
            self.axarr[0].set_title(title)

            for i, label in X_axis_labels.items():
                self.axarr[i].set_xlabel(label)

            for i, label in y_axis_primary_labels.items():
                self.axarr[i].set_ylabel(label)

            if y_axis_secondary_labels != None:
                for i, label in y_axis_secondary_labels.items():
                    self.ax2[i].set_ylabel(label)

            # Set plot legend
            plot_labels = [p.get_label() for p in self.plots]
            lgd = self.axarr[-1].legend(self.plots + self.scatters, plot_labels + self.scatter_labels,
                                       scatterpoints=1, loc='upper center', bbox_to_anchor=(0.5,-0.2))

            # Set axes limits
            for ax in self.axarr:
                ax.set_xlim(xmin=0, xmax=(self.x_max + bac.X_MAX_PADDING))

            if bac.LIMIT_Y_AXIS_TO_100:
                for ax in self.axarr:
                    if ax in self.percentual_axes:
                        ax.set_ylim(ymin=0, ymax=100)
                    else:
                        ax.set_ylim(ymin=0)
            else:
                for ax in self.axarr:
                    ax.set_ylim(ymin=0)

            for i, ax2 in self.ax2.items():
                ax2.set_ylim(ymin=0)
        else:
            self.axarr.set_title(title)

            for i, label in X_axis_labels.items():
                self.axarr.set_xlabel(label)

            for i, label in y_axis_primary_labels.items():
                self.axarr.set_ylabel(label)

            if y_axis_secondary_labels != None:
                for i, label in y_axis_secondary_labels.items():
                    self.ax2[i].set_ylabel(label)

            # Set plot legend
            plot_labels = [p.get_label() for p in self.plots]
            lgd = self.axarr.legend(self.plots + self.scatters, plot_labels + self.scatter_labels,
                                       scatterpoints=1, loc='upper center', bbox_to_anchor=(0.5,-0.2))

            # Set axes limits
            self.axarr.set_xlim(xmin=0, xmax=(self.x_max + bac.X_MAX_PADDING))
            if bac.LIMIT_Y_AXIS_TO_100:
                self.axarr.set_ylim(ymin=0, ymax=100)
            else:
                self.axarr.set_ylim(ymin=0)

            for i, ax2 in self.ax2.items():
                ax2.set_ylim(ymin=0)

        # Print plot to file: png, pdf, ps, eps and svg
        # with legend under the graph
        # plt.savefig(self.output_dir + filename + '.eps', format = 'eps', bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.savefig(self.output_dir + filename + '.png', format = 'png', bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.savefig(self.output_dir + filename + '.pdf', format = 'pdf', bbox_extra_artists=(lgd,), bbox_inches='tight')

        # plt.show()

    def add_axis_to_percentual_list(self, ax, axis_percentual_scale):
        if axis_percentual_scale:
            self.percentual_axes.append(ax)