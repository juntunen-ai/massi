import logging
from typing import Dict, Any, Optional, List, Tuple
import re
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from utils.prompt_templates import PromptTemplates
from google.cloud import secretmanager
from utils.secrets_manager import secrets_manager
import json
from .schema_service import schema_service
from .config_service import config
# from schema_service import schema_service
from google.cloud import aiplatform
import streamlit as st # << ADD THIS to access session_state
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)

class NLToSQLConverter:
    """Class for converting natural language queries to SQL for Finnish financial data."""
    
    def __init__(self, table_name: str):
        """
        Initialize the NL to SQL converter using configuration and schema services.
        """
        self.project_id = config.project_id
        self.location = config.location
        self.model_name = "gemini-2.0-flash-001"  # Or your current chosen model
        self.table_name = table_name  # <-- CRITICAL: Use the table_name passed as an argument
        self.schema = schema_service.get_schema_dict()

        # Fetch the API key from centralized secrets manager
        self.api_key = secrets_manager.get_api_key_ai_studio()
        logger.info(f"NLToSQLConverter initialized WITH table_name: '{self.table_name}'") # Verify this log
    
    # Other methods remain unchanged
    
    def generate_sql(self, natural_language_query: str) -> Tuple[Optional[str], str]:
        """
        Generate SQL from a natural language query.
        
        Args:
            natural_language_query (str): Natural language query
            
        Returns:
            Tuple[Optional[str], str]: Tuple containing the generated SQL query and explanation
        """
        if not self.table_name or not self.schema:
            return None, "Table information not set. Call set_table_info() first."
        
        # Build the prompt for the LLM
        prompt = self._build_prompt(natural_language_query)
        
        try:
            logger.debug(f"Using Vertex AI Model: {self.model_name}")

            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)

            # Use GenerativeModel from vertexai.generative_models
            model = GenerativeModel(self.model_name)

            # Define config as a dictionary
            generation_config_dict = {
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192
            }

            # Generate the SQL using the correct method
            response = model.generate_content(
                prompt,
                generation_config=generation_config_dict
            )

            # Extract SQL and explanation from response
            sql_query, explanation = self._extract_sql_and_explanation(response.text)

            # Clean and validate the SQL
            if sql_query:
                sql_query = self._clean_sql(sql_query)

            return sql_query, explanation

        except GoogleAPIError as e:
            logger.error(f"Google API error generating SQL: {str(e)}")
            return None, f"Error generating SQL: Google API Error - {str(e)}"
        except AttributeError as e:
            logger.error(f"Attribute error likely related to Vertex AI SDK usage: {str(e)}")
            return None, f"Error generating SQL: SDK Error - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {str(e)}")
            return None, f"Error generating SQL: Unexpected error - {str(e)}"
    
    def _build_prompt(self, natural_language_query: str) -> str:
        """
        Build the prompt for the LLM to generate SQL, including active filters and available years.
        """
        schema_desc = "\n".join([
            f"- `{field['name']}` ({field['type']}): {field.get('description', '')}"
            for field in self.schema
        ])  # Added backticks around field names for clarity

        # --- Retrieve active filters from st.session_state ---
        active_filters = st.session_state.get('active_filters', {})
        filter_instructions = []
        year_start_filter = active_filters.get('year_start')
        year_end_filter = active_filters.get('year_end')
        if year_start_filter and year_end_filter:
            if year_start_filter == year_end_filter:
                filter_instructions.append(f"Data must be filtered for the year {year_start_filter}.")
            else:
                filter_instructions.append(f"Data must cover the year range from {year_start_filter} to {year_end_filter} inclusive.")

        filter_prompt_segment = ""
        if filter_instructions:
            filter_prompt_segment = "\nIMPORTANT: Strictly adhere to the following pre-defined filters from the user interface when generating the SQL, in addition to the user's question:\n"
            for instruction in filter_instructions:
                filter_prompt_segment += f"- {instruction}\n"

        # --- Add available years context ---
        available_years = st.session_state.get('available_years', [])
        available_years_info = ""
        if available_years:
            min_year = min(available_years)
            max_year = max(available_years)
            available_years_info = f"\nCONTEXT: The data is available ONLY for the years {min_year} through {max_year} (inclusive). Do not generate SQL for years outside this range unless the user explicitly asks for unavailable years (in which case, still query only the available range or return an appropriate empty result query)."

        # --- Modify Prompt Structure ---
        prompt = f"""
        You are an expert SQL generator for a financial analysis system using Google BigQuery. 
        Your task is to convert natural language questions about Finnish government finances into valid BigQuery SQL queries.

        DATABASE SCHEMA:
        Table Name (MUST be used fully qualified with backticks): `{self.table_name}` 

        Fields:
        {schema_desc}

        Key information about the data:
        - The data contains Finnish government budget and accounting information.
        - `Vuosi` is the year (integer) and `Kk` is the month (integer).
        - `Ha_Tunnus` is the administrative branch code (string, e.g., '26').
        - Financial values include `Alkuperäinen_talousarvio`, `Voimassaoleva_talousarvio`, `Nettokertymä`.
        - The budget structure hierarchy uses `PaaluokkaOsasto`, `Luku`, `Momentti`.

        {available_years_info} # << ADDED AVAILABLE YEARS CONTEXT

        {filter_prompt_segment} # << INSERT UI FILTER INSTRUCTIONS HERE

        IMPORTANT INSTRUCTIONS:
        1. ALWAYS use the fully qualified table name WITH backticks: `{self.table_name}` in the FROM clause.
        2. Use ONLY columns specified in the schema above. Ensure column names with special characters (like Nettokertymä) are enclosed in backticks if needed (though BigQuery standard SQL often doesn't require it unless the name is a reserved keyword or has spaces/invalid chars). Assume standard SQL quoting rules apply.
        3. Adhere strictly to the available data years ({min_year}-{max_year} if available) AND any active filters from the user interface. If the user asks for a year outside the available range (like 2020), generate a query that correctly returns no rows for that year (e.g., by still including it in the WHERE clause but knowing the data isn't there) or adjust the query to only use available years if appropriate for the question.
        4. Generate ONLY the SQL query enclosed between ```sql and ``` tags, followed by a brief explanation starting with "Explanation:".

        Example SQL for the table `{self.table_name}`:
        Question: What was the military budget for 2023?
        SQL: 
        ```sql
        SELECT SUM(`Voimassaoleva_talousarvio`) as current_budget FROM `{self.table_name}` WHERE Vuosi = 2023 AND Ha_Tunnus = '26'
        ```
        Explanation: Calculates the sum of the current budget for the Ministry of Defense (Ha_Tunnus '26') specifically for the year 2023.

        Now, please convert the following question to a BigQuery SQL query adhering to ALL instructions:

        Question: {natural_language_query}
        """

        return prompt

    def _get_example_sql_queries(self) -> str:
        """Helper method to provide example SQL queries for the prompt."""
        return f"""
        Example 1:
        Question: What was the military budget for 2022?
        SQL: 
        ```sql
        SELECT 
          SUM(Alkuperäinen_talousarvio) as original_budget,
          SUM(Voimassaoleva_talousarvio) as current_budget
        FROM 
          `{self.table_name}`
        WHERE 
          Vuosi = 2022 
          AND Ha_Tunnus = '26'
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
          `{self.table_name}`
        WHERE 
          Vuosi IN (2022, 2023)
          AND Ha_Tunnus = '26'
        GROUP BY 
          year, quarter
        ORDER BY 
          year, quarter
        ```
        """
    
    def _extract_sql_and_explanation(self, response_text: str) -> Tuple[Optional[str], str]:
        """
        Extract SQL and explanation from the LLM response.
        
        Args:
            response_text (str): LLM response text
            
        Returns:
            Tuple[Optional[str], str]: SQL query and explanation
        """
        # Extract SQL between ```sql and ``` markers
        sql_match = re.search(r"```sql\s+(.*?)\s+```", response_text, re.DOTALL)
        sql_query = sql_match.group(1).strip() if sql_match else None
        
        # Extract explanation
        explanation_match = re.search(r"Explanation:\s+(.*?)(?:\n\n|$)", response_text, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."
        
        return sql_query, explanation
    
    def _clean_sql(self, sql_query: str) -> str:
        """
        Clean and validate the SQL query, ensuring the correct table name.
        """
        logger.info(f"--- Entering _clean_sql ---") # Using INFO for visibility
        logger.info(f"Original SQL from LLM: '{sql_query}'")

        # self.table_name in NLToSQLConverter is the FQTN from config.table_id
        # e.g., "massi-financial-analysis.finnish_finance_data.budget_transactions"
        # Remove any accidental backticks from the configured FQTN itself for clean processing
        fqtn_from_config_clean = self.table_name.replace("`", "") 

        # Derive the short table name from your configured FQTN
        short_table_name_from_config = fqtn_from_config_clean.split('.')[-1] # e.g., "budget_transactions"

        # This is the target string we want in the SQL query
        target_fqtn_with_backticks = f"`{fqtn_from_config_clean}`" # e.g., "`project.dataset.table`"

        logger.info(f"Configured FQTN (self.table_name): '{self.table_name}'")
        logger.info(f"Derived short table name from config: '{short_table_name_from_config}'")
        logger.info(f"Target FQTN with backticks for replacement: '{target_fqtn_with_backticks}'")

        # The LLM consistently generates the FROM clause with the short table name enclosed in backticks.
        # Example from logs: "FROM `budget_transactions`"

        # Define the exact string fragment the LLM is producing for the FROM clause
        llm_from_clause_fragment = f"FROM `{short_table_name_from_config}`" # e.g., "FROM `budget_transactions`"

        # Define what it should be replaced with
        correct_from_clause = f"FROM {target_fqtn_with_backticks}" # e.g., "FROM `project.dataset.table`"

        logger.info(f"Attempting to replace LLM's table reference: '{llm_from_clause_fragment}' with '{correct_from_clause}'")

        if llm_from_clause_fragment in sql_query:
            sql_query = sql_query.replace(llm_from_clause_fragment, correct_from_clause)
            logger.info(f"SQL after 'FROM' clause replacement: '{sql_query}'")
        else:
            logger.info(f"Exact 'FROM' clause pattern '{llm_from_clause_fragment}' not found in SQL.")
            # You could add more fallbacks here if needed, e.g., for "JOIN `short_table_name`"
            # or if the LLM omits backticks around the short name.
            # For now, let's focus on the observed pattern.

        # Ensure other critical cleaning steps are still performed
        sql_query = self._handle_finnish_characters(sql_query) # Keep this

        logger.info(f"--- FINAL Cleaned SQL for execution: {sql_query} ---")
        return sql_query
    
    def _handle_finnish_characters(self, sql_query: str) -> str:
        """
        Ensures known Finnish column names are correctly backticked in the SQL query
        if they appear as whole words and are not already backticked.
        """
        logger.info(f"--- Entering _handle_finnish_characters ---")
        logger.info(f"SQL before Finnish column backticking: '{sql_query}'")

        # Define your known column names that contain Finnish characters.
        finnish_columns_to_ensure_backticked = [
            "Käytettävissä", "Lisätalousarvio", "Nettokertymä",
            "Nettokertymä_ko_vuodelta", "Kirjanpitoyksikkö", "Loppusaldo",
            "Alkuperäinen_talousarvio", "Voimassaoleva_talousarvio"
            # Add any other relevant column names from your schema if needed
        ]

        processed_sql = sql_query
        for col_name in finnish_columns_to_ensure_backticked:
            # This regex looks for the column name if it's NOT already enclosed in backticks
            # AND is a whole word.
            # (?<![`\w]) - Not preceded by a backtick or word character
            # (?![`\w]) - Not followed by a backtick or word character
            # re.escape(col_name) handles if col_name itself has special regex characters.
            pattern_for_adding_backticks = r'(?<![`\w])(' + re.escape(col_name) + r')(?![`\w])'

            if re.search(pattern_for_adding_backticks, processed_sql):
                 processed_sql = re.sub(pattern_for_adding_backticks, r'`\1`', processed_sql)
                 logger.info(f"Applied/Ensured backticks for column '{col_name}'.")

        logger.info(f"SQL after Finnish column backticking: '{processed_sql}'")
        return processed_sql

class EnhancedNLToSQLConverter:
    def __init__(self, project_id: str, location: str = "europe-north1"):
        """Initialize the enhanced NL to SQL converter."""
        self.project_id = project_id
        self.location = location
        self.model_name = "gemini-2.5-pro-preview-03-25"
        self.table_name = None
        self.schema = None
        
        # Initialize generative AI
        api_key = secrets_manager.get_api_key_ai_studio()
        if not hasattr(genai, '_configured'):
            genai.configure(api_key=api_key)
            genai._configured = True
        
        # Leverage structured output feature
        self.output_schema = {
            "type": "object",
            "properties": {
                "sql": {"type": "string"},
                "explanation": {"type": "string"},
                "confidence": {"type": "number"},
                "assumptions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["sql", "explanation"]
        }
    
    def set_table_info(self, table_name: str, schema: List[Dict[str, Any]]):
        """Set the table information for SQL generation."""
        self.table_name = table_name
        self.schema = schema
    
    def generate_sql(self, natural_language_query: str) -> Dict[str, Any]:
        """Generate SQL using structured output."""
        if not self.table_name or not self.schema:
            return {
                "sql": None,
                "explanation": "Table information not set. Call set_table_info() first.",
                "confidence": 0.0,
                "assumptions": []
            }
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Use structured output feature
            response = model.generate_content(
                [self._build_prompt(natural_language_query)],
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": self.output_schema
                }
            )
            
            # Parse the JSON response
            result = json.loads(response.text)
            
            # Clean and validate the SQL
            if result.get("sql"):
                result["sql"] = self._clean_sql(result["sql"])
            
            return result
            
        except GoogleAPIError as e:
            logger.error(f"Google API error generating SQL: {str(e)}")
            return {
                "sql": None,
                "explanation": f"Error generating SQL: {str(e)}",
                "confidence": 0.0,
                "assumptions": []
            }
        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {str(e)}")
            return {
                "sql": None,
                "explanation": f"Unexpected error: {str(e)}",
                "confidence": 0.0,
                "assumptions": []
            }
    
    def _build_prompt(self, natural_language_query: str) -> str:
        """Build the prompt for the LLM."""
        # Use the enhanced prompt from PromptTemplates
        return PromptTemplates.nl_to_sql_prompt(schema_service.get_schema_dict(), self.table_name, natural_language_query)
    
    def _clean_sql(self, sql_query: str) -> str:
        """Clean and validate the SQL query."""
        # Ensure table name is properly formatted
        sql_query = sql_query.replace("`" + self.table_name + "`", f"`{self.table_name}`")
        
        # Ensure Finnish characters are handled properly
        sql_query = self._handle_finnish_characters(sql_query)
        
        return sql_query
    
    def _handle_finnish_characters(self, sql_query: str) -> str:
        """Ensure Finnish characters (ä, ö) are properly handled in column names."""
        # List of columns with Finnish characters
        finnish_columns = [
            "Käytettävissä",
            "Lisätalousarvio",
            "Nettokertymä",
            "Nettokertymä_ko_vuodelta",
            "Kirjanpitoyksikkö",
            "Loppusaldo",
            "Alkuperäinen_talousarvio"
        ]
        
        # Make sure these columns are properly backticked
        for col in finnish_columns:
            # Replace instances not already backticked
            sql_query = re.sub(r'(?<![`\w])' + col + r'(?![`\w])', '`' + col + '`', sql_query)
        
        return sql_query