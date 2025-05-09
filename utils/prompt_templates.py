"""
Prompt templates for LLM interactions.
"""

from typing import Dict, Any, List
import pandas as pd
import json
import numpy as np
from utils.schema_service import schema_service

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NpEncoder, self).default(obj)

class PromptTemplates:
    """Class for managing prompt templates for LLM interactions."""
    
    @staticmethod
    def nl_to_sql_prompt(schema: List[Dict[str, Any]], table_name: str, query: str) -> str:
        """
        Generate a prompt for the NL to SQL conversion.
        """
        # Add special instructions for Finnish character handling
        special_instructions = """
        IMPORTANT INSTRUCTIONS FOR HANDLING FINNISH CHARACTERS:
        
        1. Always use backticks (`) for column names with Finnish characters (ä, ö, å)
        2. Column names with special characters include:
           - `Alkuperäinen_talousarvio` (Original budget)
           - `Voimassaoleva_talousarvio` (Current budget)  
           - `Nettokertymä` (Net accumulation)
           - `Käytettävissä` (Available)
           - `Lisätalousarvio` (Supplementary budget)
           - `Loppusaldo` (Closing balance)
           
        3. Numeric vs String types:
           - Ha_Tunnus: INTEGER (administrative branch code)
           - Tililuokka_Tunnus: STRING (account class code)
           - LkpT_Tunnus: STRING (business accounting code)
        
        4. Common patterns:
           - Defense/Military queries: Use Ha_Tunnus = 26
           - Education queries: Use Ha_Tunnus = 29
           - Finance ministry: Use Ha_Tunnus = 23
           - For "budget" use `Voimassaoleva_talousarvio`
           - For "spending" use `Nettokertymä`
        """
        
        # Enhanced examples with proper Finnish character handling
        examples = """
        Example 1:
        Question: What was the military budget for 2022?
        SQL: 
        ```sql
        SELECT 
          SUM(`Alkuperäinen_talousarvio`) as original_budget,
          SUM(`Voimassaoleva_talousarvio`) as current_budget
        FROM 
          `{table_name}`
        WHERE 
          Vuosi = 2022 
          AND Ha_Tunnus = 26
        ```
        
        Example 2:
        Question: How has military spending developed from 2020 to 2024?
        SQL:
        ```sql
        SELECT 
          Vuosi as year,
          SUM(`Alkuperäinen_talousarvio`) as original_budget,
          SUM(`Voimassaoleva_talousarvio`) as current_budget,
          SUM(`Nettokertymä`) as actual_spending
        FROM 
          `{table_name}`
        WHERE 
          Vuosi BETWEEN 2020 AND 2024
          AND Ha_Tunnus = 26
        GROUP BY 
          year
        ORDER BY 
          year
        ```
        """.format(table_name=table_name)
        
        # Rest of the prompt remains the same, but add special_instructions before examples
        schema_str = "\n".join([
            f"- {field['name']} ({field['type']}): {field.get('description', '')}"
            for field in schema
        ])

        prompt = f"""
        You are a Finnish government financial data SQL expert using Gemini's thinking mode.

        <thinking>
        Before generating SQL, I should:
        1. Identify the Finnish financial concepts mentioned in the query
        2. Map them to correct database columns (remembering Finnish characters like ä, ö)
        3. Consider the budget hierarchy (Paaluokka -> Luku -> Momentti)
        4. Handle Finnish language variations properly (e.g., "puolustus" = "defense")
        5. Determine the appropriate aggregation level and time period
        6. Check if the query requires comparison or trend analysis
        </thinking>

        Table: `{table_name}`

        Schema:
        {schema_str}

        {special_instructions}

        {examples}

        Query: {query}

        Generate structured output with these fields:
        1. "sql": The SQL query
        2. "explanation": Explanation in natural language  
        3. "confidence": Confidence score (0-1)
        4. "assumptions": List of assumptions made (if any)

        Example output format:
        {{
          "sql": "SELECT ...",
          "explanation": "This query calculates...",
          "confidence": 0.95,
          "assumptions": ["Assuming question refers to Ministry of Defense", "Using net accumulation as spending measure"]
        }}
        """
        
        return prompt

    @staticmethod
    def results_explanation_prompt(query: str, sql: str, df: pd.DataFrame, visualization_type: str) -> str:
        """
        Generate a prompt for explaining the query results in natural language.
        
        Args:
            query (str): Original natural language query
            sql (str): SQL query used
            df (pd.DataFrame): Query results as DataFrame
            visualization_type (str): Type of visualization created
            
        Returns:
            str: Formatted prompt
        """
        # Convert DataFrame to JSON for the prompt
        df_sample = df.head(50)  # Limit to 50 rows to keep prompt size reasonable
        try:
            df_json = df_sample.to_json(orient='records', date_format='iso')
        except:
            # Fall back to a simpler format if JSON conversion fails
            df_json = str(df_sample.to_dict(orient='records'))
        
        # Create a summary of the data shape
        data_summary = f"Data has {len(df)} rows and {len(df.columns)} columns: {', '.join(df.columns)}"
        
        # Add statistical summary for numeric columns
        numeric_summary = ""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            numeric_summary = "Statistical summary of numeric columns:\n"
            for col in numeric_cols:
                numeric_summary += f"- {col}: min={df[col].min()}, max={df[col].max()}, mean={df[col].mean()}, sum={df[col].sum()}\n"
        
        # Build the complete prompt
        prompt = f"""
        You are a financial data analyst specializing in Finnish government finances. Your task is to explain the results of a data query in clear, natural language.

        Original question: {query}
        
        SQL query used:
        ```sql
        {sql}
        ```
        
        {data_summary}
        
        {numeric_summary}
        
        Data (sample of {len(df_sample)} rows):
        {df_json}
        
        Visualization type chosen: {visualization_type}
        
        Please provide:
        1. A concise summary of what the data shows, directly answering the original question
        2. Key insights or trends visible in the data
        3. Any interesting observations or anomalies
        4. Context about what this means for Finnish government finances (if applicable)
        
        Write in a clear, professional tone that would be appropriate for a government analyst. Use specific numbers and percentages from the data to support your points. Remember that all monetary values are in euros.
        
        Keep your explanation concise but thorough, focusing on the most important findings first.
        """
        
        return prompt

    @staticmethod
    def visualization_recommendation_prompt(query: str, df: pd.DataFrame) -> str:
        """
        Generate a prompt for recommending a visualization type.
        
        Args:
            query (str): Original natural language query
            df (pd.DataFrame): Query results as DataFrame
            
        Returns:
            str: Formatted prompt
        """
        # Convert DataFrame info to JSON for the prompt
        df_info = {
            "rows": len(df),
            "columns": list(df.columns),
            "column_types": {col: str(df[col].dtype) for col in df.columns},
            "sample_values": {col: df[col].iloc[0] if len(df) > 0 else None for col in df.columns}
        }
        
        # Build the complete prompt
        prompt = f"""
        You are a data visualization expert. Your task is to recommend the best visualization type for a given dataset and query.

        Original question: {query}
        
        Dataset information:
        {json.dumps(df_info, indent=2, cls=NpEncoder)}
        
        Available visualization types:
        - time_line: Line chart for time series with a single metric
        - time_multi_line: Line chart for time series with multiple metrics
        - bar: Bar chart for categorical comparisons
        - time_bar: Bar chart for time-based data
        - pie: Pie chart for showing proportions (only for small number of categories)
        - table: Table for detailed data viewing
        
        Please provide:
        1. The recommended visualization type (one of the options above)
        2. A brief explanation of why this visualization is appropriate
        3. Suggested title for the visualization
        
        Format your response as a JSON object:
        {{
            "viz_type": "recommended_type",
            "explanation": "Brief explanation of the recommendation",
            "title": "Suggested visualization title"
        }}
        """
        
        return prompt