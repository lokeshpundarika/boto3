"""Create a VPC with one public subnet and one private subnet, attach IGW."""
import boto3

REGION = "ap-south-1"
VPC_CIDR = "10.0.0.0/16"
PUBLIC_CIDR = "10.0.1.0/24"
PRIVATE_CIDR = "10.0.2.0/24"
PUBLIC_AZ = "ap-south-1a"
PRIVATE_AZ = "ap-south-1a"   # can use ap-south-1b for a different AZ

ec2 = boto3.client("ec2", region_name=REGION)


def tag(resource_id, name):
    ec2.create_tags(Resources=[resource_id], Tags=[{"Key": "Name", "Value": name}])


# 1. VPC
vpc_id = ec2.create_vpc(CidrBlock=VPC_CIDR)["Vpc"]["VpcId"]
ec2.get_waiter("vpc_available").wait(VpcIds=[vpc_id])
ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})
tag(vpc_id, "boto3-vpc")
print("VPC:", vpc_id)

# 2. Public subnet (instances get a public IP automatically)
public_subnet_id = ec2.create_subnet(
    VpcId=vpc_id, CidrBlock=PUBLIC_CIDR, AvailabilityZone=PUBLIC_AZ
)["Subnet"]["SubnetId"]
ec2.modify_subnet_attribute(SubnetId=public_subnet_id, MapPublicIpOnLaunch={"Value": True})
tag(public_subnet_id, "boto3-public-subnet")
print("Public Subnet:", public_subnet_id)

# 3. Private subnet (no public IPs)
private_subnet_id = ec2.create_subnet(
    VpcId=vpc_id, CidrBlock=PRIVATE_CIDR, AvailabilityZone=PRIVATE_AZ
)["Subnet"]["SubnetId"]
tag(private_subnet_id, "boto3-private-subnet")
print("Private Subnet:", private_subnet_id)

# 4. Internet gateway, attached to the VPC
igw_id = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
tag(igw_id, "boto3-igw")
print("Internet Gateway:", igw_id)

# 5. Public route table: 0.0.0.0/0 -> internet gateway
public_rt_id = ec2.create_route_table(VpcId=vpc_id)["RouteTable"]["RouteTableId"]
ec2.create_route(RouteTableId=public_rt_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
ec2.associate_route_table(RouteTableId=public_rt_id, SubnetId=public_subnet_id)
tag(public_rt_id, "boto3-public-rt")
print("Public Route Table:", public_rt_id)

# 6. Private route table: local traffic only (no route to the internet)
private_rt_id = ec2.create_route_table(VpcId=vpc_id)["RouteTable"]["RouteTableId"]
ec2.associate_route_table(RouteTableId=private_rt_id, SubnetId=private_subnet_id)
tag(private_rt_id, "boto3-private-rt")
print("Private Route Table:", private_rt_id)

print("\nDone. Save these IDs for cleanup:")
print(f"VPC={vpc_id}")
print(f"PUBLIC_SUBNET={public_subnet_id} PRIVATE_SUBNET={private_subnet_id}")
print(f"IGW={igw_id} PUBLIC_RT={public_rt_id} PRIVATE_RT={private_rt_id}")