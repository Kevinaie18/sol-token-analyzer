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
                st.metric("Total Buy Transactions", len(analyzed_df))
            
            with col2:
                early_count = len(early_entries)
                st.metric("Early Entry Wallets", early_count)
            
            with col3:
                whale_count = len(whale_wallets)
                st.metric("Whale Wallets", whale_count)
            
            with col4:
                avg_market_cap = analyzed_df['market_cap'].mean()
                st.metric("Avg Market Cap", f"${avg_market_cap:,.0f}")
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📈 Parsed Transactions", "🎯 Early Entries", "🐋 Whale Wallets"])
            
            with tab1:
                st.subheader("All Buy Transactions")
                st.dataframe(parsed_transactions, use_container_width=True)
                
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
                if len(early_entries) > 0:
                    st.dataframe(early_entries, use_container_width=True)
                    
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
                if len(whale_wallets) > 0:
                    st.dataframe(whale_wallets, use_container_width=True)
                    
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
            
            with col2:
                st.subheader("Transaction Volume")
                if len(analyzed_df) > 0:
                    total_volume = analyzed_df['value'].sum()
                    avg_tx_size = analyzed_df['value'].mean()
                    
                    st.write(f"**Total Volume:** ${total_volume:,.0f}")
                    st.write(f"**Average Transaction:** ${avg_tx_size:,.0f}")
                    st.write(f"**Unique Wallets:** {analyzed_df['wallet'].nunique()}")
            
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