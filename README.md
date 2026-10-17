# Molecular Property Data Pipeline

**End-to-end cloud data pipeline for molecular property analysis using AWS S3, Snowflake, Python, and SQL**

[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20EC2-orange)]()
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8)]()
[![SQL](https://img.shields.io/badge/SQL-Advanced-green)]()


## Overview

A production-style data pipeline that demonstrates end-to-end data engineering for pharmaceutical molecular property analysis. The pipeline ingests raw molecular data, stores it in **AWS S3**, applies Python-based cleaning and transformation routines, loads the processed data into **Snowflake**, and runs **SQL** analytical queries to generate statistical reports and visualizations.

### Pipeline Architecture

```
Raw CSV Data
     │
     ▼
┌─────────────────┐
│   AWS S3         │  ← Step 1: Upload raw data to cloud storage
│   (Data Lake)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Python ETL     │  ← Step 2: Clean, transform, validate
│   (Pandas/NumPy) │     - Remove duplicates
│                  │     - Handle missing values
│                  │     - Compute drug-likeness flags
│                  │     - Flag statistical outliers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Snowflake      │  ← Step 3: Load into data warehouse
│   (Data Warehouse)│    - Relational schema design
│                  │     - Views for analytics
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQL Analysis + │  ← Step 4: Query, analyze, visualize
│   Python Viz     │     - Window functions
│   (Matplotlib)   │     - Aggregations
│                  │     - Statistical reports
└─────────────────┘
```

## Key Features

### Data Engineering
- **AWS S3** integration for cloud-based raw and processed data storage
- **ETL pipeline** with data cleaning, transformation, validation, and outlier detection
- **Snowflake** data warehouse with relational schema, views, and optimized queries

### SQL Analytics
- Complex queries with **JOINs, window functions, CTEs**, and aggregations
- Automated **outlier detection** using IQR method
- Cross-target property comparisons with **RANK()** and **PARTITION BY**
- Data quality metrics and reporting

### Python Statistical Analysis
- Statistical modeling with **Pandas, NumPy, SciPy**
- Lipinski Rule of Five compliance analysis
- Ligand efficiency calculations
- Publication-quality visualizations (**Matplotlib**)

## Repository Structure

```
Molecular-Property-Pipeline/
├── 01_upload_to_s3.py              # Upload raw data to AWS S3
├── 02_clean_transform.py           # ETL: clean, transform, validate
├── 03_load_snowflake.py            # Load into Snowflake warehouse
├── 04_analyze_visualize.py         # SQL analysis + visualizations
├── config_template.py              # Configuration template (copy to config.py)
├── requirements.txt                # Python dependencies
├── .gitignore                      # Excludes config.py and credentials
├── data/
│   └── kinase_inhibitors_raw.csv   # Raw molecular property dataset
├── sql/
│   └── analysis_queries.sql        # Standalone SQL analysis queries
├── figures/                        # Generated visualizations
│   ├── target_potency_summary.png
│   ├── property_scatter.png
│   └── solubility_distribution.png
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.8+
- AWS account (S3, EC2)
- Snowflake account

### Setup

```bash
# Clone repository
git clone https://github.com/mahdiaarabi/Molecular-Property-Pipeline.git
cd Molecular-Property-Pipeline

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config_template.py config.py
# Edit config.py with your AWS and Snowflake credentials
```

### Run the Pipeline

```bash
# Step 1: Upload raw data to S3
python 01_upload_to_s3.py

# Step 2: Clean and transform data
python 02_clean_transform.py

# Step 3: Load into Snowflake
python 03_load_snowflake.py

# Step 4: Analyze and visualize
python 04_analyze_visualize.py
```

## Dataset

30 FDA-approved kinase inhibitors spanning 8 kinase target classes (EGFR, JAK2, BCR-ABL, VEGFR, ALK, BRAF, MEK, CDK4/6) with experimentally derived properties:

| Property | Description | Range |
|----------|-------------|-------|
| pIC50 | Binding potency (-log IC50) | 6.95 – 8.92 |
| logP | Lipophilicity | 1.08 – 5.42 |
| logS | Aqueous solubility | -6.15 – -2.55 |
| MW | Molecular weight (Da) | 306 – 615 |
| TPSA | Topological polar surface area | 59 – 135 |

## Technologies

| Component | Technology |
|-----------|-----------|
| Cloud Storage | AWS S3 |
| Compute | AWS EC2 |
| Data Warehouse | Snowflake |
| ETL / Analysis | Python (Pandas, NumPy, boto3) |
| Database | SQL (DDL, DML, window functions) |
| Visualization | Matplotlib |
| Version Control | Git |


## Author

**Mahdi Aarabi, Ph.D.**  
Computational Scientist 

