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
    
    # Find value and amount columns regardless of case
    value_col = next((col for col in df.columns if col.lower() == 'value'), None)
    # For token2 transactions, we need amount2
    amount_col = next((col for col in df.columns if col.lower() in ['amount2', 'amount']), None)
    
    if not value_col:
        raise ValueError("value column not found in DataFrame")
    if not amount_col:
        raise ValueError("amount2 or amount column not found in DataFrame")
    
    # Calculate price = value / amount (considering decimals)
    # First, we need to check if there's a decimal column for proper calculation
    decimal_col = next((col for col in df.columns if col.lower() in ['tokendecimals2', 'decimals2', 'decimals']), None)
    
    if decimal_col:
        # Adjust amount for decimals
        adjusted_amount = result_df[amount_col] / (10 ** result_df[decimal_col])
        result_df['price'] = result_df[value_col] / adjusted_amount
    else:
        # Assume the amount is already in the correct decimal format
        result_df['price'] = result_df[value_col] / result_df[amount_col]
    
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
    # Find wallet column regardless of case
    wallet_col = next((col for col in df.columns if col.lower() in ['wallet', 'address', 'from']), None)
    if not wallet_col:
        raise ValueError("No wallet/address column found in DataFrame")
    
    # Find other required columns regardless of case
    value_col = next((col for col in df.columns if col.lower() == 'value'), None)
    timestamp_col = next((col for col in df.columns if col.lower() in ['timestamp', 'block time', 'human time']), None)
    tx_hash_col = next((col for col in df.columns if col.lower() in ['tx_hash', 'signature']), None)
    
    # Find SOL-related columns for SOL value calculation
    token1_col = next((col for col in df.columns if col.lower() == 'token1'), None)
    amount1_col = next((col for col in df.columns if col.lower() == 'amount1'), None)
    decimals1_col = next((col for col in df.columns if col.lower() == 'tokendecimals1'), None)
    
    if not all([value_col, timestamp_col, tx_hash_col]):
        raise ValueError("Required columns (value, timestamp, tx_hash) not found in DataFrame")
    
    # Create a copy to avoid modifying original
    analysis_df = df.copy()
    
    # Calculate SOL values if SOL columns are available
    sol_address = "So11111111111111111111111111111111111111112"  # Standard SOL token address
    if all([token1_col, amount1_col, decimals1_col]):
        # Check if Token1 contains SOL transactions
        sol_mask = analysis_df[token1_col] == sol_address
        analysis_df['sol_amount'] = 0.0
        analysis_df.loc[sol_mask, 'sol_amount'] = (
            analysis_df.loc[sol_mask, amount1_col] / (10 ** analysis_df.loc[sol_mask, decimals1_col])
        )
    else:
        # If no SOL data available, set to 0
        analysis_df['sol_amount'] = 0.0
    
    # Group by wallet for analysis with volume-weighted calculations
    wallet_groups = analysis_df.groupby(wallet_col)
    
    wallet_stats_list = []
    for wallet, group in wallet_groups:
        # Basic aggregations
        total_usd_value = group[value_col].sum()
        total_sol_value = group['sol_amount'].sum()
        first_entry_time = group[timestamp_col].min()
        tx_count = len(group)
        has_early_entry = group['early_flag'].any()
        
        # Volume-weighted average market cap
        if total_usd_value > 0:
            weighted_market_cap = (group['market_cap'] * group[value_col]).sum() / total_usd_value
        else:
            weighted_market_cap = group['market_cap'].mean()
        
        wallet_stats_list.append({
            'wallet': wallet,
            'total_usd_value': round(total_usd_value, 2),
            'total_sol_value': round(total_sol_value, 6),
            'first_entry_time': first_entry_time,
            'avg_market_cap_weighted': round(weighted_market_cap, 2),
            'tx_count': tx_count,
            'early_flag': has_early_entry
        })
    
    wallet_stats = pd.DataFrame(wallet_stats_list)
    
    # Early entries: wallets that made at least one early buy
    early_entries = wallet_stats[wallet_stats['early_flag'] == True].copy()
    early_entries = early_entries.drop('early_flag', axis=1)
    
    # Filter for early entries specifically for more detailed analysis
    early_txs = analysis_df[analysis_df['early_flag'] == True]
    if not early_txs.empty:
        early_groups = early_txs.groupby(wallet_col)
        early_specific_list = []
        
        for wallet, group in early_groups:
            total_usd_early = group[value_col].sum()
            total_sol_early = group['sol_amount'].sum()
            first_tx_time = group[timestamp_col].min()
            tx_count_early = len(group)
            
            # Volume-weighted average entry market cap for early transactions only
            if total_usd_early > 0:
                weighted_entry_cap = (group['market_cap'] * group[value_col]).sum() / total_usd_early
            else:
                weighted_entry_cap = group['market_cap'].mean()
            
            early_specific_list.append({
                'wallet': wallet,
                'total_usd_value': round(total_usd_early, 2),
                'total_sol_value': round(total_sol_early, 6),
                'first_tx_time': first_tx_time,
                'avg_entry_cap_weighted': round(weighted_entry_cap, 2),
                'tx_count': tx_count_early
            })
        
        early_entries = pd.DataFrame(early_specific_list)
    
    # Whale wallets: wallets above threshold
    whale_wallets = wallet_stats[wallet_stats['total_usd_value'] > whale_threshold].copy()
    whale_wallets = whale_wallets.drop('early_flag', axis=1)
    
    return early_entries, whale_wallets

def create_parsed_transactions_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the parsed transactions report.
    """
    result_df = df.copy()
    
    # Add adjusted token amount column (accounting for decimals)
    amount_col = next((col for col in df.columns if col.lower() in ['amount2', 'amount']), None)
    decimal_col = next((col for col in df.columns if col.lower() in ['tokendecimals2', 'decimals2', 'decimals']), None)
    
    if amount_col and decimal_col:
        result_df['adjusted_token_amount'] = result_df[amount_col] / (10 ** result_df[decimal_col])
    
    # Define column mappings (case-insensitive)
    column_mappings = {
        'tx_hash': ['tx_hash', 'signature'],
        'timestamp': ['timestamp', 'block time', 'human time'],
        'wallet': ['wallet', 'address', 'from'],
        'action': ['action'],
        'value': ['value'],
        'amount_raw': ['amount2', 'amount'],
        'decimals': ['tokendecimals2', 'decimals2', 'decimals'],
        'token1': ['token1'],
        'token2': ['token2']
    }
    
    # Find actual column names in DataFrame
    available_columns = []
    for target_col, possible_names in column_mappings.items():
        found_col = next((col for col in df.columns if col.lower() in [name.lower() for name in possible_names]), None)
        if found_col:
            available_columns.append(found_col)
    
    # Add calculated columns in preferred order
    calculated_columns = ['adjusted_token_amount', 'price', 'market_cap', 'early_flag']
    available_columns.extend([col for col in calculated_columns if col in result_df.columns])
    
    return result_df[available_columns].round(6) 