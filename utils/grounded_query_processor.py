"""
Grounded query processor using Gemini 2.5 Pro with Google Search.
Enhances queries with current Finnish government financial information.
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from utils.secrets_manager import secrets_manager
from .schema_service import schema_service

logger = logging.getLogger(__name__)

# Initialize the Generative AI API with the API key from secrets_manager
api_key = secrets_manager.get_api_key_ai_studio()
if not hasattr(genai, '_configured'):
    genai.configure(api_key=api_key)
    genai._configured = True

class GroundedQueryProcessor:
    """Query processor with Google Search grounding capabilities."""
    
    def __init__(self, project_id: str, location: str = "europe-north1"):
        """Initialize the grounded query processor."""
        self.project_id = project_id
        self.location = location
        self.model_name = "gemini-exp-1206"
        
        self.model = genai.GenerativeModel(
            self.model_name,
            tools=[{"google_search_retrieval": {}}]
        )
    
    def process_with_grounding(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process query with search grounding for Finnish context.
        
        Args:
            query (str): Natural language query
            context (Dict, optional): Additional context for the query
            
        Returns:
            Dict[str, Any]: Processed query with grounding information
        """
        grounding_prompt = f"""
You are analyzing a query about Finnish government finances. Use Google Search to find recent information about:

1. Current Finnish government budget figures
2. Recent changes to ministry budgets
3. Administrative branch restructuring
4. Currency conversion rates (if applicable)
5. Recent financial decisions or budget amendments

Query to analyze: {query}

Before generating SQL, search for relevant context that might affect:
- Ministry names or codes that have changed
- Recent budget figures that should be used
- Current administrative structure
- Any major financial policy changes

Provide grounded context in this format:
{{
  "search_results": [
    {{
      "title": string,
      "content": string,
      "source": string,
      "relevance": number (0-1)
    }}
  ],
  "relevant_updates": [string],
  "suggested_query_modifications": [string],
  "confidence": number (0-1)
}}
"""
        
        try:
            response = self.model.generate_content(grounding_prompt)
            result = self._parse_grounding_result(response.text)
            
            # Add metadata
            result["query"] = query
            result["grounded"] = True
            result["timestamp"] = self._get_timestamp()
            
            logger.info(f"Query grounding completed with confidence: {result.get('confidence', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"Query grounding failed: {str(e)}")
            return {
                "query": query,
                "grounded": False,
                "error": str(e),
                "search_results": [],
                "relevant_updates": [],
                "suggested_query_modifications": [],
                "confidence": 0.0
            }
    
    def enrich_sql_query(self, sql: str, grounding_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich SQL query with grounding information.
        
        Args:
            sql (str): Original SQL query
            grounding_info (Dict[str, Any]): Grounding information
            
        Returns:
            Dict[str, Any]: Enriched query information
        """
        enrichment_prompt = f"""
Based on the following grounding information, enhance this SQL query if needed:

Original SQL:
```sql
{sql}
```

Grounding Information:
{json.dumps(grounding_info, indent=2)}

Consider:

Do any administrative branch codes need updating?
Should we add WHERE clauses based on relevant updates?
Are there recent budget amendments that affect the query?
Should we adjust the time range based on current information?

Return enhanced SQL and explanation:
{{
"original_sql": string,
"enhanced_sql": string,
"changes_made": [string],
"rationale": string
}}
"""
        try:
            response = self.model.generate_content(enrichment_prompt)
            return self._parse_enrichment_result(response.text)
            
        except Exception as e:
            logger.error(f"SQL enrichment failed: {str(e)}")
            return {
                "original_sql": sql,
                "enhanced_sql": sql,
                "changes_made": [],
                "rationale": f"Enrichment failed: {str(e)}"
            }

    def process_query(self, query: str):
        schema = schema_service.get_schema_dict()
        # Use schema as needed...

    def _parse_grounding_result(self, response_text: str) -> Dict[str, Any]:
        """Parse grounding result from model response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self._extract_structured_data(response_text)
                
        except Exception as e:
            logger.error(f"Failed to parse grounding result: {str(e)}")
            return {
                "search_results": [],
                "relevant_updates": [],
                "suggested_query_modifications": [],
                "confidence": 0.0
            }

    def _parse_enrichment_result(self, response_text: str) -> Dict[str, Any]:
        """Parse enrichment result from model response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to structured parsing
                return {
                    "original_sql": self._extract_sql(response_text, "Original"),
                    "enhanced_sql": self._extract_sql(response_text, "Enhanced"),
                    "changes_made": [],
                    "rationale": response_text
                }
                
        except Exception as e:
            logger.error(f"Failed to parse enrichment result: {str(e)}")
            return {
                "original_sql": "",
                "enhanced_sql": "",
                "changes_made": [],
                "rationale": f"Parsing failed: {str(e)}"
            }

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from free text response."""
        # Basic extraction fallback
        result = {
            "search_results": [],
            "relevant_updates": [],
            "suggested_query_modifications": [],
            "confidence": 0.5
        }
        
        # Try to extract search results
        search_pattern = r'(?:Title|Source):\s*([^\n]+)'
        matches = re.findall(search_pattern, text)
        if matches:
            result["search_results"] = [{"content": match} for match in matches]
        
        # Extract updates
        update_pattern = r'(?:Update|relevant).*?:\s*([^\n]+)'
        updates = re.findall(update_pattern, text, re.IGNORECASE)
        if updates:
            result["relevant_updates"] = updates
        
        return result

    def _extract_sql(self, text: str, prefix: str) -> str:
        """Extract SQL from text based on prefix."""
        pattern = f'{prefix}.*?```sql\\s*([\\s\\S]*?)```'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()