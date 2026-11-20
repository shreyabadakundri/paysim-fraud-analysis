"""
PaySim fraud analysis — run locally on Fraud.csv or stream from Hugging Face.

Usage:
  python scripts/run_analysis.py
  python scripts/run_analysis.py --csv data/Fraud.csv
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

BANDS = (
    (10_000, "1. Under 10k"),
    (50_000, "2. 10k to 50k"),
    (100_000, "3. 50k to 100k"),
    (500_000, "4. 100k to 500k"),
    (float("inf"), "5. 500k and above"),
)


def amount_band(amount: float) -> str:
    for limit, label in BANDS:
        if amount < limit:
            return label
    return BANDS[-1][1]


@dataclass
class Metrics:
    total_rows: int = 0
    total_fraud: int = 0
    type_txns: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    type_fraud: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    legit_amount_sum: float = 0.0
    legit_amount_n: int = 0
    fraud_amount_sum: float = 0.0
    fraud_amount_n: int = 0
    legit_amount_min: float | None = None
    legit_amount_max: float | None = None
    fraud_amount_min: float | None = None
    fraud_amount_max: float | None = None
    band_txns: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    band_fraud: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    fraud_orig_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    fraud_dest_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    fraud_orig_amount: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    fraud_dest_amount: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    rule_flags: int = 0
    rule_fraud_caught: int = 0


def update(metrics: Metrics, row: dict) -> None:
    metrics.total_rows += 1
    txn_type = row["type"]
    amount = float(row["amount"])
    is_fraud = int(row["isFraud"]) == 1

    metrics.type_txns[txn_type] += 1
    if is_fraud:
        metrics.total_fraud += 1
        metrics.type_fraud[txn_type] += 1
        metrics.fraud_amount_sum += amount
        metrics.fraud_amount_n += 1
        metrics.fraud_amount_min = (
            amount if metrics.fraud_amount_min is None else min(metrics.fraud_amount_min, amount)
        )
        metrics.fraud_amount_max = (
            amount if metrics.fraud_amount_max is None else max(metrics.fraud_amount_max, amount)
        )
        orig = row["nameOrig"]
        dest = row["nameDest"]
        metrics.fraud_orig_counts[orig] += 1
        metrics.fraud_dest_counts[dest] += 1
        metrics.fraud_orig_amount[orig] += amount
        metrics.fraud_dest_amount[dest] += amount
    else:
        metrics.legit_amount_sum += amount
        metrics.legit_amount_n += 1
        metrics.legit_amount_min = (
            amount if metrics.legit_amount_min is None else min(metrics.legit_amount_min, amount)
        )
        metrics.legit_amount_max = (
            amount if metrics.legit_amount_max is None else max(metrics.legit_amount_max, amount)
        )

    band = amount_band(amount)
    metrics.band_txns[band] += 1
    if is_fraud:
        metrics.band_fraud[band] += 1

    old_bal = float(row["oldbalanceOrg"])
    new_bal = float(row["newbalanceOrig"])
    if (
        txn_type == "TRANSFER"
        and new_bal == 0
        and abs(old_bal - amount) < 0.01
    ):
        metrics.rule_flags += 1
        if is_fraud:
            metrics.rule_fraud_caught += 1


def iter_hf_rows():
    from datasets import load_dataset

    ds = load_dataset(
        "purulalwani/Synthetic-Financial-Datasets-For-Fraud-Detection",
        split="train",
        streaming=True,
    )
    for row in ds:
        yield row


def iter_csv_rows(path: Path):
    import csv

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def repeated_accounts(metrics: Metrics, top_n: int = 15):
    rows = []
    for account_id, count in metrics.fraud_orig_counts.items():
        if count > 1:
            rows.append(
                ("sender", account_id, count, round(metrics.fraud_orig_amount[account_id], 2))
            )
    for account_id, count in metrics.fraud_dest_counts.items():
        if count > 1:
            rows.append(
                ("receiver", account_id, count, round(metrics.fraud_dest_amount[account_id], 2))
            )
    rows.sort(key=lambda x: x[2], reverse=True)
    return rows[:top_n]


def build_report(metrics: Metrics) -> dict:
    fraud_rate_overall = 100.0 * metrics.total_fraud / metrics.total_rows
    by_type = []
    for txn_type in sorted(metrics.type_txns.keys()):
        txns = metrics.type_txns[txn_type]
        fraud = metrics.type_fraud[txn_type]
        by_type.append(
            {
                "type": txn_type,
                "txn_count": txns,
                "fraud_count": fraud,
                "fraud_rate_pct": round(100.0 * fraud / txns, 4),
                "pct_of_all_fraud": round(100.0 * fraud / metrics.total_fraud, 2),
            }
        )
    by_type.sort(key=lambda x: (-x["fraud_rate_pct"], -x["fraud_count"]))

    by_band = []
    for _, label in BANDS:
        txns = metrics.band_txns[label]
        fraud = metrics.band_fraud[label]
        by_band.append(
            {
                "amount_band": label,
                "txn_count": txns,
                "fraud_count": fraud,
                "fraud_rate_pct": round(100.0 * fraud / txns, 4) if txns else 0,
            }
        )

    catch = (
        100.0 * metrics.rule_fraud_caught / metrics.total_fraud if metrics.total_fraud else 0
    )
    precision = (
        100.0 * metrics.rule_fraud_caught / metrics.rule_flags if metrics.rule_flags else 0
    )

    return {
        "dataset": "PaySim (synthetic)",
        "total_transactions": metrics.total_rows,
        "total_fraud": metrics.total_fraud,
        "overall_fraud_rate_pct": round(fraud_rate_overall, 4),
        "fraud_by_type": by_type,
        "amount_comparison": {
            "legitimate": {
                "txn_count": metrics.legit_amount_n,
                "avg_amount": round(metrics.legit_amount_sum / metrics.legit_amount_n, 2),
                "min_amount": metrics.legit_amount_min,
                "max_amount": metrics.legit_amount_max,
            },
            "fraud": {
                "txn_count": metrics.fraud_amount_n,
                "avg_amount": round(metrics.fraud_amount_sum / metrics.fraud_amount_n, 2),
                "min_amount": metrics.fraud_amount_min,
                "max_amount": metrics.fraud_amount_max,
            },
        },
        "fraud_by_amount_band": by_band,
        "repeated_fraud_accounts_top15": [
            {"role": r[0], "account_id": r[1], "fraud_txn_count": r[2], "fraud_amount": r[3]}
            for r in repeated_accounts(metrics)
        ],
        "empty_account_transfer_rule": {
            "description": "TRANSFER where newbalanceOrig = 0 and amount drains oldbalanceOrg",
            "flagged_txns": metrics.rule_flags,
            "fraud_caught": metrics.rule_fraud_caught,
            "catch_rate_pct": round(catch, 2),
            "precision_pct": round(precision, 2),
        },
    }


def write_csv_outputs(out_dir: Path, report: dict) -> None:
    import csv

    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "fraud_by_type.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["type", "txn_count", "fraud_count", "fraud_rate_pct", "pct_of_all_fraud"],
        )
        w.writeheader()
        w.writerows(report["fraud_by_type"])

    with (out_dir / "fraud_by_amount_band.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["amount_band", "txn_count", "fraud_count", "fraud_rate_pct"]
        )
        w.writeheader()
        w.writerows(report["fraud_by_amount_band"])

    with (out_dir / "repeated_fraud_accounts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["role", "account_id", "fraud_txn_count", "fraud_amount"]
        )
        w.writeheader()
        w.writerows(report["repeated_fraud_accounts_top15"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, help="Path to Fraud.csv (default: stream Hugging Face)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_dir = root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics = Metrics()
    row_iter = iter_csv_rows(args.csv) if args.csv else iter_hf_rows()

    for i, row in enumerate(row_iter, start=1):
        update(metrics, row)
        if i % 500_000 == 0:
            print(f"Processed {i:,} rows…")

    report = build_report(metrics)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv_outputs(out_dir, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()