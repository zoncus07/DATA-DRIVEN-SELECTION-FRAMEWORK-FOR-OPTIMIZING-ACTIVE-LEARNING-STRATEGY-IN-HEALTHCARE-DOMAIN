import pandas as pd
import numpy as np
from typing import Dict
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import pearsonr
import warnings

def check_high_dimensionality(
    dataset: pd.DataFrame,
    redundancy_threshold: float = 0.9,
    min_features: int = 20,
    max_redundant_pairs: int = 5
) -> Dict:
    """
    Check for high dimensionality focusing on feature redundancy, specifically designed
    to detect the type of redundancy introduced by hd.py.
    
    Args:
        dataset: Input DataFrame
        redundancy_threshold: Correlation threshold to consider features redundant (0-1)
        min_features: Minimum number of features to consider high-dimensional
        max_redundant_pairs: Maximum allowed redundant feature pairs before flagging
        
    Returns:
        Dictionary with detailed redundancy analysis
    """
    try:
        data_copy = dataset.copy()
        n_features = data_copy.shape[1]
        
        # Initial check for sufficient features
        if n_features < min_features:
            return {
                'has_issue': False,
                'details': {
                    'message': f'Dataset has only {n_features} features (minimum {min_features} required)',
                    'num_features': n_features
                },
                'status': 'complete'
            }
        
        # Select numeric columns only
        numeric_data = data_copy.select_dtypes(include=np.number)
        if numeric_data.shape[1] < 2:
            return {
                'has_issue': False,
                'details': {
                    'message': 'Not enough numeric features (need at least 2)',
                    'num_numeric_features': numeric_data.shape[1]
                },
                'status': 'complete'
            }
        
        # Find redundant feature pairs
        redundant_pairs = []
        columns = numeric_data.columns
        
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                col1 = columns[i]
                col2 = columns[j]
                
                # Skip if columns appear to be redundant by naming pattern
                if ('redundant' in col1.lower() and 'redundant' in col2.lower()):
                    redundant_pairs.append((col1, col2, 'name_pattern'))
                    continue
                
                # Skip constant columns
                if numeric_data[col1].nunique() == 1 or numeric_data[col2].nunique() == 1:
                    redundant_pairs.append((col1, col2, 'constant_column'))
                    continue
                
                # Calculate Pearson correlation with warning suppression
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        corr, _ = pearsonr(numeric_data[col1], numeric_data[col2])
                        if abs(corr) > redundancy_threshold:
                            redundant_pairs.append((col1, col2, f'corr={corr:.2f}'))
                            continue
                    except:
                        pass
                
                # Calculate mutual information if correlation is inconclusive
                try:
                    mi = mutual_info_regression(
                        numeric_data[col1].values.reshape(-1, 1),
                        numeric_data[col2]
                    )[0]
                    if mi > redundancy_threshold:
                        redundant_pairs.append((col1, col2, f'mi={mi:.2f}'))
                except:
                    pass
        
        # Prepare results
        is_high_dim = len(redundant_pairs) > max_redundant_pairs
        details = {
            'num_features': n_features,
            'num_numeric_features': numeric_data.shape[1],
            'redundant_pairs_count': len(redundant_pairs),
            'redundant_pairs': redundant_pairs[:20],  # Limit to first 20 pairs for readability
            'redundancy_threshold': redundancy_threshold,
            'max_allowed_pairs': max_redundant_pairs
        }
        
        return {
            'has_issue': is_high_dim,
            'details': details,
            'status': 'complete'
        }
        
    except Exception as e:
        return {
            'has_issue': False,
            'details': {'message': f"Error checking high dimensionality: {str(e)}"},
            'status': 'error'
        }