import pandas as pd
from typing import Dict

def check_redundancy(
    dataset: pd.DataFrame, 
    keep: str = 'first',
    subset: list = None
) -> Dict:
    """
    Check for redundant (duplicate) rows in the dataset.

    Args:
        dataset: Input DataFrame.
        keep: Determines which duplicates to mark ('first', 'last', or False).
        subset: Column labels to consider for identifying duplicates.

    Returns:
        Dictionary with results containing:
        - has_issue: Boolean indicating if duplicates were found
        - details: Information about duplicates
        - status: Execution status
    """
    try:
        data_copy = dataset.copy()
        
        # Find duplicate rows
        duplicates = data_copy[data_copy.duplicated(keep=keep, subset=subset)]
        
        if not duplicates.empty:
            return {
                'has_issue': True,
                'details': {
                    'duplicate_count': len(duplicates),
                    'duplicate_indices': duplicates.index.tolist(),
                    'keep_strategy': keep,
                    'columns_considered': subset if subset else 'all columns'
                },
                'status': 'complete'
            }
        else:
            return {
                'has_issue': False,
                'details': {
                    'message': 'No duplicate rows found.'
                },
                'status': 'complete'
            }
            
    except Exception as e:
        return {
            'has_issue': False,
            'details': {
                'message': f"Error checking for duplicates: {str(e)}"
            },
            'status': 'error'
        }