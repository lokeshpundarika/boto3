import boto3

client = boto3.client('ec2')

response = client.delete_volume(
    VolumeId='vol-0c131017c28bbe164',
    
)

print(response)