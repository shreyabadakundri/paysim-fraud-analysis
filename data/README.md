# Data

This project uses **PaySim** — a **synthetic** mobile-money transaction dataset (Lopez-Rojas et al., CC BY-SA 4.0). Do not present it as real company data on a resume; say “simulated transactions.”

## Option A — Kaggle (recommended for SQL / local CSV)

1. Download [Synthetic Financial Datasets For Fraud Detection](https://www.kaggle.com/datasets/ealaxi/paysim1).
2. Unzip and place the file here as `Fraud.csv`.
3. Load into MySQL (or run `python scripts/run_analysis.py --csv data/Fraud.csv`).

## Option B — No download (Python stream)

```bash
pip install -r requirements.txt
python scripts/run_analysis.py
```

This streams the same dataset from Hugging Face (`purulalwani/Synthetic-Financial-Datasets-For-Fraud-Detection`) and writes aggregates to `outputs/`.

## Columns (for SQL)

| Column | Description |
|--------|-------------|
| `step` | Simulated hour index |
| `type` | `CASH-IN`, `CASH-OUT`, `DEBIT`, `PAYMENT`, `TRANSFER` |
| `amount` | Transaction amount |
| `nameOrig` / `nameDest` | Customer IDs |
| `oldbalanceOrg` / `newbalanceOrig` | Sender balances before/after |
| `oldbalanceDest` / `newbalanceDest` | Receiver balances before/after |
| `isFraud` | Target (1 = fraud) |
| `isFlaggedFraud` | Built-in flag for transfers > 200,000 (not the same as the portfolio rule) |