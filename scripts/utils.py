import boto3
import os
from pathlib import Path

# Read bucket from environment, fallback to a previously hard-coded name if needed
S3_BUCKET = os.environ.get("S3_BUCKET") or os.environ.get("BUCKET_NAME") or "business-news-sentiments"
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")

s3 = boto3.client("s3", region_name=AWS_REGION)

def save_to_file(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def upload_to_s3(local_path, s3_key):
    s3.upload_file(local_path, S3_BUCKET, s3_key)
    print(f"Uploaded to s3://{S3_BUCKET}/{s3_key}")
