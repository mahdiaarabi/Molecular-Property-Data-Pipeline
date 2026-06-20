-- ============================================================
-- Molecular Property Analysis Queries
-- Run against Snowflake MOLECULAR_DB
-- Author: Mahdi (Matt) Aarabi, Ph.D.
-- ============================================================

-- 1. Summary statistics by kinase target
SELECT
    target,
    COUNT(*)                            AS n_compounds,
    ROUND(AVG(pic50), 3)                AS avg_potency,
    ROUND(STDDEV(pic50), 3)             AS std_potency,
    ROUND(MIN(pic50), 3)                AS min_potency,
    ROUND(MAX(pic50), 3)                AS max_potency,
    ROUND(AVG(logp), 3)                 AS avg_lipophilicity,
    ROUND(AVG(mw), 1)                   AS avg_mol_weight
FROM compounds
WHERE data_quality = 'validated'
GROUP BY target
ORDER BY avg_potency DESC;


-- 2. Identify drug-like candidates (Lipinski-compliant with high potency)
SELECT
    name,
    target,
    pic50,
    logp,
    logs,
    mw,
    tpsa,
    lipinski_violations,
    solubility_class,
    potency_class
FROM compounds
WHERE lipinski_compliant = 1
  AND pic50 > 8.0
  AND data_quality = 'validated'
ORDER BY pic50 DESC;


-- 3. Cross-target property comparison using window functions
SELECT
    name,
    target,
    pic50,
    logp,
    ROUND(AVG(pic50) OVER (PARTITION BY target), 3)     AS target_avg_potency,
    ROUND(pic50 - AVG(pic50) OVER (PARTITION BY target), 3) AS potency_vs_target_avg,
    RANK() OVER (PARTITION BY target ORDER BY pic50 DESC)   AS potency_rank
FROM compounds
WHERE data_quality = 'validated'
ORDER BY target, potency_rank;


-- 4. Property correlation analysis (solubility vs lipophilicity)
SELECT
    solubility_class,
    COUNT(*)                    AS n_compounds,
    ROUND(AVG(logp), 3)        AS avg_logp,
    ROUND(AVG(pic50), 3)       AS avg_potency,
    ROUND(AVG(mw), 1)          AS avg_mw,
    SUM(lipinski_compliant)    AS n_lipinski_pass
FROM compounds
GROUP BY solubility_class
ORDER BY avg_logp;


-- 5. Outlier detection summary
SELECT
    name,
    target,
    pic50,
    logp,
    logs,
    mw,
    CASE WHEN pic50_outlier = 1 THEN 'YES' ELSE '' END AS pic50_flag,
    CASE WHEN logp_outlier  = 1 THEN 'YES' ELSE '' END AS logp_flag,
    CASE WHEN logs_outlier  = 1 THEN 'YES' ELSE '' END AS logs_flag,
    CASE WHEN mw_outlier    = 1 THEN 'YES' ELSE '' END AS mw_flag
FROM compounds
WHERE pic50_outlier = 1
   OR logp_outlier = 1
   OR logs_outlier = 1
   OR mw_outlier = 1
ORDER BY name;


-- 6. Aggregated quality metrics for reporting
SELECT
    'Total Compounds'           AS metric, CAST(COUNT(*) AS VARCHAR) AS value FROM compounds
UNION ALL
SELECT 'Validated Records',     CAST(SUM(CASE WHEN data_quality = 'validated' THEN 1 ELSE 0 END) AS VARCHAR) FROM compounds
UNION ALL
SELECT 'Lipinski Compliant',    CAST(SUM(lipinski_compliant) AS VARCHAR) FROM compounds
UNION ALL
SELECT 'High Potency (>8.0)',   CAST(SUM(CASE WHEN pic50 > 8.0 THEN 1 ELSE 0 END) AS VARCHAR) FROM compounds
UNION ALL
SELECT 'Outliers Flagged',      CAST(SUM(pic50_outlier + logp_outlier + logs_outlier + mw_outlier) AS VARCHAR) FROM compounds
UNION ALL
SELECT 'Unique Targets',        CAST(COUNT(DISTINCT target) AS VARCHAR) FROM compounds;
