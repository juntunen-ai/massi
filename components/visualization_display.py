"""
Visualization display component for the Streamlit UI.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional
import logging
from utils.visualization import FinancialDataVisualizer # Assuming this path is correct
from utils.logger import setup_logger # Assuming this path is correct
import os
import traceback # Import the traceback module

# Ensure logger is set up at the module level if not already
# If setup_logger is idempotent, this is fine. Otherwise, ensure it's called once.
logger = setup_logger(__name__)

class VisualizationDisplay:
    """Component for displaying query results and visualizations."""

    def __init__(self):
        """Initialize the visualization display component with proper logging."""
        self.logger = setup_logger(__name__) # Or just use the module-level logger
        self.logger.info("VisualizationDisplay component initialized")
        self.visualizer = FinancialDataVisualizer()

    def render_results(self, query: str, sql: str, explanation: str,
                      df: Optional[pd.DataFrame], viz_type: Optional[str] = None,
                      viz_title: Optional[str] = None):
        """
        Render the query results with structured logging.
        """
        self.logger.info(f"Rendering results for query: '{query}'", extra={
            'sql': sql,
            'viz_type': viz_type,
            'viz_title': viz_title,
            'dataframe_present': df is not None
        })
        if df is None:
            self.logger.warning("DataFrame is None, rendering error state.")
            self._render_error_state(query, sql, explanation if explanation else "No data returned from query execution.")
            return

        try:
            query_hash = hash(query)
            # Tab creation itself is unlikely to error but we'll wrap content
            tab1, tab2, tab3 = st.tabs(["Analysis", "Data", "SQL Query"])

            with tab1:
                self.logger.debug("Rendering Analysis Tab")
                self._render_visualization_tab(query, df, viz_type, viz_title)
                self.logger.debug("Analysis Tab rendering complete.")

            with tab2:
                self.logger.debug("Rendering Data Tab")
                self._render_data_tab(df)
                self.logger.debug("Data Tab rendering complete.")

            with tab3:
                self.logger.debug("Rendering SQL Tab")
                self._render_sql_tab(sql, explanation)
                self.logger.debug("SQL Tab rendering complete.")

            if 'last_query_hash' not in st.session_state or st.session_state.last_query_hash != query_hash:
                self.logger.debug(f"New query detected (hash: {query_hash}), resetting relevant session state.")
                st.session_state.last_query_hash = query_hash
                pagination_keys = [key for key in st.session_state.keys() if key.startswith('current_page_')]
                for key in pagination_keys:
                    self.logger.debug(f"Deleting pagination session state key: {key}")
                    del st.session_state[key]
        except Exception as e:
            self.logger.error(f"Unhandled error in render_results for query '{query}': {str(e)}")
            self.logger.error(traceback.format_exc())
            st.error(f"A critical error occurred while rendering results: {str(e)}")
            # Optionally, show more details or the custom message you were seeing
            st.info("Query processed, but an issue occurred while trying to display the results.")


    def _render_error_state(self, query: str, sql: str, explanation: str):
        """Render an error state when query results are unavailable."""
        self.logger.info(f"Rendering error state for query: {query}")
        if 'current_results' in st.session_state:
            st.session_state.current_results = None
        st.error("Unable to retrieve data for your query or an error occurred.") # Slightly modified message
        st.markdown(f"**Your question:** {query}")
        with st.expander("Details", expanded=True):
            if sql:
                st.markdown("### Generated SQL")
                st.code(sql, language="sql")
            st.markdown("### Error Details")
            st.markdown(explanation)

    def _render_visualization_tab(self, query: str, df: pd.DataFrame,
                                 viz_type: Optional[str], viz_title: Optional[str]):
        """Render the visualization tab with enhanced error logging."""
        try:
            self.logger.info(f"Rendering visualization: type='{viz_type}', title='{viz_title}'")
            df_viz = df.copy()
            df_viz.columns = [col.lower().replace('vuosi', 'year').replace('voimassaoleva_talousarvio', 'budget').replace('nettokertymä', 'spending') for col in df_viz.columns]

            if not viz_type:
                self.logger.debug("viz_type not provided, detecting automatically.")
                viz_type = self.visualizer.detect_visualization_type(df_viz)
                self.logger.debug(f"Detected viz_type: {viz_type}")


            final_viz_title = viz_title.encode('utf-8').decode('utf-8') if viz_title else query.capitalize()
            self.logger.debug(f"Using visualization title: {final_viz_title}")

            fig = self.visualizer.create_visualization(df_viz, final_viz_title, viz_type)
            self.logger.debug("Visualization figure created successfully.")

            st.plotly_chart(fig, use_container_width=True)
            self.logger.info("Plotly chart rendered successfully.")

            if 'result_explanation' in st.session_state and st.session_state.result_explanation:
                st.markdown("### Analysis")
                st.markdown(st.session_state.result_explanation)
            else:
                self.logger.info("No LLM result explanation in session_state, generating basic insights.")
                st.markdown("### Key Insights")
                self._generate_basic_insights(df_viz, query)
        except Exception as e:
            self.logger.error(f"Error rendering visualization tab for query '{query}': {str(e)}")
            self.logger.error(traceback.format_exc()) # THIS IS THE KEY LOGGING
            st.error(f"Could not display visualization: {str(e)}")

    def _render_data_tab(self, df: pd.DataFrame):
        """Render the data tab with the raw data and enhanced error logging."""
        try:
            self.logger.info(f"Rendering data tab with {len(df)} rows.")
            st.markdown("### Raw Data")
            st.markdown(f"Showing {len(df)} rows and {len(df.columns)} columns")

            page_size = st.selectbox("Rows per page:", [10, 25, 50, 100], index=0, key=f"pagesize_{hash(str(df.values.tobytes()))}") # Unique key for selectbox
            df_display = df.copy()
            column_mapping = {
                'Alkuperäinen_talousarvio': 'Original Budget', 'Voimassaoleva_talousarvio': 'Current Budget',
                'Nettokertymä': 'Net Amount', 'Käytettävissä': 'Available',
                'Lisätalousarvio': 'Supplementary Budget', 'Kirjanpitoyksikkö': 'Accounting Unit',
                'Loppusaldo': 'Closing Balance'
            }
            df_display.columns = [column_mapping.get(col, col) for col in df_display.columns]
            total_pages = (len(df_display) + page_size - 1) // page_size

            # Using a more robust keying for pagination based on data content
            data_content_hash = hash(df_display.to_string()) # Hash of data content
            page_key = f"current_page_data_tab_{data_content_hash}"

            if page_key not in st.session_state:
                st.session_state[page_key] = 0
            if st.session_state[page_key] >= total_pages and total_pages > 0 : # check total_pages > 0
                st.session_state[page_key] = max(0, total_pages - 1)
            elif total_pages == 0: # handle empty dataframe case
                st.session_state[page_key] = 0


            if total_pages > 1:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("← Previous", key=f"prev_{page_key}", disabled=st.session_state[page_key] <= 0):
                        if page_key in st.session_state and st.session_state[page_key] > 0:
                            st.session_state[page_key] -= 1
                            st.rerun()
                with col2:
                    current_page_display = st.session_state.get(page_key, 0) + 1
                    st.markdown(f"Page {current_page_display} of {total_pages if total_pages > 0 else 1}") # Display 1 if total_pages is 0
                with col3:
                    if st.button("Next →", key=f"next_{page_key}", disabled=st.session_state.get(page_key,0) >= total_pages - 1): # Use .get for safety
                        if page_key in st.session_state and st.session_state[page_key] < total_pages - 1:
                            st.session_state[page_key] += 1
                            st.rerun()
            
            start_idx = st.session_state.get(page_key, 0) * page_size # Use .get for safety
            end_idx = min(start_idx + page_size, len(df_display))
            
            if not df_display.empty: # Check if dataframe is not empty before iloc
                 st.dataframe(df_display.iloc[start_idx:end_idx], use_container_width=True)
            else:
                 st.markdown("No data to display in the table.")

            self.logger.info("Dataframe rendered successfully.")

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download data as CSV", data=csv, file_name="finnish_financial_data.csv", mime="text/csv")
        except Exception as e:
            self.logger.error(f"Error rendering data tab: {str(e)}")
            self.logger.error(traceback.format_exc()) # THIS IS THE KEY LOGGING
            st.error(f"Could not display data table: {str(e)}")

    def _render_sql_tab(self, sql: str, explanation: str):
        """Render the SQL tab with improved formatting and error logging."""
        try:
            self.logger.info("Rendering SQL tab.")
            st.markdown("### Generated SQL Query")
            formatted_sql = self._format_sql_for_display(sql)
            st.code(formatted_sql, language="sql")

            # Simplified copy button for robustness
            # st.text_area("Copy SQL below:", sql, height=150, key="sql_copy_area") # Alternative copy

            st.markdown("### Query Explanation")
            st.markdown(explanation)
            self.logger.info("SQL tab rendered successfully.")
        except Exception as e:
            self.logger.error(f"Error rendering SQL tab: {str(e)}")
            self.logger.error(traceback.format_exc()) # THIS IS THE KEY LOGGING
            st.error(f"Could not display SQL information: {str(e)}")

    def _format_sql_for_display(self, sql: str) -> str:
        """Format SQL for better display."""
        import re
        keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'JOIN', 'ON']
        formatted_sql = sql
        try:
            for keyword in keywords:
                pattern = f'\\b{keyword}\\b' # Using \\b for word boundary
                replacement = f'\n{keyword}'
                # Using re.sub to replace case-insensitively
                formatted_sql = re.sub(pattern, replacement, formatted_sql, flags=re.IGNORECASE)
            # Remove leading newline if any
            formatted_sql = formatted_sql.strip()
        except Exception as e:
            self.logger.error(f"Error formatting SQL: {str(e)}. Returning original SQL.")
            return sql # Return original SQL if formatting fails
        return formatted_sql

    def _generate_basic_insights(self, df: pd.DataFrame, query: str):
        """Generate basic insights from the data if no LLM explanation is available."""
        try:
            self.logger.info("Generating basic insights.")
            # ... (rest of your _generate_basic_insights logic, consider adding try-except here too if complex) ...
            # For brevity, the detailed logic of this function is omitted from this direct modification example,
            # but you should apply similar try-except logging if it performs complex operations or calculations.
            st.markdown(f"Basic insights for query: {query} based on {len(df)} rows.")
            if df.empty:
                st.markdown("The dataset is empty, so no specific insights can be generated.")
                return

            time_cols = [col for col in df.columns if col.lower() in ['year', 'vuosi', 'month', 'kk', 'quarter']]
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

            if time_cols and numeric_cols:
                time_col = time_cols[0]
                main_metric = numeric_cols[0]
                if len(df) > 1:
                    first_value = df[main_metric].iloc[0]
                    last_value = df[main_metric].iloc[-1]
                    if pd.api.types.is_numeric_dtype(df[main_metric]) and first_value != 0 :
                        change = last_value - first_value
                        pct_change = (change / first_value) * 100 if first_value != 0 else float('inf')
                        trend_text = f"Increased by {pct_change:.1f}%" if pct_change > 0 else (f"Decreased by {abs(pct_change):.1f}%" if pct_change < 0 else "Remained stable")
                        st.markdown(f"**{main_metric}**: {trend_text} from {first_value:,.2f} to {last_value:,.2f} over the period.")
                    else:
                         st.markdown(f"**{main_metric}**: Trend calculation skipped due to non-numeric data or zero initial value.")

                    for col in numeric_cols[1:3]:
                        if pd.api.types.is_numeric_dtype(df[col]):
                             st.markdown(f"**{col}**: Average of {df[col].mean():,.2f}, ranging from {df[col].min():,.2f} to {df[col].max():,.2f}")
                elif len(df) == 1 and pd.api.types.is_numeric_dtype(df[main_metric]):
                     st.markdown(f"**{main_metric}**: {df[main_metric].iloc[0]:,.2f}")

            elif numeric_cols: # Simplified this branch
                if not df.empty:
                    for main_metric in numeric_cols[:2]: # Show insights for first two numeric cols
                         if pd.api.types.is_numeric_dtype(df[main_metric]):
                            st.markdown(f"**{main_metric}**: Total {df[main_metric].sum():,.2f}, Average {df[main_metric].mean():,.2f}")
            
            st.markdown(f"The query returned {len(df)} rows of data with {len(df.columns)} columns.")
            self.logger.info("Basic insights generation complete.")

        except Exception as e:
            self.logger.error(f"Error generating basic insights: {str(e)}")
            self.logger.error(traceback.format_exc())
            st.warning("Could not generate basic insights due to an error.")