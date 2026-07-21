"""
Step 2: Clean, Transform, and Validate Data
============================================
Pulls raw data from S3, applies cleaning and transformation
routines, performs statistical validation, and uploads the
cleaned dataset back to S3.

Author: Mahdi Aarabi, Ph.D.
"""

import boto3
import pandas as pd
import numpy as np
import io
import sys
from config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME
)


def create_s3_client():
    """Initialize AWS S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def read_csv_from_s3(s3_client, bucket, key):
    """Read a CSV file from S3 into a Pandas DataFrame."""
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(response["Body"].read()))


def upload_df_to_s3(s3_client, df, bucket, key):
    """Upload a DataFrame as CSV to S3."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())
    print(f"Uploaded cleaned data -> s3://{bucket}/{key}")


def clean_and_transform(df):
    """
    Apply data cleaning and transformation pipeline.

    Steps:
        1. Remove duplicates by compound name
        2. Validate SMILES strings (non-null, non-empty)
        3. Handle missing values
        4. Standardize column names (lowercase, underscores)
        5. Add computed fields (drug-likeness flags)
        6. Flag outliers using IQR method
        7. Categorize compounds by property ranges
    """
    print(f"\nRaw data: {len(df)} records, {len(df.columns)} columns")

    # --- Step 1: Remove duplicates ---
    n_before = len(df)
    df = df.drop_duplicates(subset=["name"], keep="first").reset_index(drop=True)
    n_dupes = n_before - len(df)
    print(f"  Removed {n_dupes} duplicate records")

    # --- Step 2: Validate SMILES ---
    invalid_smiles = df["smiles"].isna() | (df["smiles"].str.strip() == "")
    if invalid_smiles.any():
        print(f"  Dropping {invalid_smiles.sum()} records with invalid SMILES")
        df = df[~invalid_smiles].reset_index(drop=True)

    # --- Step 3: Handle missing values ---
    numeric_cols = ["pIC50", "logP", "logS", "MW", "TPSA", "HBA", "HBD"]
    for col in numeric_cols:
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f"  Filled {n_missing} missing values in '{col}' with median ({median_val:.2f})")

    # --- Step 4: Standardize column names ---
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # --- Step 5: Add computed fields ---
    # Lipinski's Rule of Five compliance
    df["lipinski_violations"] = (
        (df["mw"] > 500).astype(int)
        + (df["logp"] > 5).astype(int)
        + (df["hba"] > 10).astype(int)
        + (df["hbd"] > 5).astype(int)
    )
    df["lipinski_compliant"] = (df["lipinski_violations"] == 0).astype(int)

    # Ligand Efficiency
    df["ligand_efficiency"] = df["pic50"] * 1.37 / df["mw"] * 1000

    # Solubility classification
    df["solubility_class"] = pd.cut(
        df["logs"],
        bins=[-float("inf"), -6, -4, -2, float("inf")],
        labels=["Insoluble", "Poorly Soluble", "Moderately Soluble", "Soluble"],
    )

    # Potency classification
    df["potency_class"] = pd.cut(
        df["pic50"],
        bins=[-float("inf"), 7.0, 8.0, float("inf")],
        labels=["Low", "Moderate", "High"],
    )

    # --- Step 6: Flag statistical outliers (IQR method) ---
    for col in ["pic50", "logp", "logs", "mw"]:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        df[f"{col}_outlier"] = ((df[col] < lower) | (df[col] > upper)).astype(int)

    n_outliers = df[[c for c in df.columns if c.endswith("_outlier")]].sum().sum()
    print(f"  Flagged {int(n_outliers)} outlier values across numeric fields")

    # --- Step 7: Add metadata ---
    df["record_id"] = [f"MOL_{i:04d}" for i in range(1, len(df) + 1)]
    df["data_quality"] = "validated"

    print(f"\nCleaned data: {len(df)} records, {len(df.columns)} columns")
    return df


def generate_quality_report(df):
    """Print a data quality summary report."""
    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)
    print(f"Total records:           {len(df)}")
    print(f"Total features:          {len(df.columns)}")
    print(f"Missing values:          {df.isna().sum().sum()}")
    print(f"Lipinski compliant:      {df['lipinski_compliant'].sum()} / {len(df)}")
    print(f"Outliers flagged:        {df[[c for c in df.columns if 'outlier' in c]].sum().sum():.0f}")
    print(f"\nSolubility distribution:")
    print(df["solubility_class"].value_counts().to_string(header=False))
    print(f"\nPotency distribution:")
    print(df["potency_class"].value_counts().to_string(header=False))
    print(f"\nNumeric summary:")
    print(df[["pic50", "logp", "logs", "mw", "tpsa"]].describe().round(3).to_string())


def main():
    print("=" * 60)
    print("STEP 2: Clean, Transform, and Validate Data")
    print("=" * 60)

    # Pull raw data from S3
    s3 = create_s3_client()
    print("Downloading raw data from S3...")
    df = read_csv_from_s3(s3, S3_BUCKET_NAME, "raw/kinase_inhibitors_raw.csv")

    # Clean and transform
    df_clean = clean_and_transform(df)

    # Quality report
    generate_quality_report(df_clean)

    # Upload cleaned data back to S3
    upload_df_to_s3(s3, df_clean, S3_BUCKET_NAME, "cleaned/kinase_inhibitors_cleaned.csv")

    # Also save locally for Snowflake loading
    df_clean.to_csv("data/kinase_inhibitors_cleaned.csv", index=False)
    print("\nStep 2 complete: Cleaned data uploaded to S3 and saved locally.")

if __name__ == "__main__":
    main()

