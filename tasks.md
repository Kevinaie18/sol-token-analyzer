# tasks.md – Token Momentum Analyzer (Streamlit Cloud)

Each task below is atomic, testable, and contributes directly to the MVP described in the PRD.

---

## PHASE 1: Setup & Input

### Task 1.1 – Streamlit Scaffold
- Create `app.py` with a basic Streamlit layout
- Include header, sidebar, and file uploader
- Check app loads correctly on Streamlit Cloud

### Task 1.2 – Sidebar Configuration Form
- Add inputs for:
  - Token address
  - Total supply
  - Market cap thresholds
  - Optional SOL/USD price
- Validate numeric fields and display values in real time

---

## PHASE 2: CSV Parsing & Cleaning

### Task 2.1 – Upload & Delimiter Detection
- Implement upload function and detect delimiter
- Accept `.csv` with either `,` or `;`

### Task 2.2 – Normalize Data
- Clean missing or malformed rows
- Convert numeric strings to float
- Standardize date/time format

---

## PHASE 3: Logic Implementation

### Task 3.1 – Buy-Side Transaction Filtering
- Filter rows where `token2 == token_address`
- Create `filtered_df` with only buy transactions

### Task 3.2 – Price & Market Cap Calculation
- Compute `price = value / amount`
- Compute `market_cap = price * total_supply`
- Append new columns to DataFrame

### Task 3.3 – Early Entry Classification
- Compare each market cap to user-defined thresholds
- Tag transaction as `early = True/False`

### Task 3.4 – Whale Wallet Detection
- Aggregate per wallet:
  - Total value
  - First entry time
  - Tx count
- Tag whales based on value threshold or percentile

---

## PHASE 4: Output Display & Export

### Task 4.1 – Transaction Table Display
- Show parsed table (with pagination)
- Sortable by timestamp, value, or market cap

### Task 4.2 – Early Entry Table
- Show summary of wallets classified as early

### Task 4.3 – Whale Wallet Table
- Show whale wallet info with filters

### Task 4.4 – CSV Download Buttons
- Enable download for:
  - parsed_transactions.csv
  - early_entries.csv
  - whale_wallets.csv

---

## PHASE 5: Deployment

### Task 5.1 – Create `.streamlit/config.toml`
- Configure for headless cloud deployment

### Task 5.2 – GitHub Repo + Streamlit Link
- Push code to GitHub
- Link to Streamlit Cloud
- Confirm successful cloud deployment

