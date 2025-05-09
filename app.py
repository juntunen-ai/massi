"""
Main Streamlit application file for the Finnish Government Budget Explorer.

This application serves as the primary interface for users to explore
Finnish government financial data. It integrates various components for
natural language query processing, data retrieval from BigQuery,
dynamic visualization generation, and AI-powered explanations of financial insights.
"""

import streamlit as st
import logging
import pandas as pd
import json
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
import traceback # Import traceback

# Import components
from components.query_input import QueryInput
from components.visualization_display import VisualizationDisplay
from components.sidebar import Sidebar

# Import utility functions
from utils.data_provider import DataProvider # Not directly used, but keep if planned
from utils.visualization import FinancialDataVisualizer
from utils.auth import init_google_auth # Not directly used, but keep if planned
from utils.real_data_provider import RealDataProvider
from utils.nl_to_sql import NLToSQLConverter
from utils.bigquery_schema import get_bigquery_schema

from models.llm_interface import LLMInterface

# Configure logging
# Ensure your logger is configured to show DEBUG level if you use logger.debug
logging.basicConfig(level=logging.INFO, # Consider logging.DEBUG for more verbose output during debugging
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Budjettihaukka",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

class FinancialDataApp:
    """Main application class for Finnish Government Budget Explorer."""

    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing FinancialDataApp")

        if 'active_filters' not in st.session_state:
            st.session_state.active_filters = {}
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        if 'result_explanation' not in st.session_state: # Initialize if used by visualization_display
            st.session_state.result_explanation = ""
        if 'error_message' not in st.session_state:
             st.session_state.error_message = ""
        if 'sql_query' not in st.session_state: # Used in handle_query for display
            st.session_state.sql_query = ""


        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            logger.error("GOOGLE_CLOUD_PROJECT environment variable not set.")
            st.error("Configuration error: GOOGLE_CLOUD_PROJECT not set. App may not function correctly.")
            return # Stop initialization if critical config is missing

        try:
            self.data_provider = RealDataProvider(project_id=self.project_id)
            self.visualizer = FinancialDataVisualizer()
            # Components that depend on session state or other initializations
            # will be fully initialized in the run() method or after essential data is loaded.

            self.table_name = os.getenv("BIGQUERY_TABLE_ID", "massi-financial-analysis.finnish_finance_data.budget_transactions")
            logger.info(f"Using BigQuery table: {self.table_name}")

            raw_schema_fields = get_bigquery_schema()
            if not raw_schema_fields:
                 logger.error(f"Failed to load table schema definition for {self.table_name}.")
                 st.error(f"Configuration error: Could not load schema definition for table {self.table_name}.")
                 self.table_schema = [] # Ensure table_schema is initialized even on error
                 # Decide if you want to return or allow app to run with degraded functionality
            else:
                self.table_schema = []
                for field in raw_schema_fields:
                    self.table_schema.append({
                        "name": field.name,
                        "type": field.field_type,
                        "description": field.description if field.description else ""
                    })
                if not self.table_schema:
                     logger.error(f"Converted table schema is empty for {self.table_name}.")
                     st.error(f"Configuration error: Converted schema is empty for table {self.table_name}.")
                     # return # Decide if you want to return
                else:
                    logger.info(f"Successfully loaded and converted schema for table {self.table_name}")

            self.llm_interface = LLMInterface(project_id=self.project_id)
            logger.info("LLMInterface initialized.")

            self.nl_to_sql_converter = NLToSQLConverter(table_name=self.table_name)
            logger.info("NLToSQLConverter initialized and table info set.")

            # Defer sidebar and query_input initialization to run() to ensure session_state items are ready
            self.sidebar = None
            self.query_input = None
            self.visualization_display = VisualizationDisplay() # Can be initialized here

            self.load_available_years()

        except Exception as e:
            logger.error(f"Critical error during app __init__: {e}", exc_info=True)
            st.error(f"Critical error during app initialization: {e}. Please check logs.")
            # To prevent run() from executing if init fails badly
            st.session_state.initialization_failed = True


    def load_available_years(self):
        logger.debug("load_available_years called")
        try:
            years = self.data_provider.get_available_years()
            st.session_state.available_years = years
            logger.info(f"Loaded available years: {years}")
        except Exception as e:
            logger.error(f"Failed to load available years: {e}", exc_info=True)
            st.session_state.available_years = [2020, 2021, 2022, 2023, 2024] # Fallback
            st.warning("Could not dynamically load available years. Using default values.")
            
    def handle_query(self, query: str):
        logger.info(f"--- Entering handle_query for query: '{query}' ---")
        # This state is set by the QueryInput component or the run method
        # st.session_state.current_query = query # current_query should be set before calling handle_query

        with st.spinner("Processing your query... This may take a moment."):
            try:
                sql_query, sql_explanation = self._generate_sql_from_nl(query)
                st.session_state.sql_query = sql_query # Store for potential later use or if error occurs

                if not sql_query:
                    logger.warning(f"SQL generation failed for query: '{query}'. Reason: {sql_explanation}")
                    # Display error using visualization_display's error state
                    self.visualization_display.render_results(
                        query=query, 
                        sql="No SQL generated.", 
                        explanation=sql_explanation if sql_explanation else "Could not understand the query to generate SQL.", 
                        df=None
                    )
                    return

                logger.info(f"Executing SQL query: {sql_query}")
                result_df = self.data_provider.execute_query(sql_query)

                if result_df is None or result_df.empty:
                    no_data_message = "The query returned no data. Please try a different question or refine your filters."
                    logger.info(f"No data returned for SQL: {sql_query}. Original query: '{query}'")
                    self.visualization_display.render_results(
                        query=query, 
                        sql=sql_query, 
                        explanation=f"SQL Explanation: {sql_explanation}\n\nResult: {no_data_message}", 
                        df=None # Pass None for df
                    )
                    return # Exit after displaying no data message

                logger.info(f"Query returned {len(result_df)} rows.")
                st.session_state.query_result_df = result_df # Store for potential use by other parts if needed

                viz_type, viz_title, _ = self._recommend_visualization(query, result_df)
                result_explanation_text = self._explain_results(query, sql_query, result_df, viz_type)
                st.session_state.result_explanation = result_explanation_text

                logger.info(f"Calling visualization_display.render_results for query: '{query}'")
                self.visualization_display.render_results(
                    query=query,
                    sql=sql_query,
                    explanation=result_explanation_text, # This should contain the LLM's explanation of data
                    df=result_df,
                    viz_type=viz_type,
                    viz_title=viz_title
                )
                logger.info(f"--- Exiting handle_query successfully for query: '{query}' ---")
                st.session_state.error_message = "" # Clear any previous error message

            except Exception as e:
                logger.error(f"Critical error in handle_query for query '{query}': {str(e)}")
                logger.error(traceback.format_exc()) # Log the full traceback
                st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
                # Display error using visualization_display's error state or a global st.error
                self.visualization_display.render_results(
                    query=query,
                    sql=st.session_state.get('sql_query', "Error before SQL generation."), # Show SQL if available
                    explanation=f"An error occurred during processing: {str(e)}",
                    df=None # No dataframe if error
                )


    def _generate_sql_from_nl(self, query: str) -> tuple[Optional[str], str]:
        logger.info(f"Generating SQL for query: '{query}'")
        if not hasattr(self, 'nl_to_sql_converter'):
            logger.error("NLToSQLConverter not initialized.")
            return None, "Error: NL-to-SQL converter is not available."
        try:
            # Ensure schema is passed if nl_to_sql_converter expects it during generation
            sql_query, explanation_of_sql = self.nl_to_sql_converter.generate_sql(query) # self.table_schema
            if sql_query:
                logger.info(f"Generated SQL: {sql_query}")
            else:
                logger.warning(f"NLToSQLConverter failed to generate SQL for: '{query}'. Explanation: {explanation_of_sql}")
            return sql_query, explanation_of_sql
        except Exception as e:
            logger.error(f"Exception in _generate_sql_from_nl: {str(e)}", exc_info=True)
            return None, f"Error generating SQL: {str(e)}"

    def _get_table_schema(self): # This method seems unused, NLToSQLConverter gets schema at init
        # ... (your existing code, ensure it's robust or remove if NLToSQLConverter handles schema internally) ...
        logger.warning("_get_table_schema was called, but NLToSQLConverter should have schema from init.")
        return self.table_schema # Return already loaded schema

    def _explain_results(self, query: str, sql: str, df: pd.DataFrame, viz_type: str) -> str:
        logger.info(f"Generating explanation for query: '{query}'")
        if not hasattr(self, 'llm_interface'):
            logger.error("LLMInterface not initialized.")
            return "Error: LLM interface is not available."
        try:
            explanation = self.llm_interface.explain_results(query, sql, df, viz_type)
            logger.info("Successfully generated result explanation.")
            return explanation
        except Exception as e:
            logger.error(f"Exception in _explain_results: {str(e)}", exc_info=True)
            return f"Error generating explanation: {str(e)}"

    def _recommend_visualization(self, query: str, df: pd.DataFrame) -> tuple[str, str, str]:
        logger.info(f"Recommending visualization for query: '{query}'")
        # ... (your existing _recommend_visualization logic seems mostly okay) ...
        # Ensure robust return types and handling as you have.
        user_preferred_viz_type = st.session_state.get('preferred_viz_type')

        if user_preferred_viz_type and user_preferred_viz_type != 'auto':
            logger.info(f"User preferred viz type: {user_preferred_viz_type}")
            simple_title = query.capitalize() if query else "Visualization"
            default_explanation = f"Using user-preferred visualization: {user_preferred_viz_type}"
            return user_preferred_viz_type, simple_title, default_explanation

        try:
            recommendation_result = self.llm_interface.recommend_visualization(query, df.columns.tolist(), df.head())
        except Exception as e:
            logger.error(f"Error calling LLM for viz recommendation: {e}", exc_info=True)
            recommendation_result = ("table", query.capitalize() if query else "Data Table", "Error in LLM recommendation, defaulting to table.")


        viz_type = "table"
        viz_title = query.capitalize() if query else "Data Table"
        recommendation_explanation = "Defaulting to table view."

        if isinstance(recommendation_result, dict):
            viz_type = recommendation_result.get("viz_type", viz_type)
            viz_title = recommendation_result.get("title", viz_title)
            recommendation_explanation = recommendation_result.get("explanation", "LLM provided no specific explanation.")
            logger.info(f"LLM recommended: type='{viz_type}', title='{viz_title}'. Exp: {recommendation_explanation}")
        elif isinstance(recommendation_result, tuple) and len(recommendation_result) >= 2:
            viz_type = recommendation_result[0]
            viz_title = recommendation_result[1]
            if len(recommendation_result) > 2 and recommendation_result[2]:
                recommendation_explanation = recommendation_result[2]
            else:
                recommendation_explanation = f"LLM fallback/error: Displaying {viz_type} for '{viz_title}'."
            logger.info(f"LLMInterface returned tuple (possibly fallback): type='{viz_type}', title='{viz_title}'.")
        else:
            logger.warning(f"Unexpected recommendation format: {type(recommendation_result)}. Using defaults.")
        
        return viz_type, viz_title, recommendation_explanation


    def handle_filter_change(self, filters: Dict[str, Any]):
        logger.info(f"Filter change handled: {filters}. Re-processing current query if available.")
        st.session_state.active_filters = filters
        # Potentially refine the current query with filters or just re-run it.
        # For now, let's assume re-running the current query is the desired behavior.
        current_query_to_re_run = st.session_state.get("current_query")
        if current_query_to_re_run:
            logger.info(f"Re-submitting query due to filter change: {current_query_to_re_run}")
            self.handle_query(current_query_to_re_run) # This will re-process and re-render
        else:
            logger.info("No current query to re-process after filter change.")


    def run(self):
        """Main application flow."""
        logger.info("--- FinancialDataApp.run() started ---")
        if st.session_state.get('initialization_failed'):
            logger.error("App initialization failed. Halting run method.")
            return

        st.title("Financial Data Analysis through Natural Language Querying")
        
        # Initialize UI components that require session state to be ready
        if self.sidebar is None:
             self.sidebar = Sidebar(
                available_years=st.session_state.get('available_years', [2020, 2021, 2022, 2023, 2024]),
                on_filter_change=self.handle_filter_change
            )
        if self.query_input is None:
            self.query_input = QueryInput(on_query_submit=self.handle_query) # Pass actual method

        self.sidebar.render()
        natural_language_query = self.query_input.render() # This calls the method on QueryInput instance

        logger.debug(f"Query input rendered, returned NL query: '{natural_language_query}'")
        logger.debug(f"Current session state query: '{st.session_state.get('current_query')}'")

        query_to_process = None
        if natural_language_query: # A new query was submitted via the input box's submit action
            if natural_language_query != st.session_state.get("current_query_processed_flag"): # Check against a flag
                logger.info(f"New query submitted via input: '{natural_language_query}'")
                st.session_state.current_query = natural_language_query # This is the true current query from user
                st.session_state.current_query_processed_flag = natural_language_query # Mark it for processing
                
                # Reset states for a genuinely new query submission
                st.session_state.sql_query = ""
                st.session_state.query_result_df = None # Use a distinct name from old "query_result"
                st.session_state.result_explanation = ""
                st.session_state.error_message = ""
                query_to_process = natural_language_query
            else:
                # Query from input is same as last processed, might be a simple re-run without new submission
                # We still might need to re-process if filters changed, handled by handle_filter_change
                logger.debug("Query from input matches last processed query. Relying on handle_filter_change or existing state for display.")
                query_to_process = st.session_state.current_query # Use existing query if no new one
        
        # Fallback to use current_query from session state if query_input didn't yield a new one
        # This can happen on re-runs not triggered by the query input's submit action (e.g. filter changes)
        if not query_to_process and st.session_state.get("current_query"):
            logger.debug(f"No new query from input, using existing current_query from session_state: '{st.session_state.current_query}'")
            query_to_process = st.session_state.current_query


        if query_to_process:
            logger.info(f"Proceeding to handle query: '{query_to_process}'")
            try:
                self.handle_query(query_to_process)
            except Exception as e:
                logger.error(f"CRITICAL ERROR in app.run() calling handle_query for '{query_to_process}': {str(e)}")
                logger.error(traceback.format_exc()) # Log the full traceback
                st.session_state.error_message = f"A critical error occurred in the application: {str(e)}"
                st.error(st.session_state.error_message) # Display global error
        else:
            logger.info("No query to process in this run.")


        # Simplified end-of-run logic:
        # visualization_display.render_results() is now the primary display mechanism
        # and it handles its own error states and "no data" states.
        # We might only need to display a global error message if one was set.
        if st.session_state.get("error_message") and not query_to_process : # If error happened outside handle_query or before it
             logger.info(f"Displaying global error message from session_state: {st.session_state.error_message}")
             st.error(st.session_state.error_message)
        
        # The message "Query processed, but no data returned or an issue occurred."
        # should ideally be handled within visualization_display.render_results if df is None or empty
        # or if an error occurred during its processing.
        # If handle_query completed and called render_results, that component is responsible.
        # If handle_query didn't run (no query_to_process), then nothing related to query results should be shown.

        logger.info("--- FinancialDataApp.run() finished ---")


def main():
    """Main entry point for the application."""
    # Initialize session state early if needed by app constructor
    if 'current_query' not in st.session_state: # Example pre-init
        st.session_state.current_query = ""
    # ... other pre-initializations if necessary ...

    app = FinancialDataApp()
    app.run()

if __name__ == "__main__":
    main()