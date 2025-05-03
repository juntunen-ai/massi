"""
Prompt templates for LLM interactions.
"""

from typing import Dict, Any, List
import pandas as pd
import json

class PromptTemplates:
    """Class for managing prompt templates for LLM interactions."""
    
    @staticmethod
    def nl_to_sql_prompt(schema: List[Dict[str, Any]], table_name: str, query: str) -> str:
        """
        Generate a prompt for the NL to SQL conversion.
        
        Args:
            schema (List[Dict[str, Any]]): Table schema
            table_name (str): Fully-qualified table name
            query (str): Natural language query
            
        Returns:
            str: Formatted prompt
        """
        # Format schema for the prompt
        schema_str = "\n".join([
            f"- {field['name']} ({field['type']}): {field.get('description', '')}"
            for field in schema
        ])
        
        # Define Finnish government finance domain knowledge
        domain_knowledge = """
        The data contains Finnish government budget and accounting information with these key concepts:
        
        1. Administrative structure:
           - Ha_Tunnus/Hallinnonala: Administrative branch (e.g., 28 = Ministry of Defense, 26 = Ministry of Interior)
           - Tv_Tunnus/Kirjanpitoyksikkö: Accounting unit
        
        2. Budget structure (hierarchy):
           - PaaluokkaOsasto: Main class/section (top level)
           - Luku: Chapter (second level)
           - Momentti: Moment/budget line (third level)
           - TakpT: Budget account (detailed level)
        
        3. Accounting structure:
           - Tililuokka: Account class
           - Ylatiliryhma: Parent account group
           - Tiliryhma: Account group
           - Tililaji: Account type
           - LkpT: Business accounting code
        
        4. Financial values:
           - Alkuperäinen_talousarvio: Original budget allocation
           - Lisätalousarvio: Supplementary budget
           - Voimassaoleva_talousarvio: Current valid budget
           - Käytettävissä: Available funds
           - Alkusaldo: Opening balance
           - Nettokertymä_ko_vuodelta: Net accumulation for the current year
           - NettoKertymaAikVuosSiirrt: Net accumulation from previous years
           - Nettokertymä: Total net accumulation (actual spending/income)
           - Loppusaldo: Closing balance
        """
        
        # Include examples of common query patterns
        examples = """
        Example 1:
        Question: What was the military budget for 2022?
        SQL: 
        ```sql
        SELECT 
          SUM(Alkuperäinen_talousarvio) as original_budget,
          SUM(Voimassaoleva_talousarvio) as current_budget
        FROM 
          `{table_name}`
        WHERE 
          Vuosi = 2022 
          AND Ha_Tunnus = 28
        ```
        
        Example 2:
        Question: Compare defense spending between 2022 and 2023 by quarter
        SQL:
        ```sql
        SELECT 
          Vuosi as year,
          CEIL(Kk/3) as quarter,
          SUM(Voimassaoleva_talousarvio) as budget,
          SUM(Nettokertymä) as spending
        FROM 
          `{table_name}`
        WHERE 
          Vuosi IN (2022, 2023)
          AND Ha_Tunnus = 28
        GROUP BY 
          year, quarter
        ORDER BY 
          year, quarter
        ```
        
        Example 3:
        Question: What has been the development of military budget during 2020-2023?
        SQL:
        ```sql
        SELECT 
          Vuosi as year,
          SUM(Alkuperäinen_talousarvio) as original_budget,
          SUM(Voimassaoleva_talousarvio) as current_budget,
          SUM(Nettokertymä) as spending
        FROM 
          `{table_name}`
        WHERE 
          Vuosi BETWEEN 2020 AND 2023
          AND Ha_Tunnus = 28
        GROUP BY 
          year
        ORDER BY 
          year
        ```
        
        Example 4:
        Question: How did the budget utilization rate of the Ministry of Interior change from 2021 to 2023?
        SQL:
        ```sql
        SELECT 
          Vuosi as year,
          SUM(Voimassaoleva_talousarvio) as budget,
          SUM(Nettokertymä) as actual_spending,
          (SUM(Nettokertymä) / NULLIF(SUM(Voimassaoleva_talousarvio), 0)) * 100 as utilization_percentage
        FROM 
          `{table_name}`
        WHERE 
          Vuosi BETWEEN 2021 AND 2023
          AND Ha_Tunnus = 26
        GROUP BY 
          year
        ORDER BY 
          year
        ```
        """.format(table_name=table_name)
        
        # Build the complete prompt
        prompt = f"""
        You are an expert SQL generator for a Finnish government financial analysis system. 
        Your task is to convert natural language questions about government finances into BigQuery SQL queries.

        Here is the schema of the financial data table:
        Table: `{table_name}`
        
        Fields:
        {schema_str}
        
        {domain_knowledge}
        
        {examples}
        
        Now, please convert the following question to a BigQuery SQL query:
        
        Question: {query}
        
        Please provide the SQL query and a brief explanation of how it answers the question.
        Format your response as:
        
        SQL:
        ```sql
        -- Your SQL query here
        ```
        
        Explanation:
        A brief explanation of how this SQL query addresses the question.
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
        {json.dumps(df_info, indent=2)}
        
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