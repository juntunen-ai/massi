#!/usr/bin/env python
"""
Script to execute all cleanup operations for removing mock data
"""
import os
import shutil
import sys

def cleanup_mock_data():
    """Remove all mock data files and references"""
    
    # Files to remove
    files_to_remove = [
        'utils/mock_data.py',
        'app_simple.py',
        'test_imports.py',
        'test_import_fix.py',
        'utils/simple_visualization.py'
    ]
    
    # Remove files
    print("Removing mock data files...")
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed: {file_path}")
        else:
            print(f"File not found: {file_path}")
    
    # Rename real_data_provider.py to data_provider.py
    if os.path.exists('utils/real_data_provider.py'):
        os.rename('utils/real_data_provider.py', 'utils/data_provider.py')
        print("Renamed real_data_provider.py to data_provider.py")
    
    # Update utils/__init__.py
    print("Updating utils/__init__.py...")
    with open('utils/__init__.py', 'w') as f:
        f.write("""from .visualization import FinancialDataVisualizer
from .auth import init_google_auth

__all__ = ['FinancialDataVisualizer', 'init_google_auth']
""")
    print("Updated utils/__init__.py successfully")
    
    # Check for remaining references to mock data
    print("\nChecking for remaining references to mock data...")
    try:
        import re
        
        files_to_check = []
        for root, dirs, files in os.walk('.'):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'env']]
            for file in files:
                if file.endswith('.py'):
                    files_to_check.append(os.path.join(root, file))
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if re.search(r'mock', content, re.IGNORECASE):
                        print(f"Found 'mock' reference in: {file_path}")
            except UnicodeDecodeError:
                continue
                
        print("\nCleanup complete!")
        
    except Exception as e:
        print(f"Error while checking for references: {e}")

if __name__ == "__main__":
    cleanup_mock_data()