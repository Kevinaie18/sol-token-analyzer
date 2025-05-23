# 🚀 Token Momentum Analyzer

A Streamlit Cloud-based analyzer for Solana token transaction data. Detects buy-side activity, calculates market cap dynamics, identifies early entries, and flags whale wallets.

## 📋 Features

- **CSV Upload & Parsing**: Auto-detects delimiters (`;` or `,`) and cleans transaction data
- **Buy-Side Filtering**: Identifies buy transactions where `token2 == token_address`
- **Market Cap Analysis**: Calculates price per token and market cap using total supply
- **Early Entry Detection**: Flags transactions below market cap threshold
- **Whale Wallet Identification**: Identifies high-value buyers based on USD thresholds
- **Downloadable Reports**: Export parsed transactions, early entries, and whale wallets as CSV

## 🏗️ Project Structure

```
token_momentum_analyzer/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── report_builder.py       # Analysis and report generation logic
├── utils/
│   └── parser.py           # CSV parsing and data cleaning
├── .streamlit/
│   └── config.toml         # Streamlit Cloud configuration
├── data/
│   └── sample.csv          # Example input file format
└── README.md              # This file
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sol-token-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501`

### Streamlit Cloud Deployment

1. Push this repository to GitHub
2. Connect your GitHub repo to [Streamlit Cloud](https://share.streamlit.io/)
3. Deploy with the default settings

## 📊 Usage Guide

### Input Requirements

**CSV Format (Solscan Export)**:
- Must contain columns: `token2`, `value`, `amount`
- Optional columns: `tx_hash`, `timestamp`, `wallet`, `token1`
- Supports both `,` and `;` delimiters

**Configuration Parameters**:
- **Token Address**: The Solana token address to analyze
- **Total Supply**: Token's total supply for market cap calculation
- **Early Entry Threshold**: Market cap below this value flags as early
- **Whale Threshold**: USD amount above this value flags as whale

### Analysis Output

The tool generates three downloadable reports:

#### 1. Parsed Transactions (`parsed_transactions.csv`)
- All buy-side transactions with calculated metrics
- Columns: tx_hash, timestamp, value, amount, price, market_cap, wallet, token1, token2

#### 2. Early Entries (`early_entries.csv`)
- Wallets that bought during early phase (low market cap)
- Columns: wallet, first_tx_time, total_value, avg_entry_cap, tx_count

#### 3. Whale Wallets (`whale_wallets.csv`)
- High-value buyers based on total USD spent
- Columns: wallet, total_value, first_entry_time, avg_market_cap, early_flag

## 🔧 Technical Details

### Data Processing Pipeline

1. **Upload & Parse**: Auto-detect delimiter and parse CSV
2. **Clean Data**: Remove empty rows, convert numeric fields, standardize timestamps
3. **Filter Buys**: Keep only rows where `token2 == token_address`
4. **Calculate Metrics**: Compute price (`value/amount`) and market cap (`price * total_supply`)
5. **Classify Wallets**: Tag early entries and whales based on thresholds
6. **Generate Reports**: Create structured output tables

### Key Calculations

- **Price per Token**: `value / amount`
- **Market Cap**: `price * total_supply`
- **Early Flag**: `market_cap < early_threshold`
- **Whale Flag**: `total_wallet_value > whale_threshold`

## 📈 Example Workflow

1. Export transaction data from Solscan as CSV
2. Upload CSV file to the analyzer
3. Configure token address and thresholds
4. Review analysis results in the dashboard
5. Download reports for further analysis

## 🛠️ Development

### Adding New Features

The modular architecture makes it easy to extend:

- **Parser logic**: Modify `utils/parser.py`
- **Analysis functions**: Update `report_builder.py`
- **UI components**: Enhance `app.py`

### Testing

Test with your own Solscan CSV exports or use the provided `data/sample.csv` as a reference format.

## 📝 Requirements

- Python 3.10+
- Streamlit 1.28+
- Pandas 2.0+
- NumPy 1.24+

## 📄 License

This project is for private use by Oty Aie for token analysis and investment research.

## 🤝 Support

For issues or questions, please check the CSV format requirements and ensure all required columns are present in your data export. 