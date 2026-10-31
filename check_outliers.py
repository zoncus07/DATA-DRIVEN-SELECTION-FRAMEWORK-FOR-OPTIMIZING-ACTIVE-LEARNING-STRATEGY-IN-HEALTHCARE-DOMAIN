import pandas as pd
import numpy as np
from typing import Dict
from scipy import stats

def check_outliers(
    dataset: pd.DataFrame, 
    target_column: str,
    method: str = 'iqr',  # Changed default to IQR as it's more robust
    threshold: float = 3.0,
    iqr_multiplier: float = 1.5
) -> Dict:
    """
    Robust outlier detection in the target column with proper issue reporting.
    
    Args:
        dataset: Input DataFrame
        target_column: Column to check for outliers
        method: 'zscore', 'iqr', or 'both'
        threshold: Z-score threshold
        iqr_multiplier: IQR multiplier
        
    Returns:
        Dictionary with proper outlier detection results
    """
    try:
        data_copy = dataset.copy()
        
        # Validation checks
        if target_column not in data_copy.columns:
            return {
                'has_issue': True,  # Changed to True since missing column is an issue
                'details': {'message': f'Target column "{target_column}" not found.'},
                'status': 'error',
            }
            
        numeric_data = data_copy[target_column]
        if not pd.api.types.is_numeric_dtype(numeric_data):
            return {
                'has_issue': True,  # Changed to True since non-numeric is an issue
                'details': {
                    'message': f'Target column "{target_column}" must be numeric (found {numeric_data.dtype})'
                },
                'status': 'complete',
            }
            
        # Remove NaN values for analysis
        clean_data = numeric_data.dropna()
        if len(clean_data) == 0:
            return {
                'has_issue': True,  # Changed to True since no data is an issue
                'details': {'message': 'No valid numeric values to analyze'},
                'status': 'complete',
            }
            
        # Initialize results with has_issue=False
        results = {
            'has_issue': False,  # Will be updated if outliers found
            'details': {
                'method': method,
                'column': target_column,
                'total_values': len(clean_data),
                'outliers': {}
            },
            'status': 'complete'
        }
        
        # Z-score method
        if method in ['zscore', 'both']:
            z_scores = np.abs(stats.zscore(clean_data))
            z_outliers = clean_data[z_scores > threshold]
            
            if not z_outliers.empty:
                results['has_issue'] = True
                results['details']['outliers']['zscore'] = {
                    'threshold': threshold,
                    'count': len(z_outliers),
                    'percentage': (len(z_outliers) / len(clean_data)) * 100,
                    'min_outlier': float(z_outliers.min()),
                    'max_outlier': float(z_outliers.max()),
                    'indices': z_outliers.index.tolist()
                }
        
        # IQR method (more robust for most cases)
        if method in ['iqr', 'both']:
            q1 = clean_data.quantile(0.25)
            q3 = clean_data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (iqr_multiplier * iqr)
            upper_bound = q3 + (iqr_multiplier * iqr)
            
            iqr_outliers = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)]
            
            if not iqr_outliers.empty:
                results['has_issue'] = True
                results['details']['outliers']['iqr'] = {
                    'multiplier': iqr_multiplier,
                    'count': len(iqr_outliers),
                    'percentage': (len(iqr_outliers) / len(clean_data)) * 100,
                    'iqr': float(iqr),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'min_outlier': float(iqr_outliers.min()),
                    'max_outlier': float(iqr_outliers.max()),
                    'indices': iqr_outliers.index.tolist()
                }
        
        # Additional check to ensure we never miss obvious outliers
        if method == 'both' and not results['has_issue']:
            # If both methods agree there are no outliers, add verification
            if len(clean_data) > 10:  # Only for reasonable sample sizes
                median = clean_data.median()
                mad = stats.median_abs_deviation(clean_data)
                if mad > 0:  # Avoid division by zero
                    modified_z = 0.6745 * (clean_data - median) / mad
                    mad_outliers = clean_data[np.abs(modified_z) > threshold]
                    if not mad_outliers.empty:
                        results['has_issue'] = True
                        results['details']['outliers']['mad'] = {
                            'count': len(mad_outliers),
                            'indices': mad_outliers.index.tolist()
                        }
        
        return results
        
    except Exception as e:
        return {
            'has_issue': True,  # Changed to True since error is an issue
            'details': {'message': f"Error detecting outliers: {str(e)}"},
            'status': 'error'
        }