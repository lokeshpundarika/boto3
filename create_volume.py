import boto3

ec2 = boto3.client('ec2', region_name='ap-south-1')

response = ec2.create_volume(
    AvailabilityZone='ap-south-1b',
    Size=20,
    VolumeType='gp3',
    Encrypted=False,
    Iops=3000,  
    
)

volume_id = response['VolumeId']
print("Created volume:", volume_id)