"""Upload all .py files from a local folder to an S3 bucket."""
import glob
import os

import boto3
from botocore.exceptions import ClientError

REGION = "ap-south-1"
BUCKET = "boto-bucket-07-10-2026-636603298665"   # your existing bucket name
LOCAL_PATTERN = r"D:\AWS\VS_code_boto3\*.py"     # wildcard pattern of files to upload
S3_PREFIX = "boto3"                           # "folder" inside the bucket

s3 = boto3.client("s3", region_name=REGION)

files = [f for f in glob.glob(LOCAL_PATTERN) if os.path.isfile(f)]
if not files:
    raise SystemExit(f"No files matched: {LOCAL_PATTERN}")

print(f"Found {len(files)} file(s) to upload.")

for path in files:
    key = S3_PREFIX + os.path.basename(path)     # e.g. uploads/create_vpc.py
    try:
        s3.upload_file(path, BUCKET, key)
        size = s3.head_object(Bucket=BUCKET, Key=key)["ContentLength"]
        print(f"Uploaded {path} -> s3://{BUCKET}/{key} ({size} bytes)")
    except ClientError as e:
        print(f"Failed {path}: {e.response['Error']['Code']} - {e.response['Error']['Message']}")