import logging
from typing import Dict, List, Union
import pandas as pd

# Import individual check functions
from check_high_dimensionality import check_high_dimensionality
from check_imbalance import check_imbalance
from check_missing_values import check_missing_values
from check_outliers import check_outliers
from check_redundancy import check_redundancy

logger = logging.getLogger(__name__)

def analyze_dataset(
    dataset: pd.DataFrame, 
    target_column: str,
    config: Dict = None
) -> Dict[str, Union[List[str], Dict[str, dict]]]:
    """
    Analyze dataset for common ML problems with enhanced error handling and configuration.

    Args:
        dataset: Input DataFrame
        target_column: Name of target variable column
        config: Dictionary containing configuration parameters for analysis

    Returns:
        Dictionary containing:
        - 'problems': List of problem names
        - 'details': Dictionary with detailed findings
        - 'status': Analysis status ('complete', 'error')
        - 'message': Optional status message
    """
    # Initialize default config if none provided
    if config is None:
        config = {
            'high_dimensionality_threshold': 0.7,  # Lower than check's default 0.9
            'imbalance_ratio_threshold': 0.2,     # Higher than current 0.1
            'outlier_threshold': 2.5,             # Lower than current 3.0
            'correlation_threshold': 0.8,
            'mutual_info_threshold': 0.8
        }

    try:
        data_copy = dataset.copy()

        # Input validation
        if not isinstance(data_copy, pd.DataFrame) or data_copy.empty:
            logger.error("Invalid dataset: Empty or not a DataFrame")
            return {
                'problems': [],
                'details': {},
                'status': 'error',
                'message': 'Invalid dataset: Empty or not a DataFrame'
            }

        if target_column not in data_copy.columns:
            logger.error(f"Target column '{target_column}' not found in dataset")
            return {
                'problems': [],
                'details': {},
                'status': 'error',
                'message': f'Target column "{target_column}" not found in dataset'
            }

        problems = []
        details = {}
        status = 'complete'

        # Define checks with their configuration parameters
        checks = [
            ('high_dimensionality', 'High Dimensionality', check_high_dimensionality, 
             {'redundancy_threshold': config['high_dimensionality_threshold']}),
            ('missing_values', 'Missing Values', check_missing_values, 
             {'target_column': target_column}),
            ('imbalance', 'Imbalance', check_imbalance, 
             {'target_column': target_column, 'severe_imbalance_threshold': config['imbalance_ratio_threshold']}),
            ('outliers', 'Outliers', check_outliers, 
             {'target_column': target_column, 'threshold': config['outlier_threshold']}),
            ('redundancy', 'Redundancy', check_redundancy, {}),  # No parameters needed
        ]

        for check_id, name, check_func, kwargs in checks:
            try:
                result = check_func(data_copy, **kwargs)

                if result.get('status') == 'error':
                    status = 'error'
                    problems.append(name)
                    details[check_id] = {
                        'status': 'error',
                        'message': result.get('message', 'An error occurred'),
                    }
                elif result.get('has_issue', False):
                    problems.append(name)
                    details[check_id] = result.get('details', {})
                else:
                    details[check_id] = {'found': False}

            except Exception as e:
                logger.error(f"Check '{name}' failed: {str(e)}", exc_info=True)
                status = 'error'
                problems.append(name)
                details[check_id] = {
                    'status': 'error',
                    'message': str(e),
                }

        return {
            'problems': problems,
            'details': details,
            'status': status,
            'message': 'Analysis completed successfully' if status != 'error' else 'Analysis completed with errors'
        }

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return {
            'problems': [],
            'details': {},
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }

def get_default_config() -> Dict:
    """Return default configuration parameters for analysis"""
    return {
        'high_dimensionality_threshold': 0.8,
        'imbalance_ratio_threshold': 0.1,
        'outlier_threshold': 3.0,
        'correlation_threshold': 0.9,
        'mutual_info_threshold': 0.9
    }