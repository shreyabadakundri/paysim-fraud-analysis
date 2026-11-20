# PaySim fraud analysis

Portfolio project: **where fraud shows up** in simulated mobile-money transactions (PaySim), **how amount relates to risk**, and whether a **simple rule-based flag** catches a useful share of fraud.

**Stack:** SQL (MySQL), Python, Power BI  
**Data:** [PaySim / Synthetic Financial Datasets](https://www.kaggle.com/datasets/ealaxi/paysim1) — **synthetic**, not production data. Say that clearly on a resume.

---

## Business questions

1. Which **transaction types** drive fraud count and fraud **rate**?
2. How do **transaction amounts** differ for fraud vs legitimate rows, and at which **amount bands** does fraud rate rise?
3. Can a **rule** (transfer that empties the sender balance) catch fraud with acceptable **precision** for manual review?

---

## Repository layout

| Path | Purpose |
|------|---------|
| `sql/analysis_queries.sql` | Five MySQL queries (commented) |
| `sql/mysql_load_example.sql` | Optional `LOAD DATA` template |
| `scripts/run_analysis.py` | Builds `outputs/` from CSV or Hugging Face stream |
| `powerbi/` | Dashboard notes + DAX measures |
| `data/README.md` | How to download `Fraud.csv` |
| `outputs/` | Aggregates for SQL cross-check and Power BI |

---

## Quick start

```bash
pip install -r requirements.txt
python scripts/run_analysis.py
```

With a local Kaggle file:

```bash
python scripts/run_analysis.py --csv data/Fraud.csv
```

MySQL: load `Fraud.csv` (see `sql/mysql_load_example.sql`), then run `sql/analysis_queries.sql`.

---

## Suspicious-transfer rule

**Flag when:**

- `type = 'TRANSFER'`
- `newbalanceOrig = 0`
- `ABS(oldbalanceOrg - amount) < 0.01` (whole balance moved)

**Metrics:**

- **Catch rate (recall)** = flagged fraud ÷ all fraud  
- **Precision** = flagged fraud ÷ all flagged rows  

Report both. Do not rely on accuracy alone — fraud is ~0.13% of rows.

---

## Key findings

> Re-run `python scripts/run_analysis.py` to refresh numbers. Values below match the standard PaySim release (6.36M rows); your run should align unless the source file differs.

1. **Fraud is confined to cash movement.** In PaySim, fraudulent rows appear only under **`TRANSFER`** and **`CASH_OUT`**; `PAYMENT`, `CASH_IN`, and `DEBIT` have **zero** labeled fraud. Risk reviews should prioritize those two types first.

2. **Fraud amounts are large but overlap legitimate tails.** Average fraud amount is on the order of **hundreds of thousands** (simulator currency), above typical legitimate means, with the highest **fraud rates** in upper amount bands — but volume still lives in smaller bands, so rules need type filters, not amount alone.

3. **Empty-account transfers are a strong screening signal.** The drain-and-zero-balance rule flags a minority of all transactions but captures a **high share of `TRANSFER` fraud** with **strong precision** on flagged rows — suitable for **queues**, not automatic blocks, until you model false positives on live data.

See `outputs/metrics.json` after running the script for exact counts, rates, and rule catch/precision.

---

## Power BI

Import `outputs/fraud_by_type.csv` and `outputs/fraud_by_amount_band.csv`. Details in `powerbi/README.md`.

---

## Resume / interview notes

- Credit **PaySim / synthetic data** and Lopez-Rojas et al. (simulator paper).
- Verify every number in this README by running the script yourself before interviews.
- `isFlaggedFraud` (transfers > 200k) is **not** the same as the portfolio rule — compare both if you extend the project.

---

## License

Project code: MIT (add a `LICENSE` file if you prefer). Dataset: follow the [Kaggle / PaySim license](https://www.kaggle.com/datasets/ealaxi/paysim1) (CC BY-SA 4.0).