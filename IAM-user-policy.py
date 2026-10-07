import boto3
from botocore.exceptions import ClientError

iam = boto3.client('iam')

user_name = 'Raju'

policies = [
    'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
    'arn:aws:iam::aws:policy/AmazonS3FullAccess',
]

try:
    iam.create_user(UserName=user_name)
    print(f"Created user: {user_name}")
except ClientError as e:
    code = e.response['Error']['Code']
    if code == 'EntityAlreadyExists':
        print(f"User {user_name} already exists, continuing.")
    else:
        print(f"Could not create user: {code} - {e.response['Error']['Message']}")
        raise SystemExit(1)

for arn in policies:
    try:
        iam.attach_user_policy(UserName=user_name, PolicyArn=arn)
        print(f"Attached: {arn}")
    except ClientError as e:
        print(f"Could not attach {arn}: {e.response['Error']['Message']}")