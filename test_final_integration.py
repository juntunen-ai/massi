"""
Final integration test for the application.
Tests the real data provider, visualization, and basic app functionality.
"""

import logging
import sys
import pandas as pd
from utils.real_data_provider import RealDataProvider
from utils.visualization import FinancialDataVisualizer
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_integration():
    """Test the integration of data provider and visualization."""
    logger.info("Testing integration of data provider and visualization...")
    
    try:
        # Create data provider
        data_provider = RealDataProvider()
        logger.info("✅ Created data provider")
        
        # Get available years
        years = data_provider.get_available_years()
        if not years:
            logger.error("❌ No years available in BigQuery")
            return False
            
        logger.info(f"✅ Available years: {years}")
        
        # Run a simple query
        query = f"""
        SELECT 
          Vuosi as year,
          SUM(Nettokertymä) as spending
        FROM 
          `{data_provider.table_ref}`
        WHERE 
          Vuosi BETWEEN {min(years)} AND {max(years)}
        GROUP BY 
          year
        ORDER BY 
          year
        """
        
        results = data_provider.execute_query(query)
        
        if results is None or results.empty:
            logger.error("❌ Query returned no results")
            return False
            
        logger.info(f"✅ Query returned {len(results)} rows")
        logger.info(f"Sample data: {results.head().to_dict()}")
        
        # Create visualization
        visualizer = FinancialDataVisualizer()
        viz_type = visualizer.detect_visualization_type(results)
        
        logger.info(f"✅ Detected visualization type: {viz_type}")
        
        fig = visualizer.create_visualization(results, "Spending by Year")
        logger.info("✅ Created visualization")
        
        # Save the figure to a file for inspection
        fig.write_html("test_visualization.html")
        logger.info("✅ Saved visualization to test_visualization.html")
        
        return True
    except Exception as e:
        logger.error(f"❌ Integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)