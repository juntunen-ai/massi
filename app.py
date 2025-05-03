import streamlit as st
import pandas as pd
import os
import logging
from google.cloud import bigquery
from utils.nl_to_sql import NLToSQLConverter
from utils.api_client import TutkihallintoaAPI
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_ID = os.getenv('DATASET_ID')
TABLE_ID = os.getenv('TABLE_ID')
FULLY_QUALIFIED_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Initialize BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID)

def get_table_schema():
    """Get the schema of the BigQuery table."""
    try:
        table = bq_client.get_table(FULLY_QUALIFIED_TABLE)
        return [
            {
                "name": field.name,
                "type": field.field_type,
                "description": field.description or ""
            }
            for field in table.schema
        ]
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        return []

def execute_query(sql):
    """Execute a BigQuery SQL query and return the results as a DataFrame."""
    try:
        query_job = bq_client.query(sql)
        return query_job.to_dataframe()
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        st.error(f"Error executing query: {str(e)}")
        return None

def generate_visualization(df, query):
    """Generate an appropriate visualization for the query results."""
    if df is None or df.empty:
        return None
    
    # Determine the type of visualization based on the data and query
    time_series = False
    comparison = False
    single_value = False
    
    # Check if we have year/time columns
    has_year = any(col.lower() in ['year', 'vuosi'] for col in df.columns)
    
    # Check if we have numeric columns for values
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Determine visualization type based on query and data
    if len(df) == 1 and len(df.columns) <= 2:
        single_value = True
    elif has_year and len(numeric_cols) >= 1:
        time_series = True
        if 'quarter' in df.columns or 'month' in df.columns or 'kk' in df.columns:
            time_series = True
        if 'hallinnonala' in [c.lower() for c in df.columns]:
            comparison = True
    
    # Create appropriate visualization
    fig = None
    
    if single_value:
        # For single values, create a big number display
        st.subheader("Result")
        value_col = numeric_cols[0] if numeric_cols else df.columns[-1]
        metric_name = df.columns[0] if df.columns[0] != value_col else "Value"
        st.metric(label=metric_name, value=df.iloc[0][value_col])
        
    elif time_series and not comparison:
        # For time series, create a line chart
        time_col = 'year' if 'year' in df.columns else 'Vuosi' if 'Vuosi' in df.columns else df.columns[0]
        
        fig = px.line(
            df, 
            x=time_col, 
            y=numeric_cols,
            title="Financial Data Trend",
            markers=True,
            template="plotly_white"
        )
        fig.update_layout(
            xaxis_title=time_col,
            yaxis_title="Value (€)",
            legend_title="Metric"
        )
        
    elif comparison:
        # For comparisons between categories, create a bar chart
        category_col = 'hallinnonala' if 'hallinnonala' in [c.lower() for c in df.columns] else df.columns[0]
        
        fig = px.bar(
            df,
            x=category_col,
            y=numeric_cols[0] if numeric_cols else df.columns[-1],
            title="Comparison",
            template="plotly_white"
        )
        fig.update_layout(
            xaxis_title=category_col,
            yaxis_title="Value (€)"
        )
        
    else:
        # Default to table view for other types of data
        st.subheader("Results")
        st.dataframe(df)
    
    return fig

def main():
    st.set_page_config(
        page_title="Finnish Financial Data Analysis",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Finnish Government Financial Data Analysis")
    st.subheader("Natural Language Query System")
    
    # Sidebar information
    with st.sidebar:
        st.header("About this App")
        st.write("""
        This application allows you to analyze Finnish government financial data using natural language.
        
        Simply enter your question about budget allocations, spending, or other financial metrics, and the system will 
        generate the appropriate analysis and visualization.
        
        Examples:
        - What was the military budget for 2022?
        - Compare defense spending between 2022 and 2023 by quarter
        - What has been the development of military budget during 2022-2024?
        """)
        
        st.subheader("Data Source")
        st.write("Data is sourced from the Tutkihallintoa API, which provides detailed Finnish government financial data.")
        
        # Add data refresh option
        if st.button("Refresh Data (Admin)"):
            with st.spinner("Refreshing data from API..."):
                # This would trigger a data refresh pipeline in production
                st.success("Data refresh initiated. This may take some time to complete.")
    
    # Main query area
    query = st.text_input(
        "Enter your financial data query:",
        placeholder="E.g., What has been the development of military budget during 2022-2024?"
    )
    
    # SQL toggle for advanced users
    use_sql = st.checkbox("Use direct SQL instead of natural language")
    
    if use_sql:
        sql_query = st.text_area(
            "Enter SQL query:",
            placeholder="SELECT\n  Vuosi as year,\n  SUM(Voimassaoleva_talousarvio) as budget\nFROM\n  `project.dataset.table`\nWHERE\n  Vuosi BETWEEN 2022 AND 2024\nGROUP BY\n  year\nORDER BY\n  year"
        )
    
    if st.button("Analyze"):
        if (use_sql and sql_query) or (not use_sql and query):
            with st.spinner("Processing query..."):
                if use_sql:
                    # Execute SQL directly
                    final_sql = sql_query.replace("project.dataset.table", FULLY_QUALIFIED_TABLE)
                    st.code(final_sql, language="sql")
                    df = execute_query(final_sql)
                else:
                    # Convert natural language to SQL
                    nl_to_sql = NLToSQLConverter(PROJECT_ID)
                    nl_to_sql.set_table_info(FULLY_QUALIFIED_TABLE, get_table_schema())
                    
                    generated_sql, explanation = nl_to_sql.generate_sql(query)
                    
                    if generated_sql:
                        st.subheader("Generated SQL")
                        st.code(generated_sql, language="sql")
                        
                        st.subheader("Explanation")
                        st.write(explanation)
                        
                        # Execute the generated SQL
                        df = execute_query(generated_sql)
                    else:
                        st.error(f"Failed to generate SQL: {explanation}")
                        df = None
                
                # Display results and visualization
                if df is not None and not df.empty:
                    st.subheader("Results")
                    st.dataframe(df)
                    
                    # Generate visualization
                    fig = generate_visualization(df, query if not use_sql else sql_query)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Download options
                    st.download_button(
                        label="Download Results as CSV",
                        data=df.to_csv(index=False).encode('utf-8'),
                        file_name='financial_analysis_results.csv',
                        mime='text/csv'
                    )
        else:
            st.warning("Please enter a query to analyze.")

if __name__ == "__main__":
    main()