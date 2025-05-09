"""
SQL validator with Gemini 2.5 Pro's code execution tool.
Validates SQL queries before execution in BigQuery.
"""

import logging
import re
import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai

logger = logging.getLogger(__name__)

class SQLValidator:
    """SQL validator using Gemini 2.5 Pro's code execution capabilities."""
    
    def __init__(self, project_id: str, location: str = "europe-north1"):
        """Initialize the SQL validator."""
        self.project_id = project_id
        self.location = location
        self.model_name = "gemini-2.5-pro-preview-03-25"
        
        # Initialize the generative AI model
        self.model = genai.GenerativeModel(
            self.model_name,
            tools=[{"code_execution": {}}]
        )
    
    def validate_sql(self, sql: str, schema: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate SQL query with code execution.
        
        Args:
            sql (str): SQL query to validate
            schema (List[Dict[str, Any]]): Table schema
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation_prompt = f"""
Validate this SQL query for Finnish government financial data:

```sql
{sql}
```

Schema:
{self._format_schema(schema)}

Check for:

SQL syntax correctness
Column names exist in schema (including Finnish characters: ä, ö)
Appropriate aggregations for financial data
Proper handling of time fields (Vuosi, Kk)
Administrative branch codes (Ha_Tunnus) are valid
Finnish column names are properly backticked

Execute validation checks using code execution. Return results as JSON:
{{
"is_valid": boolean,
"syntax_errors": [list of syntax errors],
"field_errors": [list of invalid field references],
"warnings": [list of warnings],
"suggestions": [list of improvement suggestions]
}}
"""

        try:
            response = self.model.generate_content(validation_prompt)
            
            # Parse the validation result
            result = self._parse_validation_result(response.text)
            
            # Additional custom validation
            custom_checks = self._perform_custom_validation(sql, schema)
            
            # Merge results
            final_result = self._merge_validation_results(result, custom_checks)
            
            logger.info(f"SQL validation completed: {final_result['is_valid']}")
            return final_result
            
        except Exception as e:
            logger.error(f"SQL validation failed: {str(e)}")
            return {
                "is_valid": False,
                "syntax_errors": [f"Validation failed: {str(e)}"],
                "field_errors": [],
                "warnings": [],
                "suggestions": []
            }

    def _format_schema(self, schema: List[Dict[str, Any]]) -> str:
        """Format schema for validation prompt."""
        return "\n".join([
            f"- {field['name']} ({field['type']})"
            for field in schema
        ])

    def _parse_validation_result(self, response_text: str) -> Dict[str, Any]:
        """Parse validation result from model response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                return {
                    "is_valid": False,
                    "syntax_errors": ["Could not parse validation result"],
                    "field_errors": [],
                    "warnings": [],
                    "suggestions": []
                }
        except Exception as e:
            logger.error(f"Failed to parse validation result: {str(e)}")
            return {
                "is_valid": False,
                "syntax_errors": [f"JSON parsing error: {str(e)}"],
                "field_errors": [],
                "warnings": [],
                "suggestions": []
            }

    def _perform_custom_validation(self, sql: str, schema: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform additional custom validation checks."""
        result = {
            "is_valid": True,
            "syntax_errors": [],
            "field_errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check for Finnish character handling
        finnish_columns = [
            "Käytettävissä", "Lisätalousarvio", "Nettokertymä",
            "Nettokertymä_ko_vuodelta", "Kirjanpitoyksikkö", "Loppusaldo",
            "Alkuperäinen_talousarvio"
        ]
        
        for col in finnish_columns:
            if col in sql and f'`{col}`' not in sql:
                result["warnings"].append(
                    f"Column '{col}' should be backticked for proper handling of Finnish characters"
                )
        
        # Check for time constraints
        if "Vuosi" not in sql:
            result["warnings"].append(
                "No year constraint found - query may return excessive data"
            )
        
        # Check for administrative branch
        if "Ha_Tunnus" in sql:
            # Validate branch codes
            branch_codes = re.findall(r'Ha_Tunnus\s*=\s*(\d+)', sql)
            for code in branch_codes:
                if int(code) not in [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]:
                    result["warnings"].append(
                        f"Unusual administrative branch code: {code}"
                    )
        
        # Check for proper aggregations
        if "GROUP BY" in sql and not any(agg in sql for agg in ["SUM", "AVG", "COUNT", "MAX", "MIN"]):
            result["suggestions"].append(
                "Query has GROUP BY but no aggregation functions - consider using SUM, AVG, etc."
            )
        
        return result

    def _merge_validation_results(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two validation results."""
        merged = {
            "is_valid": result1["is_valid"] and result2["is_valid"],
            "syntax_errors": result1["syntax_errors"] + result2["syntax_errors"],
            "field_errors": result1["field_errors"] + result2["field_errors"],
            "warnings": result1["warnings"] + result2["warnings"],
            "suggestions": result1["suggestions"] + result2["suggestions"]
        }
        
        # Remove duplicates
        for key in ["syntax_errors", "field_errors", "warnings", "suggestions"]:
            merged[key] = list(set(merged[key]))
        
        return merged