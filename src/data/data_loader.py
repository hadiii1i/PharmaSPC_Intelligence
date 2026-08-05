"""
Data loading and validation module for PharmaSPC Intelligence.

Handles reading measurement data from CSV files and validating
the data before passing it to the statistical analysis engine.
"""

import pandas as pd
from typing import Tuple


def load_csv(file_path: str, measurement_column: str) -> Tuple[pd.DataFrame, list]:
    """
    Load measurement data from a CSV file and validate its contents.

    Args:
        file_path: Path to the CSV file.
        measurement_column: Name of the column containing numeric measurements.

    Returns:
        A tuple of:
            - pd.DataFrame: The cleaned dataframe (rows with missing values removed).
            - list: A list of warning messages about data quality issues found.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the measurement column is not found in the file,
                    or if no valid numeric data remains after cleaning.
    """
    warnings = []

    # --- Read file ---
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- Check column exists ---
    if measurement_column not in df.columns:
        raise ValueError(
            f"Column '{measurement_column}' not found in file. "
            f"Available columns: {list(df.columns)}"
        )

    # --- Check for missing values ---
    missing_count = df[measurement_column].isna().sum()
    if missing_count > 0:
        warnings.append(
            f"Found {missing_count} missing value(s) in '{measurement_column}'. "
            f"These rows will be removed."
        )
        df = df.dropna(subset=[measurement_column])

    # --- Check column is numeric ---
    if not pd.api.types.is_numeric_dtype(df[measurement_column]):
        raise ValueError(
            f"Column '{measurement_column}' must contain numeric values."
        )

    # --- Check enough data remains ---
    if len(df) < 2:
        raise ValueError(
            f"Not enough valid data points. "
            f"At least 2 measurements are required for SPC analysis."
        )

    # --- Detect outliers using IQR method ---
    q1 = df[measurement_column].quantile(0.25)
    q3 = df[measurement_column].quantile(0.75)
    iqr = q3 - q1
    lower_fence = q1 - 3.0 * iqr
    upper_fence = q3 + 3.0 * iqr

    outlier_mask = (
        (df[measurement_column] < lower_fence) |
        (df[measurement_column] > upper_fence)
    )
    outlier_count = outlier_mask.sum()

    if outlier_count > 0:
        warnings.append(
            f"Found {outlier_count} potential outlier(s) in '{measurement_column}' "
            f"(outside 3x IQR fence: [{lower_fence:.2f}, {upper_fence:.2f}]). "
            f"Review these values before proceeding."
        )

    df = df.reset_index(drop=True)
    return df, warnings


def extract_measurements(df: pd.DataFrame, measurement_column: str) -> list:
    """
    Extract measurement values from a DataFrame as a plain Python list.

    This converts the pandas Series to a list so it can be passed
    directly to the stats module functions.

    Args:
        df: DataFrame returned by load_csv().
        measurement_column: Name of the column to extract.

    Returns:
        List of float values.
    """
    return df[measurement_column].tolist()