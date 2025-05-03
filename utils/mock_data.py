"""
Mock data provider for testing the Finnish Government Budget Explorer.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import datetime
import random
import re

class MockDataProvider:
    """Provides mock financial data for testing."""
    
    def __init__(self):
        """Initialize the mock data provider."""
        # Define administrative branches
        self.admin_branches = {
            "23": "Ministry of Finance",
            "24": "Ministry of Justice",
            "25": "Ministry of Interior",
            "26": "Ministry of Defense",
            "27": "Ministry of Social Affairs and Health",
            "28": "Ministry of Education",
            "29": "Ministry of Agriculture and Forestry",
            "30": "Ministry of Transport and Communications",
            "31": "Ministry of Economic Affairs and Employment",
            "32": "Ministry of Environment"
        }
        
        # Define years to generate data for
        current_year = 2025  # Fixed to match the current date
        self.years = list(range(current_year - 5, current_year + 1))
        
        # Generate mock data
        self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate mock financial data."""
        # Initialize empty list for data rows
        data = []
        
        # Starting budget amounts for each admin branch
        base_budgets = {
            "23": 15_000_000_000,  # Finance
            "24": 1_000_000_000,   # Justice
            "25": 1_500_000_000,   # Interior
            "26": 5_000_000_000,   # Defense
            "27": 12_000_000_000,  # Social Affairs and Health
            "28": 7_000_000_000,   # Education
            "29": 2_500_000_000,   # Agriculture
            "30": 3_500_000_000,   # Transport
            "31": 2_800_000_000,   # Economic Affairs
            "32": 1_200_000_000    # Environment
        }
        
        # Annual growth rates for each admin branch
        growth_rates = {
            "23": 0.02,  # Finance
            "24": 0.01,  # Justice
            "25": 0.02,  # Interior
            "26": 0.05,  # Defense (higher growth due to geopolitical situation)
            "27": 0.03,  # Social Affairs and Health
            "28": 0.01,  # Education
            "29": 0.01,  # Agriculture
            "30": 0.02,  # Transport
            "31": 0.03,  # Economic Affairs
            "32": 0.04   # Environment (higher growth due to climate initiatives)
        }
        
        # Generate data for each year, month, and admin branch
        for year in self.years:
            for month in range(1, 13):
                for branch_code, branch_name in self.admin_branches.items():
                    # Calculate base budget for this year
                    year_index = self.years.index(year)
                    base_budget = base_budgets[branch_code] * (1 + growth_rates[branch_code]) ** year_index
                    
                    # Add some randomness
                    budget_noise = random.uniform(0.95, 1.05)
                    
                    # Calculate values
                    original_budget = base_budget * budget_noise
                    supplementary_budget = original_budget * random.uniform(0, 0.1)
                    current_budget = original_budget + supplementary_budget
                    
                    # Spending patterns vary by month
                    monthly_factor = 1 + 0.1 * np.sin(month / 12 * 2 * np.pi)
                    
                    # Spending is usually close to budget but with some variance
                    spending_factor = random.uniform(0.85, 1.1) * monthly_factor
                    net_amount = current_budget / 12 * spending_factor
                    
                    # Create data row
                    row = {
                        "Vuosi": year,
                        "Kk": month,
                        "Ha_Tunnus": int(branch_code),
                        "Hallinnonala": branch_name,
                        "PaaluokkaOsasto_TunnusP": branch_code,
                        "PaaluokkaOsasto_sNimi": branch_name,
                        "Alkuperäinen_talousarvio": original_budget,
                        "Lisätalousarvio": supplementary_budget,
                        "Voimassaoleva_talousarvio": current_budget,
                        "Nettokertymä_ko_vuodelta": net_amount,
                        "Nettokertymä": net_amount
                    }
                    
                    data.append(row)
        
        # Convert to DataFrame
        self.data = pd.DataFrame(data)
    
    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Execute a mock query and return results.
        
        Args:
            query (str): SQL query (will be parsed for basic filtering)
            
        Returns:
            Optional[pd.DataFrame]: Results DataFrame or None if query fails
        """
        try:
            # Create a copy of the data to filter
            result = self.data.copy()
            
            # Parse basic WHERE conditions
            year_match = re.search(r'Vuosi\s*=\s*(\d+)', query)
            year_range_match = re.search(r'Vuosi\s+BETWEEN\s+(\d+)\s+AND\s+(\d+)', query)
            branch_match = re.search(r'Ha_Tunnus\s*=\s*(\d+)', query)
            
            # Apply year filter
            if year_match:
                year = int(year_match.group(1))
                result = result[result['Vuosi'] == year]
            elif year_range_match:
                start_year = int(year_range_match.group(1))
                end_year = int(year_range_match.group(2))
                result = result[(result['Vuosi'] >= start_year) & (result['Vuosi'] <= end_year)]
            
            # Apply branch filter
            if branch_match:
                branch_code = int(branch_match.group(1))
                result = result[result['Ha_Tunnus'] == branch_code]
            
            # Parse for GROUP BY
            group_by_match = re.search(r'GROUP\s+BY\s+(.*?)(?:ORDER|LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
            
            # Apply groupby if needed
            if group_by_match:
                group_by_cols = [col.strip() for col in group_by_match.group(1).split(',')]
                
                # Handle aliased column names (e.g., "Vuosi as year")
                clean_group_by_cols = []
                for col in group_by_cols:
                    if ' as ' in col.lower():
                        clean_group_by_cols.append(col.split(' as ')[0].strip())
                    else:
                        clean_group_by_cols.append(col)
                
                # Convert "year" to "Vuosi", etc.
                for i, col in enumerate(clean_group_by_cols):
                    if col.lower() == 'year':
                        clean_group_by_cols[i] = 'Vuosi'
                    elif col.lower() == 'month':
                        clean_group_by_cols[i] = 'Kk'
                
                # Determine aggregations
                if 'SUM' in query:
                    # Find all SUM(...) expressions
                    sum_matches = re.finditer(r'SUM\s*\(\s*([^)]+)\s*\)\s*(?:as\s+([^,\s]+))?', query, re.IGNORECASE)
                    
                    agg_dict = {}
                    for match in sum_matches:
                        col = match.group(1).strip()
                        alias = match.group(2).strip() if match.group(2) else col
                        agg_dict[col] = 'sum'
                    
                    # Group by and aggregate
                    result = result.groupby(clean_group_by_cols).agg(agg_dict).reset_index()
                    
                    # Rename columns if aliases were used
                    for match in sum_matches:
                        col = match.group(1).strip()
                        alias = match.group(2).strip() if match.group(2) else col
                        if alias != col:
                            result.rename(columns={f'sum_{col}': alias}, inplace=True)
                
            # Simulate SELECT-specific columns
            select_cols_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
            if select_cols_match and '*' not in select_cols_match.group(1):
                select_cols = [col.strip() for col in select_cols_match.group(1).split(',')]
                
                # Handle expressions like "SUM(...) as alias"
                output_cols = []
                for col in select_cols:
                    if ' as ' in col.lower():
                        parts = col.lower().split(' as ')
                        alias = parts[1].strip()
                        output_cols.append(alias)
                    else:
                        # For simple column names
                        col = col.strip()
                        if col in result.columns:
                            output_cols.append(col)
                
                # Filter columns if we found any valid ones
                if output_cols:
                    result = result[output_cols]
            
            # Parse for ORDER BY
            order_by_match = re.search(r'ORDER\s+BY\s+(.*?)(?:LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
            if order_by_match:
                order_cols = [col.strip() for col in order_by_match.group(1).split(',')]
                
                ascending = [True] * len(order_cols)
                for i, col in enumerate(order_cols):
                    if ' desc' in col.lower():
                        order_cols[i] = col.lower().replace(' desc', '').strip()
                        ascending[i] = False
                    elif ' asc' in col.lower():
                        order_cols[i] = col.lower().replace(' asc', '').strip()
                
                # Sort the DataFrame
                result = result.sort_values(by=order_cols, ascending=ascending)
            
            # Parse for LIMIT
            limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
            if limit_match:
                limit = int(limit_match.group(1))
                result = result.head(limit)
            
            return result
            
        except Exception as e:
            print(f"Error executing mock query: {str(e)}")
            return None

    def get_available_years(self) -> List[int]:
        """
        Get list of available years in the data.
        
        Returns:
            List[int]: List of available years
        """
        return sorted(self.years)

    def generate_example_data(self, query_type: str) -> pd.DataFrame:
        """
        Generate example data for specific query types.
        
        Args:
            query_type (str): Type of query ('yearly_budget', 'comparison', etc.)
            
        Returns:
            pd.DataFrame: Example data
        """
        # Handle specific example queries
        if query_type == 'military_budget_2022':
            # Get defense ministry data for 2022
            result = self.data[(self.data['Vuosi'] == 2022) & (self.data['Ha_Tunnus'] == 26)]
            
            # Group by year
            result = result.groupby('Vuosi').agg({
                'Alkuperäinen_talousarvio': 'sum',
                'Voimassaoleva_talousarvio': 'sum'
            }).reset_index()
            
            # Rename columns
            result.rename(columns={
                'Alkuperäinen_talousarvio': 'original_budget',
                'Voimassaoleva_talousarvio': 'current_budget'
            }, inplace=True)
            
            return result
            
        elif query_type == 'defense_quarterly_2022_2023':
            # Filter data
            result = self.data[
                (self.data['Vuosi'].isin([2022, 2023])) &
                (self.data['Ha_Tunnus'] == 26)
            ].copy()
            
            # Add quarter column
            result['quarter'] = ((result['Kk'] - 1) // 3) + 1
            
            # Group by year and quarter
            result = result.groupby(['Vuosi', 'quarter']).agg({
                'Voimassaoleva_talousarvio': 'sum',
                'Nettokertymä': 'sum'
            }).reset_index()
            
            # Rename columns
            result.rename(columns={
                'Vuosi': 'year',
                'Voimassaoleva_talousarvio': 'budget',
                'Nettokertymä': 'spending'
            }, inplace=True)
            
            return result
            
        elif query_type == 'education_budget_trend':
            # Filter data
            result = self.data[
                (self.data['Vuosi'].between(2020, 2023)) &
                (self.data['Ha_Tunnus'] == 28)
            ]
            
            # Group by year
            result = result.groupby('Vuosi').agg({
                'Alkuperäinen_talousarvio': 'sum',
                'Voimassaoleva_talousarvio': 'sum',
                'Nettokertymä': 'sum'
            }).reset_index()
            
            # Rename columns
            result.rename(columns={
                'Vuosi': 'year',
                'Alkuperäinen_talousarvio': 'original_budget',
                'Voimassaoleva_talousarvio': 'current_budget',
                'Nettokertymä': 'spending'
            }, inplace=True)
            
            return result
            
        elif query_type == 'top_ministries_2023':
            # Filter data
            result = self.data[self.data['Vuosi'] == 2023]
            
            # Group by ministry
            result = result.groupby('Hallinnonala').agg({
                'Nettokertymä': 'sum'
            }).reset_index()
            
            # Sort and limit
            result = result.sort_values(by='Nettokertymä', ascending=False).head(5)
            
            # Rename columns
            result.rename(columns={
                'Hallinnonala': 'ministry',
                'Nettokertymä': 'spending'
            }, inplace=True)
            
            return result
            
        # Default to returning all data
        return self.data