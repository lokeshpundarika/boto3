import boto3

client = boto3.client('s3', region_name='ap-south-1')

response = client.create_bucket(
    Bucket='boto-bucket-07-10-2026-636603298665',   # lowercase, hyphens only, must be globally unique
    CreateBucketConfiguration={
        'LocationConstraint': 'ap-south-1'
    },
)

print("Created:", response['Location'])