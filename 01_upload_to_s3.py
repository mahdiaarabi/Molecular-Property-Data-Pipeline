"""
Step 1: Upload Raw Data to AWS S3
=================================
Uploads the raw molecular property dataset to an S3 bucket
for centralized cloud-based data storage.


Author: Mahdi Aarabi, Ph.D.
"""

import boto3
import os
import sys
from config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME
)


def create_s3_client():
    """Initialize AWS S3 client with credentials."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def create_bucket_if_not_exists(s3_client, bucket_name):
    """Create S3 bucket if it doesn't already exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except s3_client.exceptions.ClientError:
        if AWS_REGION == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )
        print(f"Created bucket '{bucket_name}' in {AWS_REGION}.")


def upload_file_to_s3(s3_client, local_path, bucket_name, s3_key):
    """Upload a local file to S3."""
    s3_client.upload_file(local_path, bucket_name, s3_key)
    print(f"Uploaded: {local_path} -> s3://{bucket_name}/{s3_key}")


def list_bucket_contents(s3_client, bucket_name):
    """List all objects in the S3 bucket."""
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        print(f"\nBucket contents ({bucket_name}):")
        for obj in response["Contents"]:
            print(f"  {obj['Key']:50s}  {obj['Size']:>10,} bytes")
    else:
        print("Bucket is empty.")


def main():
    print("=" * 60)
    print("STEP 1: Upload Raw Data to AWS S3")
    print("=" * 60)

    # Initialize S3 client
    s3 = create_s3_client()

    # Create bucket
    create_bucket_if_not_exists(s3, S3_BUCKET_NAME)

    # Upload raw dataset
    data_file = "data/kinase_inhibitors_raw.csv"
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found. Run generate_dataset.py first.")
        sys.exit(1)

    upload_file_to_s3(s3, data_file, S3_BUCKET_NAME, "raw/kinase_inhibitors_raw.csv")

    # Verify upload
    list_bucket_contents(s3, S3_BUCKET_NAME)
    print("\nStep 1 complete: Raw data uploaded to S3.")


if __name__ == "__main__":
    main()
    
