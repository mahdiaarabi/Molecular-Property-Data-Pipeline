"""
Step 3: Load Cleaned Data into Snowflake
========================================
Creates database schema and loads the cleaned molecular
property dataset into Snowflake for SQL-based analysis.

Author: Mahdi Aarabi, Ph.D.
"""

import snowflake.connector
import pandas as pd
import sys
from config import (
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
    SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_WAREHOUSE,
)


def get_snowflake_connection():
    """Establish connection to Snowflake."""
    passcode = input("Enter MFA code from Authenticator: ")
    return snowflake.connector.connect(
        account = "XXXXXXX",
	user = "XXXXXXX",
	password = "XXXXXXX",
	database = "MOLECULAR_DB",
	schema = "PUBLIC",
	warehouse = "COMPUTE_WH",
        passcode=passcode,
    )


def setup_database(cursor):
    """Create database, schema, and tables."""
    print("Setting up database schema...")

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DATABASE}")
    cursor.execute(f"USE DATABASE {SNOWFLAKE_DATABASE}")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_SCHEMA}")
    cursor.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")

    # Main compounds table
    cursor.execute("""
        CREATE OR REPLACE TABLE compounds (
            record_id       VARCHAR(10) PRIMARY KEY,
            name            VARCHAR(100) NOT NULL,
            smiles          VARCHAR(500) NOT NULL,
            target          VARCHAR(50),
            pic50           FLOAT,
            logp            FLOAT,
            logs            FLOAT,
            mw              FLOAT,
            tpsa            FLOAT,
            hba             INT,
            hbd             INT,
            lipinski_violations  INT,
            lipinski_compliant   INT,
            ligand_efficiency    FLOAT,
            solubility_class     VARCHAR(30),
            potency_class        VARCHAR(20),
            pic50_outlier        INT,
            logp_outlier         INT,
            logs_outlier         INT,
            mw_outlier           INT,
            data_quality         VARCHAR(20),
            load_timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
    """)
    print("  Created table: compounds")

    # Summary statistics view
    cursor.execute("""
        CREATE OR REPLACE VIEW compound_summary AS
        SELECT
            target,
            COUNT(*)                        AS n_compounds,
            ROUND(AVG(pic50), 3)            AS avg_pic50,
            ROUND(AVG(logp), 3)             AS avg_logp,
            ROUND(AVG(logs), 3)             AS avg_logs,
            ROUND(AVG(mw), 1)               AS avg_mw,
            SUM(lipinski_compliant)          AS n_lipinski_compliant,
            ROUND(100.0 * SUM(lipinski_compliant) / COUNT(*), 1) AS pct_lipinski
        FROM compounds
        GROUP BY target
    """)
    print("  Created view: compound_summary")

    # Potency ranking view
    cursor.execute("""
        CREATE OR REPLACE VIEW potency_ranking AS
        SELECT
            record_id,
            name,
            target,
            pic50,
            logp,
            logs,
            lipinski_compliant,
            RANK() OVER (PARTITION BY target ORDER BY pic50 DESC) AS potency_rank
        FROM compounds
        WHERE data_quality = 'validated'
    """)
    print("  Created view: potency_ranking")


def load_data(cursor, df):
    """Load cleaned DataFrame into Snowflake compounds table."""
    print(f"\nLoading {len(df)} records into Snowflake...")

    # Select columns matching the table schema
    cols = [
        "record_id", "name", "smiles", "target", "pic50", "logp", "logs",
        "mw", "tpsa", "hba", "hbd", "lipinski_violations", "lipinski_compliant",
        "ligand_efficiency", "solubility_class", "potency_class",
        "pic50_outlier", "logp_outlier", "logs_outlier", "mw_outlier",
        "data_quality",
    ]
    df_load = df[cols].copy()

    # Convert categorical to string for Snowflake
    for col in ["solubility_class", "potency_class"]:
        df_load[col] = df_load[col].astype(str)

    # Insert rows
    placeholders = ", ".join(["%s"] * len(cols))
    insert_sql = f"INSERT INTO compounds ({', '.join(cols)}) VALUES ({placeholders})"

    rows = [tuple(row) for row in df_load.itertuples(index=False, name=None)]
    cursor.executemany(insert_sql, rows)
    print(f"  Loaded {len(rows)} records successfully.")


def verify_load(cursor):
    """Run verification queries."""
    print("\nVerification queries:")

    cursor.execute("SELECT COUNT(*) FROM compounds")
    count = cursor.fetchone()[0]
    print(f"  Total records in compounds table: {count}")

    cursor.execute("SELECT * FROM compound_summary ORDER BY n_compounds DESC")
    print("\n  Compound Summary by Target:")
    print(f"  {'Target':<15} {'N':>5} {'Avg pIC50':>10} {'Avg logP':>10} {'% Lipinski':>12}")
    print("  " + "-" * 55)
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} {row[1]:>5} {row[2]:>10.3f} {row[3]:>10.3f} {row[6]:>11.1f}%")

    cursor.execute("""
        SELECT name, target, pic50, potency_rank
        FROM potency_ranking
        WHERE potency_rank <= 3
        ORDER BY target, potency_rank
    """)
    print("\n  Top 3 Most Potent Compounds per Target:")
    print(f"  {'Name':<20} {'Target':<15} {'pIC50':>8} {'Rank':>6}")
    print("  " + "-" * 52)
    for row in cursor.fetchall():
        print(f"  {row[0]:<20} {row[1]:<15} {row[2]:>8.2f} {row[3]:>6}")


def main():
    print("=" * 60)
    print("STEP 3: Load Data into Snowflake")
    print("=" * 60)

    # Load cleaned data
    try:
        df = pd.read_csv("data/kinase_inhibitors_cleaned.csv")
    except FileNotFoundError:
        print("Error: Run 02_clean_transform.py first.")
        sys.exit(1)

    # Connect to Snowflake
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        setup_database(cursor)
        load_data(cursor, df)
        verify_load(cursor)
        conn.commit()
        print("\nStep 3 complete: Data loaded into Snowflake.")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
