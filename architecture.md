# Architecture – Token Momentum Analyzer

## Overview

This document describes the system architecture for the Token Momentum Analyzer, a Streamlit Cloud-hosted app for analyzing Solana token transaction data (CSV format).

---

## 1. Components

### 1.1 Frontend
- **Framework**: Streamlit
- **Hosting**: Streamlit Cloud
- **Inputs**:
  - File uploader (CSV)
  - Sidebar form for token configuration:
    - Token address
    - Total supply
    - Market cap thresholds
    - Optional: SOL/USD price
- **Outputs**:
  - Transaction table
  - Early entry table
  - Whale wallet table
  - CSV download buttons

### 1.2 Backend
- **Language**: Python 3.10+
- **Libraries**:
  - `pandas`: for data cleaning and analysis
  - `numpy`: for numerical operations
  - `streamlit`: for UI
- **Logic Flow**:
  1. Parse and clean CSV
  2. Filter buy-side txs where `token2 == token_address`
  3. Compute:
     - Price per token = value / amount
     - Market cap = price * total_supply
  4. Classify wallets as early or whale
  5. Render tables and enable downloads

---

## 2. File Structure

```
token_momentum_analyzer/
├── app.py                  # Main Streamlit entrypoint
├── requirements.txt        # Python dependencies
├── report_builder.py       # Logic for structuring output CSVs
├── utils/
│   └── parser.py           # Delimiter detection, CSV parsing
├── .streamlit/
│   └── config.toml         # Streamlit Cloud configuration
├── data/
│   └── sample.csv          # Example input file
└── README.md
```

---

## 3. Data Flow Diagram

1. **CSV Upload** → Streamlit file uploader
2. **Parser** → auto-detects delimiter, parses to dataframe
3. **Buy Filter** → `df[token2] == token_address`
4. **Calculation** → price, market cap, wallet tagging
5. **Output** → 3 downloadable tables: parsed, early, whales

---

## 4. Deployment

- **Streamlit Cloud**
  - Push to GitHub
  - Link repo to Streamlit Cloud
  - Configure in `.streamlit/config.toml`:
    - `[server] headless = true`
    - `enableCORS = false`

---

## 5. Notes

- App is stateless: no persistent database or wallet tracking
- All computation is done in-session from uploaded files
- Report generation is instant and lightweight

