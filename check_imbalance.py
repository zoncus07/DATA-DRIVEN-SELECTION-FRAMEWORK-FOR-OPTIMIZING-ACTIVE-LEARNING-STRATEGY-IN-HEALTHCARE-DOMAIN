import pandas as pd
import numpy as np
from typing import Dict

def check_imbalance(
    dataset: pd.DataFrame,
    target_column: str,
    imbalance_threshold: float = 0.5,
    severe_imbalance_threshold: float = 0.1
) -> Dict:
    """
    Check for severe class imbalance in the target variable, only flagging cases
    that exceed the severe imbalance threshold.
    
    Args:
        dataset: Input DataFrame
        target_column: Name of the target column
        imbalance_threshold: Ratio threshold for regular imbalance (default 0.5)
        severe_imbalance_threshold: Ratio threshold for severe imbalance (default 0.1)
        
    Returns:
        Dictionary with imbalance analysis, only flagging severe imbalance as an issue
    """
    try:
        data_copy = dataset.copy()

        # Validation checks
        if not isinstance(data_copy, pd.DataFrame) or data_copy.empty:
            return {
                "has_issue": True,
                "details": {"message": "Invalid dataset: Empty or not a DataFrame"},
                "status": "error",
            }

        if target_column not in data_copy.columns:
            return {
                "has_issue": True,
                "details": {"message": f'Target column "{target_column}" not found'},
                "status": "error",
            }

        # Get class distribution
        class_counts = data_copy[target_column].value_counts()
        n_classes = len(class_counts)
        
        if n_classes < 2:
            return {
                "has_issue": True,
                "details": {
                    "message": "Only one class present",
                    "class_counts": class_counts.to_dict()
                },
                "status": "complete",
            }

        # Calculate imbalance ratios
        majority_count = class_counts.max()
        minority_count = class_counts.min()
        actual_ratio = minority_count / majority_count
        
        # Determine imbalance level
        if actual_ratio < severe_imbalance_threshold:
            imbalance_level = "severe"
            has_issue = True
        elif actual_ratio < imbalance_threshold:
            imbalance_level = "moderate"
            has_issue = False  # Only severe imbalance is considered an issue
        else:
            imbalance_level = "balanced"
            has_issue = False

        # Prepare detailed results
        details = {
            "class_counts": class_counts.to_dict(),
            "majority_class": class_counts.idxmax(),
            "minority_class": class_counts.idxmin(),
            "imbalance_ratio": actual_ratio,
            "imbalance_level": imbalance_level,
            "imbalance_threshold": imbalance_threshold,
            "severe_threshold": severe_imbalance_threshold
        }

        return {
            "has_issue": has_issue,
            "details": details,
            "status": "complete",
        }

    except Exception as e:
        return {
            "has_issue": True,
            "details": {"message": f"Error checking imbalance: {str(e)}"},
            "status": "error"
        }