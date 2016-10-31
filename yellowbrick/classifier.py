# yellowbrick.classifier
# Visualizations related to evaluating Scikit-Learn classification models
#
# Author:   Rebecca Bilbro <rbilbro@districtdatalabs.com>
# Author:   Benjamin Bengfort <bbengfort@districtdatalabs.com>
# Created:  Wed May 18 12:39:40 2016 -0400
#
# Copyright (C) 2016 District Data Labs
# For license information, see LICENSE.txt
#
# ID: classifier.py [5eee25b] benjamin@bengfort.com $

"""
Visualizations related to evaluating Scikit-Learn classification models
"""

##########################################################################
## Imports
##########################################################################

import numpy as np
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.metrics import auc, roc_auc_score, roc_curve
from sklearn.metrics import precision_recall_fscore_support

from .style.palettes import ddlheatmap
from .exceptions import YellowbrickTypeError
from .style.palettes import PALETTES as YELLOWBRICK_PALETTES
from .utils import get_model_name, isestimator, isclassifier
from .base import Visualizer, ScoreVisualizer, MultiModelMixin

##########################################################################
## Classification Visualization Base Object
##########################################################################

class ClassificationScoreVisualizer(ScoreVisualizer):

    def __init__(self, model, ax=None, **kwargs):
        """
        Check to see if model is an instance of a classifer.
        Should return an error if it isn't.
        """
        if not isclassifier(model):
            raise YellowbrickTypeError(
                "This estimator is not a classifier; try a regression or clustering score visualizer instead!"
        )

        super(ClassificationScoreVisualizer, self).__init__(model, ax=ax, **kwargs)


##########################################################################
## Classification Report
##########################################################################

class ClassificationReport(ClassificationScoreVisualizer):
    """
    Classification report that shows the precision, recall, and F1 scores
    for the model. Integrates numerical scores as well color-coded heatmap.

    """
    def __init__(self, model, ax=None, classes=None, **kwargs):
        """
        Pass in a fitted model to generate a classification report.

        Parameters
        ----------

        :param ax: the axis to plot the figure on.

        :param estimator: the Scikit-Learn estimator
            Should be an instance of a classifier, else the __init__ will
            return an error.

        :param classes: a list of class names for the legend
            If classes is None and a y value is passed to fit then the classes
            are selected from the target vector.

        :param colormap: optional string or matplotlib cmap to colorize lines
            Use sequential heatmap.

        :param kwargs: keyword arguments passed to the super class.

        These parameters can be influenced later on in the visualization
        process, but can and should be set as early as possible.
        """
        super(ClassificationReport, self).__init__(model, ax=ax, **kwargs)

        ## hoisted to Visualizer base class
        # self.ax = None

        ## hoisted to ScoreVisualizer base class
        # self.estimator = model
        # self.name = get_model_name(self.estimator)

        self.cmap = kwargs.pop('cmap', ddlheatmap)
        self.classes_ = classes

    def fit(self, X, y=None, **kwargs):
        """
        Parameters
        ----------

        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features

        y : ndarray or Series of length n
            An array or series of target or class values

        kwargs: keyword arguments passed to Scikit-Learn API.
        """
        super(ClassificationReport, self).fit(X, y, **kwargs)
        if self.classes_ is None:
            self.classes_ = self.estimator.classes_
        return self

    def score(self, X, y=None, **kwargs):
        """
        Generates the Scikit-Learn classification_report

        Parameters
        ----------

        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features

        y : ndarray or Series of length n
            An array or series of target or class values

        """
        y_pred = self.predict(X)
        keys   = ('precision', 'recall', 'f1')
        self.scores = precision_recall_fscore_support(y, y_pred)
        self.scores = map(lambda s: dict(zip(self.classes_, s)), self.scores[0:3])
        self.scores = dict(zip(keys, self.scores))
        return self.draw(y, y_pred)

    def draw(self, y, y_pred):
        """
        Renders the classification report across each axis.

        Parameters
        ----------

        y : ndarray or Series of length n
            An array or series of target or class values

        y_pred : ndarray or Series of length n
            An array or series of predicted target values
        """
        if self.ax is None:
            self.ax = plt.gca()

        self.matrix = []
        for cls in self.classes_:
            self.matrix.append([self.scores['precision'][cls],self.scores['recall'][cls],self.scores['f1'][cls]])

        for column in range(len(self.matrix)+1):
            for row in range(len(self.classes_)):
                self.ax.text(column,row,self.matrix[row][column],va='center',ha='center')

        fig = plt.imshow(self.matrix, interpolation='nearest', cmap=self.cmap, vmin=0, vmax=1)

        return self.ax


    def poof(self):
        """
        Plots a classification report as a heatmap.

        Returns
        ----------

        ax : the axis with the plotted figure

        """
        if self.ax is None: return

        self.finalize()
        plt.show()

        return self.ax


    def finalize(self, **kwargs):
        """
        Finalize executes any subclass-specific axes finalization steps.
        The user calls poof and poof calls finalize.

        Parameters
        ----------
        kwargs: generic keyword arguments.

        Returns
        ----------
        ax : the axis with the plotted figure

        """
        plt.title('{} Classification Report'.format(self.name))
        plt.colorbar()
        x_tick_marks = np.arange(len(self.classes_)+1)
        y_tick_marks = np.arange(len(self.classes_))
        plt.xticks(x_tick_marks, ['precision', 'recall', 'f1-score'], rotation=45)
        plt.yticks(y_tick_marks, self.classes_)
        plt.ylabel('Classes')
        plt.xlabel('Measures')

        return self.ax
##########################################################################
## Receiver Operating Characteristics
##########################################################################

class ROCAUC(ClassificationScoreVisualizer):
    """
    Plot the ROC to visualize the tradeoff between the classifier's
    sensitivity and specificity.
    """
    def __init__(self, model, ax=None, **kwargs):
        """
        Pass in a fitted model to generate a ROC curve.

        Parameters
        ----------

        :param ax: the axis to plot the figure on.

        :param estimator: the Scikit-Learn estimator
            Should be an instance of a classifier, else the __init__ will
            return an error.

        :param kwargs: keyword arguments passed to the super class.
            Currently passing in hard-coded colors for the Receiver Operating
            Characteristic curve and the diagonal.
            These will be refactored to a default Yellowbrick style.

        These parameters can be influenced later on in the visualization
        process, but can and should be set as early as possible.

        """
        super(ROCAUC, self).__init__(model, ax=ax, **kwargs)

        ## hoisted to Visualizer base class
        # self.ax = None

        ## hoisted to ScoreVisualizer base class
        # self.name = get_model_name(self.estimator)

        # TODO refactor to use new Yellowbrick color utils
        self.colors = {
            'roc': kwargs.pop('roc_color', '#2B94E9'),
            'diagonal': kwargs.pop('diagonal_color', '#666666'),
        }

    def score(self, X, y=None, **kwargs):
        """
        Generates the predicted target values using the Scikit-Learn
        estimator.

        Parameters
        ----------

        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features

        y : ndarray or Series of length n
            An array or series of target or class values

        Returns
        ------

        ax : the axis with the plotted figure

        """
        y_pred = self.predict(X)
        self.fpr, self.tpr, self.thresholds = roc_curve(y, y_pred)
        self.roc_auc = auc(self.fpr, self.tpr)
        return self.draw(y, y_pred)

    def draw(self, y, y_pred):
        """
        Renders ROC-AUC plot.
        Called internally by score, possibly more than once

        Parameters
        ----------

        y : ndarray or Series of length n
            An array or series of target or class values

        y_pred : ndarray or Series of length n
            An array or series of predicted target values

        Returns
        ------

        ax : the axis with the plotted figure

        """
        if self.ax is None:
            self.ax = plt.gca()
        plt.plot(self.fpr, self.tpr, c=self.colors['roc'], label='AUC = {:0.2f}'.format(self.roc_auc))

        # Plot the line of no discrimination to compare the curve to.
        plt.plot([0,1],[0,1],'m--',c=self.colors['diagonal'])

        return self.ax

    def poof(self, **kwargs):
        """
        Called by user. Take in the model as input and generates a plot of
        the ROC plots with AUC metrics embedded.

        Returns
        ------

        ax : the axis with the plotted figure

        """
        if self.ax is None: return

        plt.title('ROC for {}'.format(self.name))
        plt.legend(loc='lower right')

        plt.xlim([-0.02,1])
        plt.ylim([0,1.1])

        plt.show()

        return self.ax


##########################################################################
## Class Balance Chart
##########################################################################

class ClassBalance(ClassificationScoreVisualizer):
    """
    Class balance chart that shows the support for each class in the
    fitted classification model displayed as a bar plot.
    """
    def __init__(self, model, ax=None, classes=None, **kwargs):
        """
        Pass in a fitted model to generate a class balance chart.

        Parameters
        ----------

        :param ax: the axis to plot the figure on.

        :param estimator: the Scikit-Learn estimator
            Should be an instance of a classifier, else the __init__ will
            return an error.

        :param classes: a list of class names for the legend
            If classes is None and a y value is passed to fit then the classes
            are selected from the target vector.

        :param kwargs: keyword arguments passed to the super class. Here, used
            to colorize the bars in the histogram.

        These parameters can be influenced later on in the visualization
        process, but can and should be set as early as possible.

        """
        super(ClassBalance, self).__init__(model, ax=ax, **kwargs)

        ## hoisted to Visualizer base class
        # self.ax = None

        ## hoisted to ScoreVisualizer base class
        # self.estimator = model
        # self.name      = get_model_name(self.estimator)

        self.colors    = kwargs.pop('colors', YELLOWBRICK_PALETTES['paired'])
        self.classes_  = classes

    def fit(self, X, y=None, **kwargs):
        """
        Parameters
        ----------

        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features

        y : ndarray or Series of length n
            An array or series of target or class values

        kwargs: keyword arguments passed to Scikit-Learn API.

        Returns
        ------
        self : instance
            Returns the instance of the classification score visualizer

        """
        super(ClassBalance, self).fit(X, y, **kwargs)
        if self.classes_ is None:
            self.classes_ = self.estimator.classes_
        return self

    def score(self, X, y=None, **kwargs):
        """
        Generates the Scikit-Learn precision_recall_fscore_support

        Parameters
        ----------

        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features

        y : ndarray or Series of length n
            An array or series of target or class values

        Returns
        ------

        ax : the axis with the plotted figure
        """
        y_pred = self.predict(X)
        self.scores  = precision_recall_fscore_support(y, y_pred)
        self.support = dict(zip(self.classes_, self.scores[-1]))
        return self.draw()

    def draw(self):
        """
        Renders the class balance chart across the axis.

        Returns
        ------

        ax : the axis with the plotted figure

        """
        if self.ax is None:
            self.ax = plt.gca()

        #TODO: Would rather not have to set the colors with this method.
        # Refactor to make better use of yb_palettes module?

        colors = self.colors[0:len(self.classes_)]
        plt.bar(np.arange(len(self.support)), self.support.values(), color=colors, align='center', width=0.5)

        return self.ax

    def poof(self):
        """
        Plots a class balance chart

        Returns
        ------

        ax : the axis with the plotted figure
        """
        if self.ax is None: return

        plt.xticks(np.arange(len(self.support)), self.support.keys())
        cmax, cmin = max(self.support.values()), min(self.support.values())
        ceiling = cmax + cmax*0.1
        span = cmax - cmin
        plt.ylim(0, ceiling)

        plt.show()

        return self.ax
