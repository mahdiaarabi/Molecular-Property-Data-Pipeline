"""
Step 4: Statistical Analysis and Visualization
===============================================
Connects to Snowflake, runs analytical SQL queries, and
generates publication-quality visualizations and reports.

Author: Mahdi Aarabi, Ph.D.
"""

import snowflake.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["figure.dpi"] = 120
matplotlib.rcParams["font.size"] = 11

import os
from config import (
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
    SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_WAREHOUSE,
)

os.makedirs("figures", exist_ok=True)


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


def query_to_df(cursor, sql):
    """Execute SQL query and return results as a DataFrame."""
    cursor.execute(sql)
    columns = [desc[0].lower() for desc in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def plot_target_summary(df):
    """Bar chart of average potency by kinase target."""
    df_sorted = df.sort_values("avg_pic50", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df_sorted["target"], df_sorted["avg_pic50"],
                   color="#2563EB", alpha=0.85, edgecolor="white")
    ax.set_xlabel("Average pIC50")
    ax.set_title("Average Binding Potency by Kinase Target")
    ax.grid(True, axis="x", alpha=0.3)

    for bar, val in zip(bars, df_sorted["avg_pic50"]):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig("figures/target_potency_summary.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved: figures/target_potency_summary.png")


def plot_property_scatter(df):
    """Scatter plot: logP vs pIC50, colored by Lipinski compliance."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # logP vs pIC50
    colors = ["#059669" if x == 1 else "#DC2626" for x in df["lipinski_compliant"]]
    axes[0].scatter(df["logp"], df["pic50"], c=colors, alpha=0.7, s=80, edgecolors="white")
    axes[0].set_xlabel("logP (Lipophilicity)")
    axes[0].set_ylabel("pIC50 (Potency)")
    axes[0].set_title("Lipophilicity vs Potency")
    axes[0].axvline(x=5, color="#DC2626", linestyle="--", alpha=0.5, label="Lipinski logP cutoff")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # MW vs pIC50
    axes[1].scatter(df["mw"], df["pic50"], c=colors, alpha=0.7, s=80, edgecolors="white")
    axes[1].set_xlabel("Molecular Weight (Da)")
    axes[1].set_ylabel("pIC50 (Potency)")
    axes[1].set_title("Molecular Weight vs Potency")
    axes[1].axvline(x=500, color="#DC2626", linestyle="--", alpha=0.5, label="Lipinski MW cutoff")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.suptitle("Property Space Analysis (Green = Lipinski Compliant, Red = Violation)",
                 fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig("figures/property_scatter.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved: figures/property_scatter.png")


def plot_solubility_analysis(df):
    """Bar chart of compound counts by solubility class."""
    sol_counts = df["solubility_class"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#DC2626", "#D97706", "#2563EB", "#059669"]
    bars = ax.bar(sol_counts.index, sol_counts.values, color=colors[:len(sol_counts)],
                  alpha=0.85, edgecolor="white")
    ax.set_xlabel("Solubility Class")
    ax.set_ylabel("Number of Compounds")
    ax.set_title("Compound Distribution by Solubility Classification")
    ax.grid(True, axis="y", alpha=0.3)

    for bar, val in zip(bars, sol_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
                str(val), ha="center", fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.savefig("figures/solubility_distribution.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved: figures/solubility_distribution.png")


def main():
    print("=" * 60)
    print("STEP 4: Statistical Analysis and Visualization")
    print("=" * 60)

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"USE DATABASE {SNOWFLAKE_DATABASE}")
        cursor.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")

        # Query 1: Target summary
        print("\n--- Target Summary ---")
        df_summary = query_to_df(cursor, "SELECT * FROM compound_summary ORDER BY avg_pic50 DESC")
        print(df_summary.to_string(index=False))
        plot_target_summary(df_summary)

        # Query 2: Full compound data for scatter plots
        df_all = query_to_df(cursor, "SELECT * FROM compounds WHERE data_quality = 'validated'")
        plot_property_scatter(df_all)
        plot_solubility_analysis(df_all)

        # Query 3: Top candidates
        print("\n--- Top Drug-Like Candidates (Lipinski + High Potency) ---")
        df_top = query_to_df(cursor, """
            SELECT name, target, pic50, logp, logs, mw, solubility_class
            FROM compounds
            WHERE lipinski_compliant = 1 AND pic50 > 8.0
            ORDER BY pic50 DESC
        """)
        print(df_top.to_string(index=False))

        # Query 4: Quality metrics
        print("\n--- Data Quality Metrics ---")
        df_quality = query_to_df(cursor, """
            SELECT 'Total Compounds' AS metric, CAST(COUNT(*) AS VARCHAR) AS value FROM compounds
            UNION ALL
            SELECT 'Lipinski Compliant', CAST(SUM(lipinski_compliant) AS VARCHAR) FROM compounds
            UNION ALL
            SELECT 'High Potency (>8.0)', CAST(SUM(CASE WHEN pic50 > 8.0 THEN 1 ELSE 0 END) AS VARCHAR) FROM compounds
            UNION ALL
            SELECT 'Unique Targets', CAST(COUNT(DISTINCT target) AS VARCHAR) FROM compounds
        """)
        print(df_quality.to_string(index=False))

        print("\nStep 4 complete: Analysis and visualizations generated.")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
