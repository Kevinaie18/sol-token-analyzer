import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

# Import our custom modules
from utils.parser import parse_csv, clean_dataframe
from report_builder import (
    filter_buy_transactions, 
    calculate_price_and_market_cap, 
    classify_early_entries,
    analyze_wallets,
    create_parsed_transactions_report
)

def main():
    st.set_page_config(
        page_title="Token Momentum Analyzer",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🚀 Token Momentum Analyzer")
    st.markdown("**Analyze Solana token transaction data to identify early entries and whale wallets**")
    
    # Sidebar configuration
    st.sidebar.header("📊 Configuration")
    
    # Token configuration inputs
    token_address = st.sidebar.text_input(
        "Token Address *", 
        placeholder="Enter Solana token address",
        help="The token address to analyze for buy-side transactions"
    )
    
    total_supply = st.sidebar.number_input(
        "Total Supply *", 
        value=1000000.0,
        min_value=1.0,
        format="%.0f",
        help="Total token supply for market cap calculation"
    )
    
    # Market cap thresholds
    st.sidebar.subheader("🎯 Thresholds")
    early_threshold = st.sidebar.number_input(
        "Early Entry Market Cap ($)", 
        value=100000.0,
        min_value=1.0,
        format="%.0f",
        help="Market cap below this value flags as early entry"
    )
    
    whale_threshold = st.sidebar.number_input(
        "Whale Wallet Threshold ($)", 
        value=10000.0,
        min_value=1.0,
        format="%.0f",
        help="Total USD spent above this value flags as whale"
    )
    
    # Optional SOL/USD price
    sol_usd_price = st.sidebar.number_input(
        "SOL/USD Price (optional)", 
        value=100.0,
        min_value=0.01,
        format="%.2f",
        help="Fallback price if USD values are missing"
    )
    
    # File upload
    st.header("📁 Upload Transaction Data")
    uploaded_file = st.file_uploader(
        "Choose a CSV file (Solscan export)",
        type=['csv'],
        help="Upload your Solscan CSV export file"
    )
    
    if uploaded_file is not None and token_address:
        try:
            # Parse CSV
            with st.spinner("Parsing CSV file..."):
                raw_df, delimiter = parse_csv(uploaded_file)
                cleaned_df = clean_dataframe(raw_df)
            
            st.success(f"✅ Parsed {len(cleaned_df)} transactions (delimiter: '{delimiter}')")
            
            # Show original data preview
            with st.expander("📋 Raw Data Preview", expanded=False):
                st.dataframe(raw_df.head(10), use_container_width=True)
                st.info(f"Original columns: {list(raw_df.columns)}")
            
            # Process data
            with st.spinner("Analyzing transactions..."):
                # Filter buy transactions
                buy_df = filter_buy_transactions(cleaned_df, token_address)
                
                if len(buy_df) == 0:
                    st.warning(f"⚠️ No buy transactions found for token address: {token_address}")
                    st.info("Make sure the token address is correct and exists in the 'token2' column")
                    return
                
                # Calculate price and market cap
                analyzed_df = calculate_price_and_market_cap(buy_df, total_supply)
                
                # Classify early entries
                analyzed_df = classify_early_entries(analyzed_df, early_threshold)
                
                # Analyze wallets
                early_entries, whale_wallets = analyze_wallets(analyzed_df, whale_threshold)
                
                # Create final reports
                parsed_transactions = create_parsed_transactions_report(analyzed_df)
            
            # Display results
            st.header("📊 Analysis Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Buy Transactions", f"{len(analyzed_df):,}")
            
            with col2:
                early_count = len(early_entries)
                st.metric("Early Entry Wallets", f"{early_count:,}")
            
            with col3:
                whale_count = len(whale_wallets)
                st.metric("Whale Wallets", f"{whale_count:,}")
            
            with col4:
                # Calculate volume-weighted average market cap for overall summary
                total_volume = analyzed_df['value'].sum()
                if total_volume > 0:
                    weighted_avg_cap = (analyzed_df['market_cap'] * analyzed_df['value']).sum() / total_volume
                else:
                    weighted_avg_cap = analyzed_df['market_cap'].mean()
                st.metric("Avg Market Cap (Weighted)", f"${weighted_avg_cap:,.0f}")
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📈 Parsed Transactions", "🎯 Early Entries", "🐋 Whale Wallets"])
            
            with tab1:
                st.subheader("All Buy Transactions")
                st.info("💡 **Token amounts are automatically adjusted for decimals** - Raw amounts from the CSV are converted using the TokenDecimals column for accurate calculations.")
                
                # Format parsed transactions for better display
                display_parsed = parsed_transactions.copy()
                
                # Format numeric columns
                if 'value' in display_parsed.columns:
                    display_parsed['USD Value'] = display_parsed['value'].apply(lambda x: f"${x:,.2f}")
                    display_parsed = display_parsed.drop('value', axis=1)
                
                if 'adjusted_token_amount' in display_parsed.columns:
                    display_parsed['Token Amount'] = display_parsed['adjusted_token_amount'].apply(lambda x: f"{x:,.6f}")
                    display_parsed = display_parsed.drop('adjusted_token_amount', axis=1)
                
                if 'price' in display_parsed.columns:
                    display_parsed['Price per Token'] = display_parsed['price'].apply(lambda x: f"${x:.8f}")
                    display_parsed = display_parsed.drop('price', axis=1)
                
                if 'market_cap' in display_parsed.columns:
                    display_parsed['Market Cap'] = display_parsed['market_cap'].apply(lambda x: f"${x:,.0f}")
                    display_parsed = display_parsed.drop('market_cap', axis=1)
                
                # Rename columns for better readability
                column_renames = {
                    'tx_hash': 'Transaction Hash',
                    'signature': 'Transaction Hash', 
                    'timestamp': 'Timestamp',
                    'block time': 'Timestamp',
                    'human time': 'Timestamp',
                    'wallet': 'Wallet Address',
                    'address': 'Wallet Address',
                    'from': 'Wallet Address',
                    'action': 'Action',
                    'amount_raw': 'Raw Amount',
                    'decimals': 'Decimals',
                    'token1': 'Token 1',
                    'token2': 'Token 2',
                    'early_flag': 'Early Entry'
                }
                
                for old_name, new_name in column_renames.items():
                    if old_name in display_parsed.columns:
                        display_parsed = display_parsed.rename(columns={old_name: new_name})
                
                st.dataframe(display_parsed, use_container_width=True)
                
                # Download button for parsed transactions
                csv_buffer = io.StringIO()
                parsed_transactions.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download Parsed Transactions CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"parsed_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with tab2:
                st.subheader("Early Entry Analysis")
                st.info("💡 **Volume-weighted market cap** - Average market cap weighted by transaction size (larger transactions have more influence on the average)")
                if len(early_entries) > 0:
                    # Format the dataframe for better display
                    display_early = early_entries.copy()
                    
                    # Rename columns for better readability
                    column_renames_early = {
                        'wallet': 'Wallet Address',
                        'total_usd_value': 'Total USD Spent',
                        'total_sol_value': 'Total SOL Spent',
                        'first_tx_time': 'First Entry Time',
                        'avg_entry_cap_weighted': 'Avg Entry Market Cap (Weighted)',
                        'tx_count': 'Transaction Count'
                    }
                    
                    for old_name, new_name in column_renames_early.items():
                        if old_name in display_early.columns:
                            display_early = display_early.rename(columns={old_name: new_name})
                    
                    # Format numerical values
                    if 'Total USD Spent' in display_early.columns:
                        display_early['Total USD Spent'] = display_early['Total USD Spent'].apply(lambda x: f"${x:,.2f}")
                    if 'Total SOL Spent' in display_early.columns and display_early['Total SOL Spent'].sum() > 0:
                        display_early['Total SOL Spent'] = display_early['Total SOL Spent'].apply(lambda x: f"{x:,.6f} SOL" if x > 0 else "0 SOL")
                    if 'Avg Entry Market Cap (Weighted)' in display_early.columns:
                        display_early['Avg Entry Market Cap (Weighted)'] = display_early['Avg Entry Market Cap (Weighted)'].apply(lambda x: f"${x:,.0f}")
                    if 'Transaction Count' in display_early.columns:
                        display_early['Transaction Count'] = display_early['Transaction Count'].apply(lambda x: f"{x:,}")
                    
                    st.dataframe(display_early, use_container_width=True)
                    
                    # Download button for early entries
                    csv_buffer = io.StringIO()
                    early_entries.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="📥 Download Early Entries CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"early_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No early entry wallets found with current threshold.")
            
            with tab3:
                st.subheader("Whale Wallet Analysis")
                st.info("💡 **Volume-weighted market cap** - Average market cap weighted by transaction size (larger transactions have more influence on the average)")
                if len(whale_wallets) > 0:
                    # Format the dataframe for better display
                    display_whales = whale_wallets.copy()
                    
                    # Rename columns for better readability
                    column_renames_whales = {
                        'wallet': 'Wallet Address',
                        'total_usd_value': 'Total USD Spent',
                        'total_sol_value': 'Total SOL Spent',
                        'first_entry_time': 'First Entry Time',
                        'avg_market_cap_weighted': 'Avg Market Cap (Weighted)',
                        'tx_count': 'Transaction Count'
                    }
                    
                    for old_name, new_name in column_renames_whales.items():
                        if old_name in display_whales.columns:
                            display_whales = display_whales.rename(columns={old_name: new_name})
                    
                    # Format numerical values
                    if 'Total USD Spent' in display_whales.columns:
                        display_whales['Total USD Spent'] = display_whales['Total USD Spent'].apply(lambda x: f"${x:,.2f}")
                    if 'Total SOL Spent' in display_whales.columns and display_whales['Total SOL Spent'].sum() > 0:
                        display_whales['Total SOL Spent'] = display_whales['Total SOL Spent'].apply(lambda x: f"{x:,.6f} SOL" if x > 0 else "0 SOL")
                    if 'Avg Market Cap (Weighted)' in display_whales.columns:
                        display_whales['Avg Market Cap (Weighted)'] = display_whales['Avg Market Cap (Weighted)'].apply(lambda x: f"${x:,.0f}")
                    if 'Transaction Count' in display_whales.columns:
                        display_whales['Transaction Count'] = display_whales['Transaction Count'].apply(lambda x: f"{x:,}")
                    
                    st.dataframe(display_whales, use_container_width=True)
                    
                    # Download button for whale wallets
                    csv_buffer = io.StringIO()
                    whale_wallets.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="📥 Download Whale Wallets CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"whale_wallets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No whale wallets found with current threshold.")
            
            # Analysis insights
            st.header("💡 Key Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Market Cap Distribution")
                if len(analyzed_df) > 0:
                    min_cap = analyzed_df['market_cap'].min()
                    max_cap = analyzed_df['market_cap'].max()
                    median_cap = analyzed_df['market_cap'].median()
                    
                    st.write(f"**Min Market Cap:** ${min_cap:,.0f}")
                    st.write(f"**Max Market Cap:** ${max_cap:,.0f}")
                    st.write(f"**Median Market Cap:** ${median_cap:,.0f}")
                    
                    # Add percentiles for better insight
                    p25 = analyzed_df['market_cap'].quantile(0.25)
                    p75 = analyzed_df['market_cap'].quantile(0.75)
                    st.write(f"**25th Percentile:** ${p25:,.0f}")
                    st.write(f"**75th Percentile:** ${p75:,.0f}")
            
            with col2:
                st.subheader("Transaction Volume")
                if len(analyzed_df) > 0:
                    total_usd_volume = analyzed_df['value'].sum()
                    avg_tx_size = analyzed_df['value'].mean()
                    
                    # Find wallet column properly
                    wallet_col = next((col for col in analyzed_df.columns if col.lower() in ['wallet', 'address', 'from']), None)
                    if wallet_col:
                        unique_wallets = analyzed_df[wallet_col].nunique()
                    else:
                        unique_wallets = "Unknown"
                    
                    st.write(f"**Total USD Volume:** ${total_usd_volume:,.2f}")
                    st.write(f"**Average Transaction:** ${avg_tx_size:,.2f}")
                    st.write(f"**Unique Wallets:** {unique_wallets:,}" if isinstance(unique_wallets, int) else f"**Unique Wallets:** {unique_wallets}")
                    
                    # Show SOL volume if available
                    if 'sol_amount' in analyzed_df.columns:
                        total_sol_volume = analyzed_df['sol_amount'].sum()
                        if total_sol_volume > 0:
                            avg_sol_tx = analyzed_df['sol_amount'].mean()
                            st.write(f"**Total SOL Volume:** {total_sol_volume:,.6f} SOL")
                            st.write(f"**Average SOL per TX:** {avg_sol_tx:,.6f} SOL")
            
            # Additional metrics in a third column layout
            st.subheader("📈 Additional Metrics")
            col3, col4, col5 = st.columns(3)
            
            with col3:
                if len(early_entries) > 0:
                    st.write("**Early Entry Stats:**")
                    early_total_usd = early_entries['total_usd_value'].sum() if 'total_usd_value' in early_entries.columns else 0
                    early_avg_usd = early_entries['total_usd_value'].mean() if 'total_usd_value' in early_entries.columns else 0
                    st.write(f"• Total Spent: ${early_total_usd:,.2f}")
                    st.write(f"• Avg per Wallet: ${early_avg_usd:,.2f}")
            
            with col4:
                if len(whale_wallets) > 0:
                    st.write("**Whale Wallet Stats:**")
                    whale_total_usd = whale_wallets['total_usd_value'].sum() if 'total_usd_value' in whale_wallets.columns else 0
                    whale_avg_usd = whale_wallets['total_usd_value'].mean() if 'total_usd_value' in whale_wallets.columns else 0
                    st.write(f"• Total Spent: ${whale_total_usd:,.2f}")
                    st.write(f"• Avg per Whale: ${whale_avg_usd:,.2f}")
            
            with col5:
                st.write("**Price Analysis:**")
                min_price = analyzed_df['price'].min()
                max_price = analyzed_df['price'].max()
                avg_price = analyzed_df['price'].mean()
                st.write(f"• Min Price: ${min_price:.8f}")
                st.write(f"• Max Price: ${max_price:.8f}")
                st.write(f"• Avg Price: ${avg_price:.8f}")
            
            # Volume-weighted analysis explanation
            st.subheader("📊 Volume-Weighted Analysis")
            st.markdown("""
            **Volume-Weighted Average Market Cap**: Unlike simple averages, this calculation gives more weight to larger transactions, 
            providing a more accurate representation of the market cap at which most value was traded.
            
            **Formula**: Σ(Market Cap × Transaction Value) / Σ(Transaction Value)
            
            This means larger purchases have more influence on the average, which better reflects actual market behavior.
            """)
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please check your CSV format and token address.")
    
    elif uploaded_file is not None and not token_address:
        st.warning("⚠️ Please enter a token address to proceed with analysis.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Token Momentum Analyzer v1.7** | Built with Streamlit")

if __name__ == "__main__":
    main() 