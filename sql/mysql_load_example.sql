-- Example: load PaySim into MySQL (adjust paths and LOCAL INFILE policy).

CREATE DATABASE IF NOT EXISTS paysim_db;
USE paysim_db;

DROP TABLE IF EXISTS paysim;

CREATE TABLE paysim (
  step INT,
  type VARCHAR(20),
  amount DOUBLE,
  nameOrig VARCHAR(32),
  oldbalanceOrg DOUBLE,
  newbalanceOrig DOUBLE,
  nameDest VARCHAR(32),
  oldbalanceDest DOUBLE,
  newbalanceDest DOUBLE,
  isFraud TINYINT,
  isFlaggedFraud TINYINT
);

LOAD DATA LOCAL INFILE 'C:/path/to/Fraud.csv'
INTO TABLE paysim
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Then run queries in analysis_queries.sql