-- PaySim fraud analysis (MySQL syntax)
-- Table: paysim (load from Fraud.csv)

-- Returns fraud count and fraud rate (%) for each transaction type.
SELECT
  type,
  COUNT(*) AS txn_count,
  SUM(isFraud) AS fraud_count,
  ROUND(100.0 * SUM(isFraud) / COUNT(*), 4) AS fraud_rate_pct
FROM paysim
GROUP BY type
ORDER BY fraud_rate_pct DESC, fraud_count DESC;

-- Returns average, min, and max transaction amount for fraud vs non-fraud.
SELECT
  CASE WHEN isFraud = 1 THEN 'fraud' ELSE 'legitimate' END AS label,
  COUNT(*) AS txn_count,
  ROUND(AVG(amount), 2) AS avg_amount,
  ROUND(MIN(amount), 2) AS min_amount,
  ROUND(MAX(amount), 2) AS max_amount
FROM paysim
GROUP BY isFraud;

-- Returns fraud volume and rate within fixed amount bands.
SELECT
  CASE
    WHEN amount < 10000 THEN '1. Under 10k'
    WHEN amount < 50000 THEN '2. 10k to 50k'
    WHEN amount < 100000 THEN '3. 50k to 100k'
    WHEN amount < 500000 THEN '4. 100k to 500k'
    ELSE '5. 500k and above'
  END AS amount_band,
  COUNT(*) AS txn_count,
  SUM(isFraud) AS fraud_count,
  ROUND(100.0 * SUM(isFraud) / COUNT(*), 4) AS fraud_rate_pct
FROM paysim
GROUP BY amount_band
ORDER BY amount_band;

-- Returns originator and recipient accounts appearing in more than one fraudulent transaction.
SELECT account_id, role, fraud_txn_count, ROUND(fraud_amount, 2) AS fraud_amount
FROM (
  SELECT
    nameOrig AS account_id,
    'sender' AS role,
    COUNT(*) AS fraud_txn_count,
    SUM(amount) AS fraud_amount
  FROM paysim
  WHERE isFraud = 1
  GROUP BY nameOrig
  HAVING COUNT(*) > 1

  UNION ALL

  SELECT
    nameDest,
    'receiver',
    COUNT(*),
    SUM(amount)
  FROM paysim
  WHERE isFraud = 1
  GROUP BY nameDest
  HAVING COUNT(*) > 1
) repeated
ORDER BY fraud_txn_count DESC;

-- Returns catch rate and precision for empty-account TRANSFER rule.
SELECT
  SUM(isFraud) AS total_fraud,
  SUM(rule_flag) AS flagged_txns,
  SUM(CASE WHEN rule_flag = 1 AND isFraud = 1 THEN 1 ELSE 0 END) AS fraud_caught,
  ROUND(100.0 * SUM(CASE WHEN rule_flag = 1 AND isFraud = 1 THEN 1 ELSE 0 END)
        / NULLIF(SUM(isFraud), 0), 2) AS catch_rate_pct,
  ROUND(100.0 * SUM(CASE WHEN rule_flag = 1 AND isFraud = 1 THEN 1 ELSE 0 END)
        / NULLIF(SUM(rule_flag), 0), 2) AS precision_pct
FROM (
  SELECT
    isFraud,
    CASE
      WHEN type = 'TRANSFER'
       AND newbalanceOrig = 0
       AND ABS(oldbalanceOrg - amount) < 0.01
      THEN 1 ELSE 0
    END AS rule_flag
  FROM paysim
) scored;