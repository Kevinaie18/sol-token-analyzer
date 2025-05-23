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
    
    # Convert numeric columns
    numeric_columns = ['value', 'amount']
    for col in numeric_columns:
        if col in cleaned_df.columns:
            # Remove any non-numeric characters and convert to float
            cleaned_df[col] = pd.to_numeric(
                cleaned_df[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                errors='coerce'
            )
    
    # Standardize timestamp if it exists
    if 'timestamp' in cleaned_df.columns:
        cleaned_df['timestamp'] = pd.to_datetime(cleaned_df['timestamp'], errors='coerce')
    
    # Remove rows with critical missing data
    if 'token2' in cleaned_df.columns and 'value' in cleaned_df.columns and 'amount' in cleaned_df.columns:
        cleaned_df = cleaned_df.dropna(subset=['token2', 'value', 'amount'])
    
    return cleaned_df 