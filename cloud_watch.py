"""Launch an EC2 instance using an EXISTING key pair, then create a CloudWatch CPU alarm."""
import urllib.request

import boto3
from botocore.exceptions import ClientError

REGION = "ap-south-1"
INSTANCE_TYPE = "t3.micro"
KEY_NAME = "lokesh"             # existing key pair name in AWS (case-sensitive)
SG_NAME = "loki-ssh-sg"
EMAIL = "lokeshpundarika11@gmail.com"
CPU_THRESHOLD = 50.0            # percent

ec2 = boto3.client("ec2", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)


def get_latest_ami():
    param = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
    return ssm.get_parameter(Name=param)["Parameter"]["Value"]


def check_key_pair():
    """The key pair already exists, so just confirm AWS can find it."""
    try:
        ec2.describe_key_pairs(KeyNames=[KEY_NAME])
        print(f"Using existing key pair: {KEY_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidKeyPair.NotFound":
            raise SystemExit(
                f"Key pair '{KEY_NAME}' not found in {REGION}. "
                "Check the name (case-sensitive) and region in EC2 -> Key Pairs."
            )
        raise


def create_security_group():
    my_ip = urllib.request.urlopen("https://checkip.amazonaws.com").read().decode().strip()
    vpc_id = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    try:
        sg_id = ec2.create_security_group(
            GroupName=SG_NAME, Description="SSH from my IP", VpcId=vpc_id
        )["GroupId"]
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": f"{my_ip}/32", "Description": "My IP"}],
            }],
        )
        print(f"Created security group {sg_id} (SSH allowed from {my_ip})")
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidGroup.Duplicate":
            sg_id = ec2.describe_security_groups(GroupNames=[SG_NAME])["SecurityGroups"][0]["GroupId"]
            print(f"Security group '{SG_NAME}' already exists, reusing {sg_id}.")
        else:
            raise
    return sg_id


def launch_instance(ami_id, sg_id):
    resp = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[sg_id],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "boto3-monitored"}],
        }],
    )
    instance_id = resp["Instances"][0]["InstanceId"]
    print(f"Launching {instance_id} ...")
    ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])
    inst = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    print(f"Running. Public IP: {inst.get('PublicIpAddress')}")
    return instance_id


def create_cpu_alarm(instance_id):
    topic_arn = sns.create_topic(Name="ec2-cpu-alerts")["TopicArn"]
    sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=EMAIL)
    print(f"Check {EMAIL} and CONFIRM the SNS subscription, or you won't get alerts.")

    alarm_name = f"high-cpu-{instance_id}"
    cloudwatch.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription=f"CPU above {CPU_THRESHOLD}% on {instance_id}",
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        Statistic="Average",
        Period=300,
        EvaluationPeriods=2,
        Threshold=CPU_THRESHOLD,
        ComparisonOperator="GreaterThanThreshold",
        TreatMissingData="missing",
        AlarmActions=[topic_arn],
        OKActions=[topic_arn],
    )
    print("Created alarm:", alarm_name)
    return alarm_name


def main():
    ami_id = get_latest_ami()
    print("Using AMI:", ami_id)
    check_key_pair()
    sg_id = create_security_group()
    instance_id = launch_instance(ami_id, sg_id)
    alarm_name = create_cpu_alarm(instance_id)

    print("\nSummary")
    print("Instance:", instance_id)
    print("Alarm:   ", alarm_name)
    print(f"Terminate: aws ec2 terminate-instances --instance-ids {instance_id}")
    print(f"Delete alarm: aws cloudwatch delete-alarms --alarm-names {alarm_name}")


if __name__ == "__main__":
    main()