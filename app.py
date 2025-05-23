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
    create_parsed_transactions_report,
    analyze_pnl
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
    st.sidebar.caption(f"📝 {total_supply:,.0f}".replace(',', ' '))
    
    # Market cap thresholds
    st.sidebar.subheader("🎯 Thresholds")
    early_threshold = st.sidebar.number_input(
        "Early Entry Market Cap ($)", 
        value=100000.0,
        min_value=1.0,
        format="%.0f",
        help="Market cap below this value flags as early entry"
    )
    st.sidebar.caption(f"📝 ${early_threshold:,.0f}".replace(',', ' '))
    
    whale_threshold = st.sidebar.number_input(
        "Whale Wallet Threshold ($)", 
        value=10000.0,
        min_value=1.0,
        format="%.0f",
        help="Total USD spent above this value flags as whale"
    )
    st.sidebar.caption(f"📝 ${whale_threshold:,.0f}".replace(',', ' '))
    
    # Optional SOL/USD price
    sol_usd_price = st.sidebar.number_input(
        "SOL/USD Price (optional)", 
        value=100.0,
        min_value=0.01,
        format="%.2f",
        help="Fallback price if USD values are missing"
    )
    st.sidebar.caption(f"📝 {sol_usd_price:,.2f}".replace(',', ' ').replace('.', ','))
    
    # Current token price for P&L analysis
    current_token_price = st.sidebar.number_input(
        "Current Token Price (USD)", 
        value=0.0,
        min_value=0.0,
        format="%.6f",
        help="Current token price for unrealized P&L calculation (optional)"
    )
    st.sidebar.caption(f"📝 ${current_token_price:.6f}".replace('.', ','))
    
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
                # Filter buy transactions for original analysis
                buy_df = filter_buy_transactions(cleaned_df, token_address)
                
                if len(buy_df) == 0:
                    st.warning(f"⚠️ No buy transactions found for token address: {token_address}")
                    st.info("Make sure the token address is correct and exists in the 'token2' column")
                    # Still proceed with P&L analysis as it includes both buys and sells
                
                # P&L Analysis on all transactions (includes both buys and sells)
                pnl_analysis = analyze_pnl(
                    cleaned_df, 
                    token_address, 
                    current_token_price if current_token_price > 0 else None,
                    sol_usd_price
                )
                
                if len(buy_df) > 0:
                    # Calculate price and market cap for buy transactions
                    analyzed_df = calculate_price_and_market_cap(buy_df, total_supply)
                    
                    # Classify early entries
                    analyzed_df = classify_early_entries(analyzed_df, early_threshold)
                    
                    # Analyze wallets
                    early_entries, whale_wallets = analyze_wallets(analyzed_df, whale_threshold)
                    
                    # Create final reports
                    parsed_transactions = create_parsed_transactions_report(analyzed_df)
                else:
                    # Create empty dataframes if no buy transactions
                    analyzed_df = pd.DataFrame()
                    early_entries = pd.DataFrame()
                    whale_wallets = pd.DataFrame()
                    parsed_transactions = pd.DataFrame()
            
            # Display results
            st.header("📊 Analysis Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                buy_count = len(analyzed_df) if not analyzed_df.empty else 0
                st.metric("Total Buy Transactions", f"{buy_count:,}".replace(',', ' '))
            
            with col2:
                pnl_wallets = len(pnl_analysis) if not pnl_analysis.empty else 0
                st.metric("Wallets with Activity", f"{pnl_wallets:,}".replace(',', ' '))
            
            with col3:
                if not pnl_analysis.empty:
                    profitable_wallets = len(pnl_analysis[pnl_analysis['is_profitable'] == True])
                    st.metric("Profitable Wallets", f"{profitable_wallets:,}".replace(',', ' '))
                else:
                    st.metric("Profitable Wallets", "0")
            
            with col4:
                if not analyzed_df.empty:
                    # Calculate volume-weighted average market cap for overall summary
                    value_col = next((col for col in analyzed_df.columns if col.lower() == 'value'), None)
                    if value_col:
                        total_volume = analyzed_df[value_col].sum()
                        if total_volume > 0:
                            weighted_avg_cap = (analyzed_df['market_cap'] * analyzed_df[value_col]).sum() / total_volume
                        else:
                            weighted_avg_cap = analyzed_df['market_cap'].mean()
                        st.metric("Avg Market Cap (Weighted)", f"${weighted_avg_cap:,.0f}".replace(',', ' '))
                    else:
                        st.metric("Avg Market Cap (Weighted)", "N/A")
                else:
                    st.metric("Avg Market Cap (Weighted)", "N/A")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Parsed Transactions", "🎯 Early Entries", "🐋 Whale Wallets", "💰 P&L Analysis"])
            
            with tab1:
                st.subheader("All Buy Transactions")
                st.info("💡 **Token amounts are automatically adjusted for decimals** - Raw amounts from the CSV are converted using the TokenDecimals column for accurate calculations.")
                
                # Format parsed transactions for better display
                display_parsed = parsed_transactions.copy()
                
                # Format numeric columns
                value_col = next((col for col in display_parsed.columns if col.lower() == 'value'), None)
                if value_col:
                    display_parsed['USD Value'] = display_parsed[value_col].apply(lambda x: f"${x:,.2f}".replace(',', ' '))
                    display_parsed = display_parsed.drop(value_col, axis=1)
                
                if 'adjusted_token_amount' in display_parsed.columns:
                    display_parsed['Token Amount'] = display_parsed['adjusted_token_amount'].apply(lambda x: f"{x:,.6f}".replace(',', ' '))
                    display_parsed = display_parsed.drop('adjusted_token_amount', axis=1)
                
                if 'price' in display_parsed.columns:
                    display_parsed['Price per Token'] = display_parsed['price'].apply(lambda x: f"${x:.3f}")
                    display_parsed = display_parsed.drop('price', axis=1)
                
                if 'market_cap' in display_parsed.columns:
                    display_parsed['Market Cap'] = display_parsed['market_cap'].apply(lambda x: f"${x:,.0f}".replace(',', ' '))
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
                        display_early['Total USD Spent'] = display_early['Total USD Spent'].apply(lambda x: f"${x:,.2f}".replace(',', ' '))
                    if 'Total SOL Spent' in display_early.columns and display_early['Total SOL Spent'].sum() > 0:
                        display_early['Total SOL Spent'] = display_early['Total SOL Spent'].apply(lambda x: f"{x:,.2f} SOL".replace(',', ' ') if x > 0 else "0 SOL")
                    if 'Avg Entry Market Cap (Weighted)' in display_early.columns:
                        display_early['Avg Entry Market Cap (Weighted)'] = display_early['Avg Entry Market Cap (Weighted)'].apply(lambda x: f"${x:,.0f}".replace(',', ' '))
                    if 'Transaction Count' in display_early.columns:
                        display_early['Transaction Count'] = display_early['Transaction Count'].apply(lambda x: f"{x:,}".replace(',', ' '))
                    
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
                        display_whales['Total USD Spent'] = display_whales['Total USD Spent'].apply(lambda x: f"${x:,.2f}".replace(',', ' '))
                    if 'Total SOL Spent' in display_whales.columns and display_whales['Total SOL Spent'].sum() > 0:
                        display_whales['Total SOL Spent'] = display_whales['Total SOL Spent'].apply(lambda x: f"{x:,.2f} SOL".replace(',', ' ') if x > 0 else "0 SOL")
                    if 'Avg Market Cap (Weighted)' in display_whales.columns:
                        display_whales['Avg Market Cap (Weighted)'] = display_whales['Avg Market Cap (Weighted)'].apply(lambda x: f"${x:,.0f}".replace(',', ' '))
                    if 'Transaction Count' in display_whales.columns:
                        display_whales['Transaction Count'] = display_whales['Transaction Count'].apply(lambda x: f"{x:,}".replace(',', ' '))
                    
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
            
            with tab4:
                st.subheader("💰 P&L Analysis")
                st.info("💡 **Comprehensive P&L tracking** - Analyzes buy (token2) vs sell (token1) transactions to calculate realized and unrealized profit/loss")
                
                if len(pnl_analysis) > 0:
                    # Create filtering and sorting controls
                    col_filter1, col_filter2, col_filter3 = st.columns(3)
                    
                    with col_filter1:
                        profit_filter = st.selectbox(
                            "Filter by P&L",
                            options=["All Wallets", "Profitable Only", "Loss-making Only"],
                            key="pnl_filter"
                        )
                    
                    with col_filter2:
                        sort_by = st.selectbox(
                            "Sort by",
                            options=["Total P&L (SOL)", "ROI %", "Realized P&L (SOL)", "Unrealized P&L (SOL)", "Total Bought", "Total Sold"],
                            key="pnl_sort"
                        )
                    
                    with col_filter3:
                        sort_order = st.selectbox(
                            "Sort Order",
                            options=["Descending", "Ascending"],
                            key="pnl_order"
                        )
                    
                    # Search functionality
                    search_wallet = st.text_input(
                        "🔍 Search by wallet address",
                        placeholder="Enter wallet address...",
                        key="wallet_search"
                    )
                    
                    # Apply filters
                    filtered_pnl = pnl_analysis.copy()
                    
                    # Profit filter
                    if profit_filter == "Profitable Only":
                        filtered_pnl = filtered_pnl[filtered_pnl['is_profitable'] == True]
                    elif profit_filter == "Loss-making Only":
                        filtered_pnl = filtered_pnl[filtered_pnl['is_profitable'] == False]
                    
                    # Search filter
                    if search_wallet:
                        filtered_pnl = filtered_pnl[filtered_pnl['wallet'].str.contains(search_wallet, case=False, na=False)]
                    
                    # Sorting
                    sort_column_map = {
                        "Total P&L (SOL)": "total_pnl_sol",
                        "ROI %": "roi_percentage", 
                        "Realized P&L (SOL)": "realized_pnl_sol",
                        "Unrealized P&L (SOL)": "unrealized_pnl_sol",
                        "Total Bought": "total_bought",
                        "Total Sold": "total_sold"
                    }
                    
                    sort_col = sort_column_map[sort_by]
                    ascending = sort_order == "Ascending"
                    filtered_pnl = filtered_pnl.sort_values(by=sort_col, ascending=ascending)
                    
                    if len(filtered_pnl) > 0:
                        # P&L Summary metrics
                        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                        
                        with col_metric1:
                            total_pnl_sol = filtered_pnl['total_pnl_sol'].sum()
                            st.metric("Total P&L (SOL)", f"{total_pnl_sol:,.2f} SOL".replace(',', ' '))
                        
                        with col_metric2:
                            avg_roi = filtered_pnl['roi_percentage'].mean()
                            st.metric("Average ROI", f"{avg_roi:.1f}%")
                        
                        with col_metric3:
                            realized_total_sol = filtered_pnl['realized_pnl_sol'].sum()
                            st.metric("Total Realized P&L", f"{realized_total_sol:,.2f} SOL".replace(',', ' '))
                        
                        with col_metric4:
                            unrealized_total_sol = filtered_pnl['unrealized_pnl_sol'].sum()
                            st.metric("Total Unrealized P&L", f"{unrealized_total_sol:,.2f} SOL".replace(',', ' '))
                        
                        # Format the dataframe for display
                        display_pnl = filtered_pnl.copy()
                        
                        # Show full wallet addresses for easy copy/paste
                        display_pnl['Wallet'] = display_pnl['wallet']
                        
                        # Format only SOL columns with proper styling and space separators
                        display_pnl['Total P&L (SOL)'] = display_pnl['total_pnl_sol'].apply(
                            lambda x: f"🟢 {x:,.2f}".replace(',', ' ') if x > 0 else f"🔴 {x:,.2f}".replace(',', ' ') if x < 0 else f"⚫ {x:,.2f}".replace(',', ' ')
                        )
                        
                        display_pnl['Realized P&L (SOL)'] = display_pnl['realized_pnl_sol'].apply(
                            lambda x: f"🟢 {x:,.2f}".replace(',', ' ') if x > 0 else f"🔴 {x:,.2f}".replace(',', ' ') if x < 0 else f"⚫ {x:,.2f}".replace(',', ' ')
                        )
                        
                        display_pnl['Unrealized P&L (SOL)'] = display_pnl['unrealized_pnl_sol'].apply(
                            lambda x: f"🟢 {x:,.2f}".replace(',', ' ') if x > 0 else f"🔴 {x:,.2f}".replace(',', ' ') if x < 0 else f"⚫ {x:,.2f}".replace(',', ' ')
                        )
                        
                        display_pnl['Tokens Bought'] = display_pnl['total_bought'].apply(
                            lambda x: f"{x:,.2f}".replace(',', ' ')
                        )
                        
                        display_pnl['Tokens Sold'] = display_pnl['total_sold'].apply(
                            lambda x: f"{x:,.2f}".replace(',', ' ')
                        )
                        
                        display_pnl['Avg Buy Price'] = display_pnl['avg_buy_price_usd'].apply(
                            lambda x: f"${x:.3f}" if x > 0 else "N/A"
                        )
                        
                        display_pnl['Avg Sell Price'] = display_pnl['avg_sell_price_usd'].apply(
                            lambda x: f"${x:.3f}" if x > 0 else "N/A"
                        )
                        
                        display_pnl['ROI %'] = display_pnl['roi_percentage'].apply(
                            lambda x: f"🟢 {x:.1f}%" if x > 0 else f"🔴 {x:.1f}%" if x < 0 else f"⚫ {x:.1f}%"
                        )
                        
                        display_pnl['Position'] = display_pnl['has_position'].apply(
                            lambda x: "🟡 Open" if x else "⚫ Closed"
                        )
                        
                        # Select columns for display - only SOL P&L columns
                        display_columns = [
                            'Wallet', 'Total P&L (SOL)', 'Realized P&L (SOL)', 'Unrealized P&L (SOL)',
                            'Tokens Bought', 'Tokens Sold', 
                            'Avg Buy Price', 'Avg Sell Price', 'ROI %', 'Position'
                        ]
                        
                        # Display the formatted table
                        st.dataframe(
                            display_pnl[display_columns], 
                            use_container_width=True,
                            height=400
                        )
                        
                        # Additional insights
                        st.subheader("📊 P&L Insights")
                        
                        col_insight1, col_insight2, col_insight3 = st.columns(3)
                        
                        with col_insight1:
                            st.write("**Top Performers:**")
                            top_3 = filtered_pnl.nlargest(3, 'total_pnl_sol')
                            for idx, row in top_3.iterrows():
                                st.code(f"{row['wallet']}")
                                st.write(f"P&L: {row['total_pnl_sol']:,.2f} SOL".replace(',', ' '))
                                st.write("---")
                        
                        with col_insight2:
                            st.write("**Biggest Losses:**")
                            bottom_3 = filtered_pnl.nsmallest(3, 'total_pnl_sol')
                            for idx, row in bottom_3.iterrows():
                                st.code(f"{row['wallet']}")
                                st.write(f"P&L: {row['total_pnl_sol']:,.2f} SOL".replace(',', ' '))
                                st.write("---")
                        
                        with col_insight3:
                            st.write("**Position Summary:**")
                            open_positions = len(filtered_pnl[filtered_pnl['has_position'] == True])
                            closed_positions = len(filtered_pnl[filtered_pnl['has_position'] == False])
                            st.write(f"• Open: {open_positions}")
                            st.write(f"• Closed: {closed_positions}")
                            st.write(f"• Total: {len(filtered_pnl)}")
                        
                        # Download button
                        csv_buffer = io.StringIO()
                        filtered_pnl.to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="📥 Download P&L Analysis CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"pnl_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.info("No results found with current filters.")
                
                else:
                    st.info("No transaction data available for P&L analysis. Please ensure your CSV contains both buy and sell transactions.")
            
            # Analysis insights
            st.header("💡 Key Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Market Cap Distribution")
                if not analyzed_df.empty:
                    min_cap = analyzed_df['market_cap'].min()
                    max_cap = analyzed_df['market_cap'].max()
                    median_cap = analyzed_df['market_cap'].median()
                    
                    st.write(f"**Min Market Cap:** ${min_cap:,.0f}".replace(',', ' '))
                    st.write(f"**Max Market Cap:** ${max_cap:,.0f}".replace(',', ' '))
                    st.write(f"**Median Market Cap:** ${median_cap:,.0f}".replace(',', ' '))
                    
                    # Add percentiles for better insight
                    p25 = analyzed_df['market_cap'].quantile(0.25)
                    p75 = analyzed_df['market_cap'].quantile(0.75)
                    st.write(f"**25th Percentile:** ${p25:,.0f}".replace(',', ' '))
                    st.write(f"**75th Percentile:** ${p75:,.0f}".replace(',', ' '))
                else:
                    st.info("No buy transaction data available for market cap analysis.")
            
            with col2:
                st.subheader("Transaction Volume")
                if not analyzed_df.empty:
                    value_col = next((col for col in analyzed_df.columns if col.lower() == 'value'), None)
                    if value_col:
                        total_usd_volume = analyzed_df[value_col].sum()
                        avg_tx_size = analyzed_df[value_col].mean()
                        
                        # Find wallet column properly
                        wallet_col = next((col for col in analyzed_df.columns if col.lower() in ['wallet', 'address', 'from']), None)
                        if wallet_col:
                            unique_wallets = analyzed_df[wallet_col].nunique()
                        else:
                            unique_wallets = "Unknown"
                        
                        st.write(f"**Total USD Volume:** ${total_usd_volume:,.2f}".replace(',', ' '))
                        st.write(f"**Average Transaction:** ${avg_tx_size:,.2f}".replace(',', ' '))
                        st.write(f"**Unique Wallets:** {unique_wallets:,}".replace(',', ' '))
                        
                        # Show SOL volume if available
                        if 'sol_amount' in analyzed_df.columns:
                            total_sol_volume = analyzed_df['sol_amount'].sum()
                            if total_sol_volume > 0:
                                avg_sol_tx = analyzed_df['sol_amount'].mean()
                                st.write(f"**Total SOL Volume:** {total_sol_volume:,.2f} SOL".replace(',', ' '))
                                st.write(f"**Average SOL per TX:** {avg_sol_tx:,.2f} SOL".replace(',', ' '))
                else:
                    st.info("No buy transaction data available for volume analysis.")
            
            # P&L Summary insights
            if not pnl_analysis.empty:
                st.subheader("📈 P&L Overview")
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    st.write("**Overall P&L:**")
                    total_traders = len(pnl_analysis)
                    profitable_count = len(pnl_analysis[pnl_analysis['is_profitable'] == True])
                    profitability_rate = (profitable_count / total_traders) * 100 if total_traders > 0 else 0
                    st.write(f"• Profitability Rate: {profitability_rate:.1f}%")
                    st.write(f"• Profitable Wallets: {profitable_count}")
                    st.write(f"• Loss-making Wallets: {total_traders - profitable_count}")
                
                with col4:
                    st.write("**P&L Distribution (SOL):**")
                    total_realized = pnl_analysis['realized_pnl_sol'].sum()
                    total_unrealized = pnl_analysis['unrealized_pnl_sol'].sum()
                    st.write(f"• Total Realized: {total_realized:,.2f} SOL".replace(',', ' '))
                    st.write(f"• Total Unrealized: {total_unrealized:,.2f} SOL".replace(',', ' '))
                    st.write(f"• Combined P&L: {total_realized + total_unrealized:,.2f} SOL".replace(',', ' '))
                
                with col5:
                    st.write("**Position Status:**")
                    open_positions = len(pnl_analysis[pnl_analysis['has_position'] == True])
                    closed_positions = len(pnl_analysis[pnl_analysis['has_position'] == False])
                    st.write(f"• Open Positions: {open_positions}")
                    st.write(f"• Closed Positions: {closed_positions}")
                    avg_roi = pnl_analysis['roi_percentage'].mean()
                    st.write(f"• Average ROI: {avg_roi:.1f}%")
            
            # Additional metrics for buy transactions
            if not analyzed_df.empty:
                st.subheader("📊 Additional Buy Metrics")
                col6, col7, col8 = st.columns(3)
                
                with col6:
                    early_count = len(early_entries)
                    st.write("**Early Entry Stats:**")
                    if early_count > 0:
                        early_total_usd = early_entries['total_usd_value'].sum() if 'total_usd_value' in early_entries.columns else 0
                        early_avg_usd = early_entries['total_usd_value'].mean() if 'total_usd_value' in early_entries.columns else 0
                        st.write(f"• Count: {early_count:,}".replace(',', ' '))
                        st.write(f"• Total Spent: ${early_total_usd:,.2f}".replace(',', ' '))
                        st.write(f"• Avg per Wallet: ${early_avg_usd:,.2f}".replace(',', ' '))
                    else:
                        st.write("• No early entries found")
                
                with col7:
                    whale_count = len(whale_wallets)
                    st.write("**Whale Wallet Stats:**")
                    if whale_count > 0:
                        whale_total_usd = whale_wallets['total_usd_value'].sum() if 'total_usd_value' in whale_wallets.columns else 0
                        whale_avg_usd = whale_wallets['total_usd_value'].mean() if 'total_usd_value' in whale_wallets.columns else 0
                        st.write(f"• Count: {whale_count:,}".replace(',', ' '))
                        st.write(f"• Total Spent: ${whale_total_usd:,.2f}".replace(',', ' '))
                        st.write(f"• Avg per Whale: ${whale_avg_usd:,.2f}".replace(',', ' '))
                    else:
                        st.write("• No whales found")
                
                with col8:
                    st.write("**Price Analysis:**")
                    min_price = analyzed_df['price'].min()
                    max_price = analyzed_df['price'].max()
                    avg_price = analyzed_df['price'].mean()
                    st.write(f"• Min Price: ${min_price:.3f}")
                    st.write(f"• Max Price: ${max_price:.3f}")
                    st.write(f"• Avg Price: ${avg_price:.3f}")
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please check your CSV format and token address.")
    
    elif uploaded_file is not None and not token_address:
        st.warning("⚠️ Please enter a token address to proceed with analysis.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Token Momentum Analyzer v2.0** | Built with Streamlit | Now with P&L Analysis")

if __name__ == "__main__":
    main() 