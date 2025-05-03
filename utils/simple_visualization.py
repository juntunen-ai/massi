"""
Simplified visualization utilities for Finnish Government Budget Explorer.
This module provides basic visualization functions for mock data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class FinancialDataVisualizer:
    """Class for creating visualizations of financial data."""

    def plot_time_series(self, df: pd.DataFrame, x_col: str, y_col: str, title: str):
        """
        Plot a time series line chart.

        Args:
            df (pd.DataFrame): DataFrame containing the data to plot.
            x_col (str): Column name for the x-axis.
            y_col (str): Column name for the y-axis.
            title (str): Title of the chart.
        """
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df, x=x_col, y=y_col)
        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.grid(True)
        plt.show()

    def plot_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, title: str):
        """
        Plot a bar chart.

        Args:
            df (pd.DataFrame): DataFrame containing the data to plot.
            x_col (str): Column name for the x-axis.
            y_col (str): Column name for the y-axis.
            title (str): Title of the chart.
        """
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x=x_col, y=y_col)
        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.show()

    def plot_pie_chart(self, df: pd.DataFrame, labels_col: str, values_col: str, title: str):
        """
        Plot a pie chart.

        Args:
            df (pd.DataFrame): DataFrame containing the data to plot.
            labels_col (str): Column name for the labels.
            values_col (str): Column name for the values.
            title (str): Title of the chart.
        """
        plt.figure(figsize=(8, 8))
        plt.pie(df[values_col], labels=df[labels_col], autopct='%1.1f%%', startangle=140)
        plt.title(title)
        plt.show()