"""
Simple visualization utilities for Finnish financial data.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional

class FinancialDataVisualizer:
    """Class for visualizing Finnish financial data."""
    
    def __init__(self):
        """Initialize the visualizer."""
        # Set default color scheme for Finnish government data
        # Using a blue color palette reminiscent of Finnish flag
        self.color_scheme = px.colors.sequential.Blues
        
        # Common labels in Finnish and English
        self.label_translations = {
            'Vuosi': 'Year',
            'Kk': 'Month',
            'quarter': 'Quarter',
            'Nettokertymä': 'Net Amount',
            'Alkuperäinen_talousarvio': 'Original Budget',
            'Voimassaoleva_talousarvio': 'Current Budget',
            'Hallinnonala': 'Administrative Branch',
            'spending': 'Spending',
            'budget': 'Budget',
            'ministry': 'Ministry',
            'original_budget': 'Original Budget',
            'current_budget': 'Current Budget',
            'year': 'Year',
            'month': 'Month'
        }
    
    def detect_visualization_type(self, df: pd.DataFrame) -> str:
        """
        Automatically detect the appropriate visualization type based on the data.

        Args:
            df (pd.DataFrame): Data to visualize

        Returns:
            str: Visualization type ('line', 'bar', 'pie', etc.)
        """
        # Get column names and types
        columns = list(df.columns)
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

        # Check for time series data
        time_columns = [col for col in columns if col.lower() in ['year', 'vuosi', 'month', 'kk', 'quarter']]

        # Check for categorical data
        category_columns = [col for col in columns if col.lower() in ['hallinnonala', 'ministry', 'administrative_branch', 'paaluokka', 'momentti', 'luku']]

        # Logic for visualization type selection
        if len(df) == 1 and len(numeric_columns) >= 1:
            # Single row with numeric values - use a single value display
            return 'single_value'
        elif len(df) == 1 and len(numeric_columns) > 1:
            # Single row with multiple values - use bar for comparison
            return 'bar'
        elif len(time_columns) >= 1 and len(numeric_columns) >= 1:
            # Time series data - check for multiple numeric values
            if len(df) > 1:  # Need at least 2 points for a line chart
                if len(numeric_columns) > 2:  # Too many lines can be confusing
                    return 'time_bar'  # Use bar chart instead
                elif len(numeric_columns) > 1:
                    return 'time_multi_line'
                else:
                    return 'time_line'
            else:
                return 'single_value'
        elif category_columns and len(numeric_columns) >= 1:
            # Categorical data with numeric values
            if len(df) <= 8:  # Good for pie charts
                return 'pie'
            else:
                return 'bar'
        elif len(df) > 10 and len(numeric_columns) >= 1:
            # Large datasets
            if any(col.lower() in ['year', 'vuosi'] for col in columns):
                return 'time_bar'
            else:
                return 'bar'
        elif len(df) <= 10 and len(numeric_columns) >= 1:
            # Small datasets
            return 'bar'
        else:
            # Default to table when no clear pattern
            return 'table'

    def _create_visualization_title(self, df: pd.DataFrame, viz_type: str, query: str) -> str:
        """
        Create a more descriptive title based on the data and query.

        Args:
            df (pd.DataFrame): Data to visualize
            viz_type (str): Visualization type
            query (str): Original query

        Returns:
            str: Descriptive title
        """
        # Extract key information from data
        time_cols = [col for col in df.columns if col.lower() in ['year', 'vuosi', 'month', 'kk', 'quarter']]
        ministry_cols = [col for col in df.columns if col.lower() in ['hallinnonala', 'ministry', 'administrative_branch']]

        title_parts = []

        # Add query focus
        if 'budget' in query.lower():
            title_parts.append('Budget Analysis')
        elif 'spending' in query.lower():
            title_parts.append('Spending Analysis')
        else:
            title_parts.append(query.capitalize())

        # Add time period info
        if time_cols and len(df) > 0:
            time_col = time_cols[0]
            min_year = df[time_col].min()
            max_year = df[time_col].max()
            if min_year == max_year:
                title_parts.append(f"({min_year})")
            else:
                title_parts.append(f"({min_year}-{max_year})")

        # Add ministry info if available
        if ministry_cols and len(df) < 5:  # Don't add if too many ministries
            ministry_col = ministry_cols[0]
            ministries = df[ministry_col].unique()
            if len(ministries) == 1:
                title_parts.append(f"- {ministries[0]}")

        return ' '.join(title_parts)
    
    def create_visualization(self, df: pd.DataFrame, title: str = '', 
                            viz_type: Optional[str] = None) -> go.Figure:
        """
        Create a visualization based on the data with error handling.
        
        Args:
            df (pd.DataFrame): Data to visualize
            title (str): Visualization title
            viz_type (Optional[str]): Visualization type or None for auto-detection
            
        Returns:
            go.Figure: Plotly figure
        """
        try:
            # Validate input
            if df is None or df.empty:
                return self._create_error_figure("No data available to visualize")
            
            # Auto-detect visualization type if not specified
            if not viz_type:
                viz_type = self.detect_visualization_type(df)
            
            # Translate column names for better display
            df_display = df.copy()
            df_display.columns = [self.label_translations.get(col, col) for col in df.columns]
            
            # Create appropriate visualization based on type
            if viz_type == 'single_value':
                return self._create_single_value_viz(df_display, title)
            elif viz_type == 'time_line':
                return self._create_time_line_viz(df_display, title)
            elif viz_type == 'time_multi_line':
                return self._create_time_multi_line_viz(df_display, title)
            elif viz_type == 'pie':
                return self._create_pie_viz(df_display, title)
            elif viz_type == 'bar':
                return self._create_bar_viz(df_display, title)
            elif viz_type == 'time_bar':
                return self._create_time_bar_viz(df_display, title)
            else:
                # Default to table
                return self._create_table_viz(df_display, title)
        
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return self._create_error_figure(f"Error creating visualization: {str(e)}")

    def _create_error_figure(self, error_message: str) -> go.Figure:
        """Create an error visualization."""
        fig = go.Figure()
        
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="red"),
            align="center"
        )
        
        fig.update_layout(
            title="Visualization Error",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_single_value_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a visualization for a single value."""
        # Extract the first numeric column and its value
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            return self._create_table_viz(df, title)
        
        value_col = numeric_cols[0]
        value = df[value_col].iloc[0]
        
        # Create a figure with a big number display
        fig = go.Figure()
        
        fig.add_trace(go.Indicator(
            mode="number",
            value=value,
            title={"text": f"{title}<br><span style='font-size:0.8em;color:gray'>{value_col}</span>"},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_time_line_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a line chart for time series data with error handling."""
        # Ensure column names are compatible with BigQuery
        df.columns = [col.replace(' ', '_').lower() for col in df.columns]

        # Identify the time column and numeric column
        time_cols = [col for col in df.columns if col in ['year', 'vuosi', 'month', 'kk', 'quarter']]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        if not time_cols or not numeric_cols:
            return self._create_error_figure("No time series data found")

        time_col = time_cols[0]
        value_col = numeric_cols[0]

        # Check if we have enough data points
        if len(df) < 2:
            return self._create_single_value_viz(df, title)

        try:
            # Create line chart
            fig = px.line(
                df, 
                x=time_col, 
                y=value_col,
                title=title,
                markers=True,
                color_discrete_sequence=[self.color_scheme[5]]
            )

            # Format the layout
            fig.update_layout(
                xaxis_title=time_col,
                yaxis_title=value_col,
                height=400
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating line chart: {str(e)}")
            return self._create_error_figure(f"Error creating line chart: {str(e)}")
    
    def _create_time_multi_line_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a line chart for time series data with multiple metrics."""
        # Identify the time column and numeric columns
        time_cols = [col for col in df.columns if col.lower() in 
                    ['year', 'vuosi', 'month', 'kk', 'quarter']]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not time_cols or len(numeric_cols) < 2:
            return self._create_time_line_viz(df, title)
        
        time_col = time_cols[0]
        
        # Create line chart with multiple lines
        fig = px.line(
            df,
            x=time_col,
            y=numeric_cols,
            title=title,
            markers=True,
            color_discrete_sequence=self.color_scheme
        )
        
        # Format the layout
        fig.update_layout(
            xaxis_title=time_col,
            yaxis_title="Value",
            height=400,
            legend_title_text=""
        )
        
        return fig
    
    def _create_pie_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a pie chart for categorical data."""
        # Identify the category column and numeric column
        non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not non_numeric_cols or not numeric_cols:
            return self._create_table_viz(df, title)
        
        category_col = non_numeric_cols[0]
        value_col = numeric_cols[0]
        
        # Create pie chart
        fig = px.pie(
            df,
            values=value_col,
            names=category_col,
            title=title,
            color_discrete_sequence=self.color_scheme
        )
        
        # Format the layout
        fig.update_layout(
            height=400
        )
        
        return fig
    
    def _create_bar_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a bar chart for categorical data."""
        # Identify the category column and numeric column
        non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not non_numeric_cols or not numeric_cols:
            return self._create_table_viz(df, title)
        
        category_col = non_numeric_cols[0]
        value_col = numeric_cols[0]
        
        # Sort the data by value for better visualization
        df_sorted = df.sort_values(by=value_col, ascending=False)
        
        # Create bar chart
        fig = px.bar(
            df_sorted,
            x=category_col,
            y=value_col,
            title=title,
            color_discrete_sequence=[self.color_scheme[5]]
        )
        
        # Format the layout
        fig.update_layout(
            xaxis_title=category_col,
            yaxis_title=value_col,
            height=400
        )
        
        return fig
    
    def _create_time_bar_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a bar chart for time series data."""
        # Identify the time column and numeric column
        time_cols = [col for col in df.columns if col.lower() in 
                    ['year', 'vuosi', 'month', 'kk', 'quarter']]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not time_cols or not numeric_cols:
            return self._create_table_viz(df, title)
        
        time_col = time_cols[0]
        value_col = numeric_cols[0]
        
        # Create bar chart
        fig = px.bar(
            df,
            x=time_col,
            y=value_col,
            title=title,
            color_discrete_sequence=[self.color_scheme[5]]
        )
        
        # Format the layout
        fig.update_layout(
            xaxis_title=time_col,
            yaxis_title=value_col,
            height=400
        )
        
        return fig
    
    def _create_table_viz(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create a table visualization for the data."""
        # Format numeric columns
        df_display = df.copy()
        for col in df.select_dtypes(include=['number']).columns:
            df_display[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
        
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df_display.columns),
                fill_color=self.color_scheme[5],
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[df_display[col] for col in df_display.columns],
                fill_color='lavender',
                align='left'
            )
        )])
        
        # Add title
        fig.update_layout(
            title=title,
            height=400
        )
        
        return fig