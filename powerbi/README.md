# Power BI

## Quick dashboard (no 6M-row import)

1. Run `python scripts/run_analysis.py` once (or use committed files in `outputs/`).
2. **Get data** → Text/CSV:
   - `outputs/fraud_by_type.csv`
   - `outputs/fraud_by_amount_band.csv`
3. Build visuals:
   - **Matrix**: `type` × `fraud_rate_pct`, `fraud_count`
   - **Clustered bar**: `amount_band` × `fraud_count` (sort by band name)
   - **Card**: overall fraud rate from `metrics.json` → `overall_fraud_rate_pct`
   - **Card**: rule `catch_rate_pct` and `precision_pct` from `metrics.json`

## Optional: full dataset

Only import `Fraud.csv` if you need row-level drill-through; prefer aggregated CSVs for portfolio dashboards.

DAX for a full transaction model: see `DAX_measures.txt`.