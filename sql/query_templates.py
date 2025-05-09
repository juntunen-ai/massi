"""
SQL query templates for common financial data analysis tasks.
These templates can be used by the NL-to-SQL converter to generate more consistent 
and optimized queries for common question patterns.
"""

# Updated SQL templates to use f-string compatible format
TEMPLATES = {
    # Template for aggregating budget values for a specific year and administrative branch
    "yearly_budget": """
        SELECT 
          SUM(Alkuperäinen_talousarvio) as original_budget,
          SUM(Voimassaoleva_talousarvio) as current_budget,
          SUM(Nettokertymä) as net_accumulation
        FROM 
          {table_name}
        WHERE 
          Vuosi = {year} 
          AND Ha_Tunnus = {hallinnonala}
    """,
    
    # Template for comparing values across years
    "yearly_comparison": """
        SELECT 
          Vuosi as year,
          SUM(Alkuperäinen_talousarvio) as original_budget,
          SUM(Voimassaoleva_talousarvio) as current_budget,
          SUM(Nettokertymä) as net_accumulation
        FROM 
          {table_name}
        WHERE 
          Vuosi BETWEEN {start_year} AND {end_year}
          {hallinnonala_filter}
        GROUP BY 
          year
        ORDER BY 
          year
    """,
    
    # Template for quarterly analysis
    "quarterly_analysis": """
        SELECT 
          Vuosi as year,
          CEIL(Kk/3) as quarter,
          SUM(Voimassaoleva_talousarvio) as budget,
          SUM(Nettokertymä) as spending
        FROM 
          {table_name}
        WHERE 
          Vuosi BETWEEN {start_year} AND {end_year}
          {hallinnonala_filter}
        GROUP BY 
          year, quarter
        ORDER BY 
          year, quarter
    """,
    
    # Template for monthly analysis
    "monthly_analysis": """
        SELECT 
          Vuosi as year,
          Kk as month,
          SUM(Voimassaoleva_talousarvio) as budget,
          SUM(Nettokertymä) as spending
        FROM 
          {table_name}
        WHERE 
          Vuosi = {year}
          {hallinnonala_filter}
        GROUP BY 
          year, month
        ORDER BY 
          year, month
    """,
    
    # Template for spending by category (using PaaluokkaOsasto)
    "spending_by_category": """
        SELECT 
          PaaluokkaOsasto_sNimi as category,
          SUM(Nettokertymä) as spending
        FROM 
          {table_name}
        WHERE 
          Vuosi = {year}
          {hallinnonala_filter}
        GROUP BY 
          category
        ORDER BY 
          spending DESC
        LIMIT {limit}
    """,
    
    # Template for spending growth analysis
    "spending_growth": """
        WITH yearly_spending AS (
          SELECT 
            Vuosi as year,
            SUM(Nettokertymä) as spending
          FROM 
            {table_name}
          WHERE 
            Vuosi BETWEEN {start_year} AND {end_year}
            {hallinnonala_filter}
          GROUP BY 
            year
        )
        
        SELECT 
          year,
          spending,
          spending - LAG(spending) OVER(ORDER BY year) as absolute_growth,
          (spending / LAG(spending) OVER(ORDER BY year) - 1) * 100 as percentage_growth
        FROM 
          yearly_spending
        ORDER BY 
          year
    """,
    
    # Template for budget vs actual spending
    "budget_vs_actual": """
        SELECT 
          Vuosi as year,
          SUM(Voimassaoleva_talousarvio) as budget,
          SUM(Nettokertymä) as actual_spending,
          SUM(Nettokertymä) / NULLIF(SUM(Voimassaoleva_talousarvio), 0) * 100 as budget_utilization_percentage
        FROM 
          {table_name}
        WHERE 
          Vuosi BETWEEN {start_year} AND {end_year}
          {hallinnonala_filter}
        GROUP BY 
          year
        ORDER BY 
          year
    """,
    
    # Template for comparing administrative branches
    "compare_branches": """
        SELECT 
          Hallinnonala as administrative_branch,
          SUM(Nettokertymä) as spending
        FROM 
          {table_name}
        WHERE 
          Vuosi = {year}
        GROUP BY 
          administrative_branch
        ORDER BY 
          spending DESC
        LIMIT {limit}
    """
}

def get_template(template_name):
    """
    Get a SQL template by name.
    
    Args:
        template_name (str): Template name
        
    Returns:
        str: Template string or None if not found
    """
    return TEMPLATES.get(template_name)

def format_template(template_name, **kwargs):
    """
    Format a SQL template with the given parameters.
    
    Args:
        template_name (str): Template name
        **kwargs: Parameters to format the template
        
    Returns:
        str: Formatted template or None if template not found
    """
    template = TEMPLATES.get(template_name)
    if not template:
        return None
    
    # Ensure table_name is properly backticked if not already
    if 'table_name' in kwargs and not kwargs['table_name'].startswith('`'):
        kwargs['table_name'] = f"`{kwargs['table_name']}`"
    
    return template.format(**kwargs)