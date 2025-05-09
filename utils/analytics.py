"""
Financial analytics utilities for government budget data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class FinancialAnalytics:
    """Class for performing financial analytics on government budget data."""
    
    def __init__(self):
        """Initialize the analytics module."""
        pass
    
    def analyze_budget_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze budget trends over time.
        
        Args:
            df (pd.DataFrame): Budget data with year and budget columns
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            # Ensure we have required columns
            required_cols = ['year', 'budget']
            if not all(col in df.columns for col in required_cols):
                return {"error": "Missing required columns for trend analysis"}
            
            # Calculate year-over-year changes
            df = df.sort_values('year')
            df['budget_change'] = df['budget'].pct_change()
            df['budget_change_abs'] = df['budget'].diff()
            
            # Calculate compound annual growth rate (CAGR)
            years = df['year'].max() - df['year'].min()
            start_budget = df['budget'].iloc[0]
            end_budget = df['budget'].iloc[-1]
            
            if years > 0 and start_budget > 0:
                cagr = ((end_budget / start_budget) ** (1/years)) - 1
            else:
                cagr = None
            
            # Find significant changes
            significant_changes = df[abs(df['budget_change']) > 0.1].copy()
            
            analysis = {
                "cagr": cagr * 100 if cagr is not None else None,
                "average_annual_growth": df['budget_change'].mean() * 100 if 'budget_change' in df.columns else None,
                "total_change": ((end_budget - start_budget) / start_budget) * 100 if start_budget > 0 else None,
                "significant_changes": significant_changes[['year', 'budget_change']].to_dict('records'),
                "volatility": df['budget_change'].std() * 100 if 'budget_change' in df.columns else None
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            return {"error": str(e)}
    
    def compare_ministries(self, df: pd.DataFrame, year: int = None) -> Dict[str, Any]:
        """
        Compare spending across ministries.
        
        Args:
            df (pd.DataFrame): Data with ministry and spending columns
            year (int): Specific year to analyze (optional)
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        try:
            # Filter for specific year if provided
            if year and 'year' in df.columns:
                df = df[df['year'] == year]
            
            # Group by ministry
            if 'ministry' in df.columns:
                ministry_spending = df.groupby('ministry')['spending'].sum().sort_values(ascending=False)
            elif 'Hallinnonala' in df.columns:
                ministry_spending = df.groupby('Hallinnonala')['Nettokertymä'].sum().sort_values(ascending=False)
            else:
                return {"error": "No ministry column found"}
            
            # Calculate percentages
            total_spending = ministry_spending.sum()
            ministry_percentages = (ministry_spending / total_spending * 100).round(2)
            
            # Find top 5 spenders
            top_5 = ministry_spending.head(5)
            
            analysis = {
                "total_spending": total_spending,
                "ministry_breakdown": ministry_spending.to_dict(),
                "ministry_percentages": ministry_percentages.to_dict(),
                "top_5_spenders": top_5.to_dict(),
                "concentrated_spending": top_5.sum() / total_spending * 100
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in ministry comparison: {str(e)}")
            return {"error": str(e)}
    
    def budget_execution_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze budget execution vs actual spending.
        
        Args:
            df (pd.DataFrame): Data with budget and spending columns
            
        Returns:
            Dict[str, Any]: Execution analysis
        """
        try:
            # Check for required columns
            budget_cols = [col for col in df.columns if 'budget' in col.lower() or 'talousarvio' in col.lower()]
            spending_cols = [col for col in df.columns if 'spending' in col.lower() or 'kertymä' in col.lower()]
            
            if not budget_cols or not spending_cols:
                return {"error": "Missing budget or spending columns"}
            
            budget_col = budget_cols[0]
            spending_col = spending_cols[0]
            
            # Calculate execution rate
            df['execution_rate'] = (df[spending_col] / df[budget_col] * 100)
            
            # Find over and under-execution
            over_execution = df[df['execution_rate'] > 100]
            under_execution = df[df['execution_rate'] < 80]
            
            analysis = {
                "overall_execution_rate": (df[spending_col].sum() / df[budget_col].sum() * 100),
                "average_execution_rate": df['execution_rate'].mean(),
                "over_executing_items": len(over_execution),
                "under_executing_items": len(under_execution),
                "execution_efficiency": 100 - abs(df['execution_rate'] - 100).mean()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in budget execution analysis: {str(e)}")
            return {"error": str(e)}