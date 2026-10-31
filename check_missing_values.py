import pandas as pd
from typing import Dict, List

def check_missing_values(dataset: pd.DataFrame, target_column: str = None) -> Dict:
    """
    Check for missing values in all columns with special attention to the target column.
    
    Args:
        dataset: Input DataFrame.
        target_column: (Optional) Name of the target variable column for special reporting.
        
    Returns:
        Dictionary containing:
        - has_issue: Boolean indicating if missing values were found
        - details: Dictionary with detailed findings
        - status: Execution status
    """
    try:
        data_copy = dataset.copy()
        
        # Check for missing values in all columns
        missing_stats = data_copy.isnull().sum()
        missing_stats = missing_stats[missing_stats > 0]  # Only keep columns with missing values
        
        if not missing_stats.empty:
            results = {
                'has_issue': True,
                'details': {
                    'missing_summary': {
                        'total_rows': len(data_copy),
                        'columns_with_missing': missing_stats.to_dict(),
                        'missing_percentage': (missing_stats / len(data_copy) * 100).to_dict()
                    }
                },
                'status': 'complete'
            }
            
            # Add special reporting for target column if specified
            if target_column:
                if target_column not in data_copy.columns:
                    results['details']['target_column_status'] = f'Error: Column "{target_column}" not found'
                else:
                    target_missing = data_copy[target_column].isnull().sum()
                    results['details']['target_column'] = {
                        'missing_count': target_missing,
                        'missing_percentage': (target_missing / len(data_copy)) * 100,
                        'importance': 'High' if target_missing > 0 else 'None'
                    }
                    
            return results
        else:
            return {
                'has_issue': False,
                'details': {
                    'message': 'No missing values found in any columns',
                    'target_column_status': f'Column "{target_column}" checked' if target_column else 'No target column specified'
                },
                'status': 'complete'
            }
            
    except Exception as e:
        return {
            'has_issue': False,
            'details': {
                'message': f"Error checking missing values: {str(e)}"
            },
            'status': 'error'
        }