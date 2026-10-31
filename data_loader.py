import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = [".csv", ".parquet", ".xlsx"]


def load_dataset(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load dataset from file with format autodetection.
    """
    if not any(file_path.endswith(ext) for ext in SUPPORTED_FORMATS):
        logger.error(f"Unsupported file format. Supported: {SUPPORTED_FORMATS}")
        return None

    try:
        if file_path.endswith(".csv"):
            dataset = pd.read_csv(file_path)
        elif file_path.endswith(".parquet"):
            dataset = pd.read_parquet(file_path)
        elif file_path.endswith(".xlsx"):
            dataset = pd.read_excel(file_path)

        logger.info(f"Loaded dataset with shape: {dataset.shape}")
        return dataset

    except Exception as e:
        logger.error(f"Failed to load {file_path}: {str(e)}")
        return None
