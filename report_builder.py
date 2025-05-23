import pandas as pd
import numpy as np
from typing import Dict, Tuple

def filter_buy_transactions(df: pd.DataFrame, token_address: str) -> pd.DataFrame:
    """
    Filter buy-side transactions where token2 == token_address.
    """
    # Find the token2 column regardless of case
    token2_col = next((col for col in df.columns if col.lower() == 'token2'), None)
    if not token2_col:
        raise ValueError("token2 column not found in DataFrame")
    
    buy_df = df[df[token2_col] == token_address].copy()
    return buy_df

def calculate_price_and_market_cap(df: pd.DataFrame, total_supply: float) -> pd.DataFrame:
    """
    Calculate price per token and market cap.
    """
    result_df = df.copy()
    
    # Calculate price = value / amount
    result_df['price'] = result_df['value'] / result_df['amount']
    
    # Calculate market cap = price * total_supply
    result_df['market_cap'] = result_df['price'] * total_supply
    
    return result_df

def classify_early_entries(df: pd.DataFrame, early_threshold: float) -> pd.DataFrame:
    """
    Add early_flag column based on market cap threshold.
    """
    result_df = df.copy()
    result_df['early_flag'] = result_df['market_cap'] < early_threshold
    return result_df

def analyze_wallets(df: pd.DataFrame, whale_threshold: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze wallets to identify early entries and whales.
    Returns (early_entries_df, whale_wallets_df).
    """
    if 'wallet' not in df.columns:
        # Try to find wallet column with different names
        wallet_cols = [col for col in df.columns if 'wallet' in col.lower() or 'address' in col.lower()]
        if wallet_cols:
            df = df.rename(columns={wallet_cols[0]: 'wallet'})
        else:
            raise ValueError("No wallet/address column found in DataFrame")
    
    # Group by wallet for analysis
    wallet_stats = df.groupby('wallet').agg({
        'value': 'sum',
        'timestamp': 'min',
        'market_cap': 'mean',
        'early_flag': 'any',
        'tx_hash': 'count'
    }).round(2)
    
    wallet_stats = wallet_stats.rename(columns={
        'value': 'total_value',
        'timestamp': 'first_entry_time',
        'market_cap': 'avg_market_cap',
        'tx_hash': 'tx_count'
    })
    
    # Reset index to make wallet a column
    wallet_stats = wallet_stats.reset_index()
    
    # Early entries: wallets that made at least one early buy
    early_entries = wallet_stats[wallet_stats['early_flag'] == True].copy()
    early_entries = early_entries.drop('early_flag', axis=1)
    
    # Filter for early entries specifically
    early_txs = df[df['early_flag'] == True]
    if not early_txs.empty:
        early_specific_stats = early_txs.groupby('wallet').agg({
            'timestamp': 'min',
            'value': 'sum',
            'market_cap': 'mean',
            'tx_hash': 'count'
        }).round(2)
        
        early_specific_stats = early_specific_stats.rename(columns={
            'timestamp': 'first_tx_time',
            'value': 'total_value',
            'market_cap': 'avg_entry_cap',
            'tx_hash': 'tx_count'
        })
        
        early_entries = early_specific_stats.reset_index()
    
    # Whale wallets: wallets above threshold
    whale_wallets = wallet_stats[wallet_stats['total_value'] > whale_threshold].copy()
    
    return early_entries, whale_wallets

def create_parsed_transactions_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the parsed transactions report.
    """
    columns_order = ['tx_hash', 'timestamp', 'value', 'amount', 'price', 'market_cap', 'wallet', 'token1', 'token2']
    
    # Only include columns that exist
    available_columns = [col for col in columns_order if col in df.columns]
    
    return df[available_columns].round(6) 