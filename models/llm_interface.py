"""
Interface for interacting with LLMs for natural language processing tasks.
"""

import logging
import json
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple, Union
from google.cloud import aiplatform
from google.api_core.exceptions import GoogleAPIError
from utils.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for interacting with LLMs."""
    
    def __init__(self, project_id: str, location: str = "europe-west4"):
        """
        Initialize the LLM interface.
        
        Args:
            project_id (str): Google Cloud project ID
            location (str): Vertex AI location
        """
        self.project_id = project_id
        self.location = location
        self.gemini_model = "gemini-1.5-pro"
        self.vertex_initialized = False
        
    def _init_vertex_ai(self):
        """Initialize Vertex AI if not already initialized."""
        if not self.vertex_initialized:
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                self.vertex_initialized = True
            except Exception as e:
                logger.error(f"Error initializing Vertex AI: {str(e)}")
                raise
    
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
            # Initialize Vertex AI
            self._init_vertex_ai()
            
            # Create the prompt
            prompt = PromptTemplates.nl_to_sql_prompt(schema, table_name, query)
            
            # Get the model
            model = aiplatform.Vertex(model_name=self.gemini_model)
            
            # Log the prompt
            logger.info(f"Sending NL to SQL prompt to Gemini: {prompt[:500]}...")
            
            # Generate the SQL
            response = model.predict(prompt=prompt)
            
            # Extract SQL and explanation
            sql, explanation = self._extract_sql_and_explanation(response.text)
            
            if sql:
                logger.info(f"Generated SQL query: {sql}")
            else:
                logger.warning("Failed to extract SQL from response")
            
            return sql, explanation
            
        except GoogleAPIError as e:
            logger.error(f"Google API error generating SQL: {str(e)}")
            return None, f"Error generating SQL: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {str(e)}")
            return None, f"Unexpected error: {str(e)}"
    
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
            # Initialize Vertex AI
            self._init_vertex_ai()
            
            # Create the prompt
            prompt = PromptTemplates.results_explanation_prompt(query, sql, df, visualization_type)
            
            # Get the model
            model = aiplatform.Vertex(model_name=self.gemini_model)
            
            # Generate the explanation
            response = model.predict(prompt=prompt)
            
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
        try:
            # Initialize Vertex AI
            self._init_vertex_ai()
            
            # Create the prompt
            prompt = PromptTemplates.visualization_recommendation_prompt(query, df)
            
            # Get the model
            model = aiplatform.Vertex(model_name=self.gemini_model)
            
            # Generate the recommendation
            response = model.predict(prompt=prompt)
            
            # Parse the JSON response
            try:
                recommendation = json.loads(response.text)
                return recommendation
            except json.JSONDecodeError:
                logger.error(f"Error parsing visualization recommendation: {response.text}")
                # Fall back to default recommendation
                return {
                    "viz_type": "table",
                    "explanation": "Defaulting to table view due to error parsing recommendation",
                    "title": query.capitalize()
                }
            
        except Exception as e:
            logger.error(f"Error recommending visualization: {str(e)}")
            # Fall back to default recommendation
            return {
                "viz_type": "table",
                "explanation": f"Error generating recommendation: {str(e)}",
                "title": query.capitalize()
            }
    
    def analyze_question(self, query: str) -> Dict[str, Any]:
        """
        Analyze a natural language question to extract intent and parameters.
        
        Args:
            query (str): Natural language query
            
        Returns:
            Dict[str, Any]: Analysis of the question intent and parameters
        """
        try:
            # Initialize Vertex AI
            self._init_vertex_ai()
            
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
            model = aiplatform.Vertex(model_name=self.gemini_model)
            
            # Generate the analysis
            response = model.predict(prompt=prompt)
            
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