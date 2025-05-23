# PRD – Token Momentum Analyzer (Streamlit Cloud Version)

**Project Title**: Token Momentum Analyzer  
**Platform**: Streamlit Cloud  
**Owner**: Oty Aie  
**Version**: 1.7  
**Date**: 23 May 2025  

---

## 1. Purpose

Deploy a self-serve, Streamlit Cloud-based analyzer to review token transaction data (e.g., from Solscan). The app detects buy-side activity for a specific token address, calculates market cap dynamics using USD value per row, flags early entries, and identifies whales — all with a downloadable report format.

---

## 2. Target User

- **Oty Aie**: Analyst and investor using this privately to screen tokens, monitor early capital inflow, and study wallet behavior.

---

## 3. Scope

- Input: SPL transaction CSV (Solana)
- Output: Cleaned, labeled data tables and downloadable reports
- Core: Detect buys (`token2 == token_address`), calculate market cap and wallet signals

---

## 4. Features

### 4.1. CSV Upload and Parsing
- Upload CSV (Solscan export)
- Auto-detect delimiter (`;` or `,`)
- Clean and standardize transaction fields
- Handle missing or malformed rows gracefully

### 4.2. Token Configuration (Manual Inputs)
- **Token address** (required): used to detect buy-side transactions via `token2`
- **Total supply** (required)
- **SOL/USD** (optional fallback if `value` is missing)
- **Market cap thresholds**: for early entry flags

### 4.3. Core Calculations
- **Buy Detection**: Keep rows where `token2 == token_address`
- **Price** = `value / amount`
- **Market Cap** = `price * total_supply`
- Classify transactions:
  - **Early Buy**: market cap < threshold
  - **Whale**: total USD bought > wallet threshold (e.g., $10k or top 1%)

### 4.4. Streamlit Cloud UI Components
- Sidebar for configuration inputs
- File uploader for CSV
- Display of:
  - Parsed transactions (raw + cleaned)
  - Early entries table
  - Whale wallet table
- Download buttons for each report

### 4.5. Report Structuring
Each downloadable report will follow this structure:

#### A. `parsed_transactions.csv`
| Column             | Description                                      |
|--------------------|--------------------------------------------------|
| tx_hash            | Transaction hash (if available)                  |
| timestamp          | Transaction time                                 |
| value              | USD value of the transaction                     |
| amount             | Token amount transferred                         |
| price              | USD price per token (value / amount)             |
| market_cap         | Calculated as price * total_supply               |
| wallet             | Buyer's address                                  |
| token1/token2      | Tokens involved in swap                          |

#### B. `early_entries.csv`
| wallet             | Buyer address                                    |
| first_tx_time      | Timestamp of first early buy                     |
| total_value        | Total USD spent in early phase                   |
| avg_entry_cap      | Average market cap at time of entry              |
| tx_count           | Number of early entries                          |

#### C. `whale_wallets.csv`
| wallet             | Wallet address                                   |
| total_value        | Total USD bought                                 |
| first_entry_time   | Time of first buy                                |
| avg_market_cap     | Average cap during buys                          |
| early_flag         | True if wallet was also early                    |

---

## 5. Architecture
| Component   | Tool              |
|-------------|-------------------|
| UI          | Streamlit Cloud   |
| Processing  | Python (Pandas)   |
| Storage     | None (session-only)|

---

## 6. MVP Tasks
- [ ] UI layout + input config
- [ ] Buy-side filtering (`token2 == token_address`)
- [ ] Price + market cap computation
- [ ] Wallet tagging logic (early, whale)
- [ ] Structured output tables
- [ ] Download buttons

---

## 7. Deliverables
- Streamlit Cloud deployment
- Three downloadable reports per token
- Clean and interactive analysis interface
