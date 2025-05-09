"""
Interface for interacting with LLMs for natural language processing tasks.
"""

import logging
import json
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple, Union
from google.cloud import secretmanager
import google.generativeai as genai  # For the Gemini API
from google.api_core.exceptions import GoogleAPIError
from utils.prompt_templates import PromptTemplates
from google.auth import default
from utils.errors import SQLGenerationError
from google.cloud import aiplatform
from google.generativeai.types import GenerationConfig
import os
from google.oauth2 import service_account
import google.auth
import streamlit as st

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for interacting with LLMs."""

    def __init__(self, project_id: str, location: str = "europe-north1"):
        """
        Initialize the LLM interface.

        Args:
            project_id (str): Google Cloud project ID
            location (str): Location (not used for Generative AI API)
        """
        self.project_id = project_id
        self.location = location
        # Use the correct model identifier for Vertex AI
        self.gemini_model = "gemini-1.5-pro"  # Updated to latest stable version

        # Get API key from Secret Manager
        self.api_key = self._get_api_key_from_secret_manager()

        # Configure the genai client
        api_key = os.environ.get("GOOGLE_API_KEY")
        if (api_key):
            genai.configure(api_key=api_key)
        else:
            # Use application default credentials
            credentials, project = google.auth.default()
            genai.configure(credentials=credentials)

    def _get_api_key_from_secret_manager(self) -> str:
        """Get API key from Secret Manager."""
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{self.project_id}/secrets/gemini-api-key-ai-studio/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    def _init_vertex_ai(self):
        """Initialize Vertex AI if not already initialized."""
        if not self.vertex_initialized:
            try:
                # Add authentication check
                from google.auth import default

                # Get credentials
                credentials, project = default()

                # Initialize with credentials
                aiplatform.init(
                    project=self.project_id, 
                    location=self.location,
                    credentials=credentials
                )
                self.vertex_initialized = True
            except Exception as e:
                logger.error(f"Error initializing Vertex AI: {str(e)}")
                logger.warning("LLM functionality will be disabled")
                # Don't re-raise the exception, so other parts of code can continue
                self.vertex_initialized = False

    def generate_sql(self, query: str, schema: List[Dict[str, Any]], 
                    table_name: str) -> Tuple[Optional[str], str]:
        """
        Generate SQL from a natural language query.

        Args:
            query (str): Natural language query
            schema (List[Dict[str, Any]]): Table schema
            table_name (str): Fully-qualified table name

        Returns:
            Tuple[Optional[str], str]: Generated SQL and explanation
        """
        try:
            # Ensure query is properly encoded for Finnish characters
            query = query.encode('utf-8').decode('utf-8')
        
            # Create the prompt
            prompt = PromptTemplates.nl_to_sql_prompt(schema, table_name, query)

            # Get the model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=GenerationConfig(
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192
                )
            )

            # Generate content
            response = model.generate_content(prompt)

            # Extract SQL and explanation
            sql, explanation = self._extract_sql_and_explanation(response.text)

            if sql:
                logger.info(f"Generated SQL query: {sql}")
            else:
                logger.warning("Failed to extract SQL from response")

            return sql, explanation

        except GoogleAPIError as e:
            logger.error(f"Google API error generating SQL: {str(e)}")
            raise SQLGenerationError(f"Failed to generate SQL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {str(e)}")
            raise SQLGenerationError(f"Unexpected error: {str(e)}")

    def _extract_sql_and_explanation(self, response_text: str) -> Tuple[Optional[str], str]:
        """
        Extract SQL and explanation from LLM response.

        Args:
            response_text (str): LLM response text

        Returns:
            Tuple[Optional[str], str]: SQL query and explanation
        """
        import re

        # Extract SQL between ```sql and ``` markers
        sql_match = re.search(r"```sql\s+(.*?)\s+```", response_text, re.DOTALL)
        sql_query = sql_match.group(1).strip() if sql_match else None

        # Extract explanation after the "Explanation:" marker
        explanation_match = re.search(r"Explanation:\s+(.*?)(?:\n\n|$)", response_text, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."

        return sql_query, explanation
    
    def explain_results(self, query: str, sql: str, df: pd.DataFrame, 
                       visualization_type: str) -> str:
        """
        Generate a natural language explanation of query results.
        
        Args:
            query (str): Original natural language query
            sql (str): SQL query used
            df (pd.DataFrame): Query results as DataFrame
            visualization_type (str): Type of visualization created
            
        Returns:
            str: Natural language explanation of results
        """
        try:
            # Create the prompt
            prompt = PromptTemplates.results_explanation_prompt(query, sql, df, visualization_type)
            
            # Get the model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=GenerationConfig(
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192
                )
            )
            
            # Generate the explanation
            response = model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error explaining results: {str(e)}")
            return f"I encountered an error while analyzing the results: {str(e)}"
    
    def recommend_visualization(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Recommend a visualization type based on the query and data.
        
        Args:
            query (str): Original natural language query
            df (pd.DataFrame): Query results as DataFrame
            
        Returns:
            Dict[str, Any]: Visualization recommendation
        """
        import re

        try:
            # Create the prompt
            prompt = PromptTemplates.visualization_recommendation_prompt(query, df)
            
            # Get the model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=GenerationConfig(
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192
                )
            )
            
            # Generate the recommendation
            response = model.generate_content(prompt)
            response_text = response.text  # Get raw text

            # --- ADD/MODIFY PRE-PROCESSING TO STRIP MARKDOWN ---
            json_string = response_text  # Default to raw text
            # Look for ```json ... ``` block
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_string = json_match.group(1).strip()  # Extract content within backticks
            else:
                # Optional: if no ```json found, try removing ``` if they exist without json specifier
                json_match_plain = re.search(r"```\s*(.*?)\s*```", response_text, re.DOTALL)
                if json_match_plain:
                    json_string = json_match_plain.group(1).strip()
                else:
                    # If no backticks at all, just strip whitespace
                    json_string = response_text.strip()
            # --- END PRE-PROCESSING ---

            # Parse the cleaned JSON string
            recommendation = json.loads(json_string)
            # (Add logging here if needed: logger.debug(f"Successfully parsed recommendation: {recommendation}"))

            # --- The rest of your existing logic to extract viz_type, title etc. from recommendation ---
            viz_type = recommendation.get("viz_type", "table")
            viz_title = recommendation.get("title", query.capitalize() if query else "Visualization")
            st.session_state.last_viz_title = viz_title  # Store for potential reuse
            recommendation_explanation = recommendation.get("explanation", "No explanation provided for recommendation.")

            logger.info(f"LLM recommended visualization: type='{viz_type}', title='{viz_title}'. Explanation: {recommendation_explanation}")
            # Note: This method in your app.py was expected to return a tuple (viz_type, viz_title)
            # Ensure this method returns that, not the full recommendation dict, to match app.py's usage.
            return viz_type, viz_title  # Make sure return matches expected type

        except json.JSONDecodeError:
            # Log the string that failed to parse
            logger.error(f"Error parsing visualization recommendation JSON: '{json_string}'")
            # Fall back to default recommendation - return tuple
            return "table", query.capitalize() if query else "Data Table"
        except Exception as e:
            logger.error(f"Exception in recommend_visualization: {str(e)}. Falling back to default.", exc_info=True)
            # Fall back to default recommendation - return tuple
            return "table", query.capitalize() if query else "Data Table"
    
    def analyze_question(self, query: str) -> Dict[str, Any]:
        """
        Analyze a natural language question to extract intent and parameters.
        
        Args:
            query (str): Natural language query
            
        Returns:
            Dict[str, Any]: Analysis of the question intent and parameters
        """
        try:
            # Create the prompt for question analysis
            prompt = f"""
            You are a financial data query analyzer. Your task is to analyze a question about Finnish government finances and extract the key parameters.
            
            Question: {query}
            
            Please analyze this question and extract the following information:
            
            1. Time period: What years or time range is the user asking about?
            2. Administrative branches: Which ministries or departments is the user interested in?
            3. Financial metrics: Which financial metrics (budget, spending, etc.) is the user interested in?
            4. Aggregation: What level of detail is requested (yearly, quarterly, monthly)?
            5. Visualization intent: Does the question imply a specific visualization (comparison, trend, breakdown)?
            
            Format your response as a JSON object:
            {{
                "time_period": {{
                    "start_year": <year or null>,
                    "end_year": <year or null>,
                    "specific_year": <year or null>
                }},
                "administrative_branches": [<list of branch codes or names>],
                "metrics": [<list of requested metrics>],
                "aggregation": "<yearly|quarterly|monthly>",
                "visualization_intent": "<comparison|trend|breakdown|detailed>"
            }}
            """
            
            # Get the model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=GenerationConfig(
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192
                )
            )
            
            # Generate the analysis
            response = model.generate_content(prompt)
            
            # Parse the JSON response
            try:
                analysis = json.loads(response.text)
                return analysis
            except json.JSONDecodeError:
                logger.error(f"Error parsing question analysis: {response.text}")
                # Return empty analysis
                return {
                    "time_period": {"start_year": None, "end_year": None, "specific_year": None},
                    "administrative_branches": [],
                    "metrics": [],
                    "aggregation": "yearly",
                    "visualization_intent": "detailed"
                }
            
        except Exception as e:
            logger.error(f"Error analyzing question: {str(e)}")
            # Return empty analysis
            return {
                "time_period": {"start_year": None, "end_year": None, "specific_year": None},
                "administrative_branches": [],
                "metrics": [],
                "aggregation": "yearly",
                "visualization_intent": "detailed"
            }

    def extract_sql_from_response(self, response):
        """Extract SQL query from Gemini model response."""
        try:
            # Get text from response based on Gemini 1.5 response format
            if hasattr(response, 'text'):
                content = response.text
            elif hasattr(response, 'parts') and response.parts:
                content = response.parts[0].text
            elif hasattr(response, 'candidates') and response.candidates:
                content = response.candidates[0].content.parts[0].text
            else:
                logging.error(f"Unexpected response format: {type(response)}")
                logging.debug(f"Response content: {response}")
                return None

            # Extract SQL between markdown code blocks
            import re
            sql_match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
                logging.debug(f"Extracted SQL: {sql}")
                return sql

            # Fallback: try without language specifier
            sql_match = re.search(r'```\s*(SELECT.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
            if sql_match:
                sql = sql_match.group(1).strip()
                logging.debug(f"Extracted SQL (fallback): {sql}")
                return sql

            # Fallback: look for anything that looks like SQL
            sql_match = re.search(r'(SELECT\s+.+?FROM\s+.+?(?:WHERE|GROUP BY|ORDER BY|LIMIT|$).*)', content, re.DOTALL | re.IGNORECASE)
            if sql_match:
                sql = sql_match.group(1).strip()
                logging.debug(f"Extracted SQL (raw): {sql}")
                return sql

            logging.warning("Failed to extract SQL from response")
            logging.debug(f"Full response content: {content}")
            return None

        except Exception as e:
            logging.error(f"Error extracting SQL: {e}")
            return None

    def generate_sql_query(self, user_query, schema_info):
        """Generate SQL query for the given user query."""
        try:
            prompt = f"""
You are a SQL query generator for a financial analysis application.

DATABASE SCHEMA:
{schema_info}

USER QUERY: {user_query}

Your task is to write a SQL query that answers the user query.
The query will be executed against a BigQuery database with Finnish finance data.

IMPORTANT INSTRUCTIONS:
1. Your response must contain only a single SQL query.
2. The SQL query must be enclosed between ```sql and ``` tags.
3. Use standard BigQuery SQL syntax.
4. Do not include any explanations, only the SQL query.
5. Ensure proper handling of UTF-8 characters in column names.
6. Be sure to use ONLY columns specified in the schema above.

Example response format:
```sql
SELECT column FROM table WHERE condition;
"""
            # Generate response with Gemini 1.5 Pro
            response = self.model.generate_content(prompt)

            # Extract SQL from response
            sql = self.extract_sql_from_response(response)
            if not sql:
                logging.warning("Failed to extract SQL from response")
                return None

            return sql

        except Exception as e:
            logging.error(f"Error generating SQL query: {e}")
            return None

    def generate_sql_with_fallbacks(self, user_query, schema_info):
        """Generate SQL with multiple fallback strategies."""
        try:
            # First attempt with standard prompt
            sql = self.generate_sql_query(user_query, schema_info)
            if sql:
                return sql

            # Second attempt with more structured prompt
            logging.info("First SQL generation attempt failed, trying with structured prompt")
            sql = self.generate_structured_sql_query(user_query, schema_info)
            if sql:
                return sql

            # Third attempt with examples
            logging.info("Second SQL generation attempt failed, trying with examples")
            sql = self.generate_sql_query_with_examples(user_query, schema_info)
            if sql:
                return sql

            # All attempts failed
            logging.error("All SQL generation attempts failed")
            return None

        except Exception as e:
            logging.error(f"Error in SQL generation pipeline: {e}")
            return None

    def generate_structured_sql_query(self, user_query, schema_info):
        """Generate SQL with more structured prompt."""
        # Implementation similar to generate_sql_query but with a more structured prompt
        pass

    def generate_sql_query_with_examples(self, user_query, schema_info):
        """Generate SQL with example queries included in the prompt."""
        # Implementation with examples included
        pass

    def run_diagnostics(self):
        """Run diagnostics on the LLM interface."""
        results = {
            "status": "initialized",
            "errors": []
        }

        try:
            # Test 1: Check if genai is properly configured
            logging.info("Testing genai configuration...")
            models = genai.list_models()
            available_models = [model.name for model in models if "gemini" in model.name.lower()]
            results["available_models"] = available_models
            logging.info(f"Available Gemini models: {available_models}")

            # Test 2: Check if our target model is available
            target_model = "gemini-1.5-pro"
            if any(target_model in model for model in available_models):
                logging.info(f"Target model {target_model} is available")
                results["target_model_available"] = True
            else:
                msg = f"Target model {target_model} not found in available models"
                logging.warning(msg)
                results["target_model_available"] = False
                results["errors"].append(msg)

            # Test 3: Try a simple generation
            logging.info("Testing simple content generation...")
            prompt = "Generate a simple SELECT statement from a table called 'users'"
            try:
                response = self.model.generate_content(prompt)
                if hasattr(response, 'text'):
                    results["test_generation"] = "success"
                    results["test_response"] = response.text[:100] + "..." # Truncate for logging
                    logging.info(f"Test generation successful. Response starts with: {response.text[:50]}...")
                else:
                    msg = f"Unexpected response format: {type(response)}"
                    logging.warning(msg)
                    results["test_generation"] = "unexpected_format"
                    results["errors"].append(msg)
            except Exception as e:
                msg = f"Test generation failed: {str(e)}"
                logging.error(msg)
                results["test_generation"] = "failed"
                results["errors"].append(msg)

            # Final status
            if not results["errors"]:
                results["status"] = "healthy"
            else:
                results["status"] = "issues_detected"

            return results

        except Exception as e:
            logging.error(f"Diagnostics failed: {e}")
            results["status"] = "diagnostics_failed"
            results["errors"].append(str(e))
            return results