"""
Visualization display component for the Streamlit UI.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional
import logging
from utils.visualization import FinancialDataVisualizer

logger = logging.getLogger(__name__)

class VisualizationDisplay:
    """Component for displaying query results and visualizations."""
    
    def __init__(self):
        """Initialize the visualization display component."""
        self.visualizer = FinancialDataVisualizer()
    
    def render_results(self, query: str, sql: str, explanation: str, 
                      df: Optional[pd.DataFrame], viz_type: Optional[str] = None, 
                      viz_title: Optional[str] = None):
        """
        Render the query results and visualization.
        
        Args:
            query (str): Original natural language query
            sql (str): Generated SQL query
            explanation (str): Explanation of the SQL query
            df (Optional[pd.DataFrame]): Query results as DataFrame
            viz_type (Optional[str]): Visualization type
            viz_title (Optional[str]): Visualization title
        """
        if df is None:
            self._render_error_state(query, sql, explanation)
            return
        
        # Convert SQL to a nicely formatted display
        formatted_sql = self._format_sql_for_display(sql)
        
        # Main results container
        with st.container():
            # Simple tabs for different views of the data
            tab1, tab2, tab3 = st.tabs(["Analysis", "Data", "SQL Query"])
            
            with tab1:
                self._render_visualization_tab(query, df, viz_type, viz_title)
                
            with tab2:
                self._render_data_tab(df)
                
            with tab3:
                self._render_sql_tab(sql, explanation)
    
    def _render_error_state(self, query: str, sql: str, explanation: str):
        """
        Render an error state when query results are unavailable.
        
        Args:
            query (str): Original natural language query
            sql (str): Generated SQL query
            explanation (str): Explanation of the SQL query or error
        """
        st.error("Unable to retrieve data for your query.")
        st.markdown(f"**Your question:** {query}")
        
        with st.expander("Details"):
            if sql:
                st.markdown("### Generated SQL")
                st.code(sql, language="sql")
            
            st.markdown("### Error Details")
            st.markdown(explanation)
    
    def _render_visualization_tab(self, query: str, df: pd.DataFrame, 
                                 viz_type: Optional[str], viz_title: Optional[str]):
        """
        Render the visualization tab.
        
        Args:
            query (str): Original natural language query
            df (pd.DataFrame): Query results as DataFrame
            viz_type (Optional[str]): Visualization type
            viz_title (Optional[str]): Visualization title
        """
        # Determine visualization type if not provided
        if not viz_type:
            viz_type = self.visualizer.detect_visualization_type(df)
        
        # Determine title if not provided
        if not viz_title:
            viz_title = query.capitalize()
        
        # Create the visualization
        fig = self.visualizer.create_visualization(df, viz_title, viz_type)
        
        # Show the visualization
        st.plotly_chart(fig, use_container_width=True)
        
        # Show natural language explanation of the results
        if 'result_explanation' in st.session_state:
            st.markdown("### Analysis")
            st.markdown(st.session_state.result_explanation)
        else:
            st.markdown("### Key Insights")
            # Generate basic insights if no LLM explanation is available
            self._generate_basic_insights(df, query)
    
    def _render_data_tab(self, df: pd.DataFrame):
        """
        Render the data tab with the raw data.
        
        Args:
            df (pd.DataFrame): Query results as DataFrame
        """
        st.markdown("### Raw Data")
        st.markdown(f"Showing {len(df)} rows and {len(df.columns)} columns")
        
        # Display pagination controls
        page_size = st.selectbox("Rows per page:", [10, 25, 50, 100], index=0)
        
        # Calculate total pages
        total_pages = (len(df) + page_size - 1) // page_size
        
        # Initialize current page in session state if not present
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0
        
        # Display pagination controls if needed
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button("← Previous", disabled=st.session_state.current_page <= 0):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with col2:
                st.markdown(f"Page {st.session_state.current_page + 1} of {total_pages}")
                
            with col3:
                if st.button("Next →", disabled=st.session_state.current_page >= total_pages - 1):
                    st.session_state.current_page += 1
                    st.rerun()
        
        # Calculate start and end indices for the current page
        start_idx = st.session_state.current_page * page_size
        end_idx = min(start_idx + page_size, len(df))
        
        # Display the data for the current page
        st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
        
        # Add download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="finnish_financial_data.csv",
            mime="text/csv",
        )
    
    def _render_sql_tab(self, sql: str, explanation: str):
        """
        Render the SQL tab with the query and explanation.
        
        Args:
            sql (str): Generated SQL query
            explanation (str): Explanation of the SQL query
        """
        st.markdown("### Generated SQL Query")
        st.code(sql, language="sql")
        
        st.markdown("### Query Explanation")
        st.markdown(explanation)
        
        # Add copy button for SQL
        st.text_area("Copy SQL Query", sql, height=100)
    
    def _format_sql_for_display(self, sql: str) -> str:
        """
        Format SQL for better display.
        
        Args:
            sql (str): SQL query
            
        Returns:
            str: Formatted SQL
        """
        # Simple SQL formatting
        import re
        
        # Add line breaks after major SQL keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'JOIN', 'ON']
        
        formatted_sql = sql
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            replacement = f'\n{keyword}'
            formatted_sql = re.sub(pattern, replacement, formatted_sql, flags=re.IGNORECASE)
        
        return formatted_sql
    
    def _generate_basic_insights(self, df: pd.DataFrame, query: str):
        """
        Generate basic insights from the data if no LLM explanation is available.
        
        Args:
            df (pd.DataFrame): Query results as DataFrame
            query (str): Original natural language query
        """
        # Check for time series data
        time_cols = [col for col in df.columns if col.lower() in 
                   ['year', 'vuosi', 'month', 'kk', 'quarter']]
        
        # Check for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if time_cols and numeric_cols:
            # Time series data with numeric values
            time_col = time_cols[0]
            main_metric = numeric_cols[0]
            
            if len(df) > 1:
                # Calculate trend
                first_value = df[main_metric].iloc[0]
                last_value = df[main_metric].iloc[-1]
                change = last_value - first_value
                pct_change = (change / first_value) * 100 if first_value != 0 else float('inf')
                
                # Show trend insights
                if pct_change > 0:
                    trend_text = f"Increased by {pct_change:.1f}% from {first_value:,.2f} to {last_value:,.2f}"
                elif pct_change < 0:
                    trend_text = f"Decreased by {abs(pct_change):.1f}% from {first_value:,.2f} to {last_value:,.2f}"
                else:
                    trend_text = f"Remained stable at {first_value:,.2f}"
                
                st.markdown(f"**{main_metric}**: {trend_text} over the period.")
                
                # Show additional metrics
                for col in numeric_cols[1:3]:  # Limit to 2 additional metrics
                    st.markdown(f"**{col}**: Average of {df[col].mean():,.2f}, ranging from {df[col].min():,.2f} to {df[col].max():,.2f}")
            
            else:
                # Single value
                st.markdown(f"**{main_metric}**: {df[main_metric].iloc[0]:,.2f}")
        
        elif len(numeric_cols) > 0:
            # Categorical data with numeric values
            if len(df) > 0:
                main_metric = numeric_cols[0]
                
                # Show top and bottom values
                if len(df) > 1:
                    top_row = df.nlargest(1, main_metric).iloc[0]
                    bottom_row = df.nsmallest(1, main_metric).iloc[0]
                    
                    # Get the first non-numeric column for category name
                    category_cols = [col for col in df.columns if col not in numeric_cols]
                    category_col = category_cols[0] if category_cols else None
                    
                    if category_col:
                        st.markdown(f"**Highest {main_metric}**: {top_row[category_col]} with {top_row[main_metric]:,.2f}")
                        st.markdown(f"**Lowest {main_metric}**: {bottom_row[category_col]} with {bottom_row[main_metric]:,.2f}")
                    
                    # Show total and average
                    st.markdown(f"**Total {main_metric}**: {df[main_metric].sum():,.2f}")
                    st.markdown(f"**Average {main_metric}**: {df[main_metric].mean():,.2f}")
                else:
                    # Single value
                    st.markdown(f"**{main_metric}**: {df[main_metric].iloc[0]:,.2f}")
        
        # Show data dimensions
        st.markdown(f"The query returned {len(df)} rows of data with {len(df.columns)} columns.")