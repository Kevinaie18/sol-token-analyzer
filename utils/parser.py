import pandas as pd
import numpy as np
from typing import Tuple, Optional

def detect_delimiter(file_content: str) -> str:
    """
    Detect delimiter in CSV content.
    Returns ';' or ',' based on which appears more frequently.
    """
    semicolon_count = file_content.count(';')
    comma_count = file_content.count(',')
    
    if semicolon_count > comma_count:
        return ';'
    else:
        return ','

def parse_csv(uploaded_file) -> Tuple[pd.DataFrame, str]:
    """
    Parse uploaded CSV file with automatic delimiter detection.
    Returns DataFrame and delimiter used.
    """
    try:
        # Read the file content to detect delimiter
        content = str(uploaded_file.read(), "utf-8")
        uploaded_file.seek(0)  # Reset file pointer
        
        delimiter = detect_delimiter(content)
        
        # Parse CSV with detected delimiter
        df = pd.read_csv(uploaded_file, delimiter=delimiter)
        
        return df, delimiter
    
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize the DataFrame.
    """
    # Make a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Remove completely empty rows
    cleaned_df = cleaned_df.dropna(how='all')
    
    # Convert numeric columns with case-insensitive matching
    numeric_columns = ['value', 'amount']
    for col_name in numeric_columns:
        # Find the actual column name regardless of case
        actual_col = next((col for col in cleaned_df.columns if col.lower() == col_name), None)
        if actual_col:
            # Remove any non-numeric characters and convert to float
            cleaned_df[actual_col] = pd.to_numeric(
                cleaned_df[actual_col].astype(str).str.replace(',', '').str.replace('$', ''), 
                errors='coerce'
            )
    
    # Standardize timestamp if it exists
    timestamp_col = next((col for col in cleaned_df.columns if col.lower() in ['timestamp', 'block time', 'human time']), None)
    if timestamp_col:
        cleaned_df[timestamp_col] = pd.to_datetime(cleaned_df[timestamp_col], errors='coerce')
    
    # Remove rows with critical missing data using case-insensitive column names
    token2_col = next((col for col in cleaned_df.columns if col.lower() == 'token2'), None)
    value_col = next((col for col in cleaned_df.columns if col.lower() == 'value'), None)
    amount_col = next((col for col in cleaned_df.columns if col.lower() == 'amount'), None)
    
    if all([token2_col, value_col, amount_col]):
        cleaned_df = cleaned_df.dropna(subset=[token2_col, value_col, amount_col])
    
    return cleaned_df 