import boto3
from botocore.exceptions import ClientError
temp = open("temp.txt", "w")


ec2_RESSOURCE = boto3.resource('ec2', region_name='us-east-1')
ec2_CLIENT = boto3.client('ec2')

# Creating 5 t2.large ec2 instances


def create_t2_instances(sg_id, keyname):
    ec2_RESSOURCE.create_instances(
        ImageId="ami-08c40ec9ead489470",
        MinCount=1,
        MaxCount=5,
        InstanceType="t2.large",
        KeyName="vockey",
        SecurityGroupIds=[sg_id],
        Placement={'AvailabilityZone': 'us-east-1a'})
    print('t2.large instances created')

# Creating 4 m4.large instances


def create_m4_instances(sg_id, keyname):
    ec2_RESSOURCE.create_instances(
        ImageId="ami-08c40ec9ead489470",
        MinCount=1,
        MaxCount=4,
        InstanceType="m4.large",
        KeyName="vockey",
        SecurityGroupIds=[sg_id],
        Placement={
            'AvailabilityZone': 'us-east-1b'})
    print('m4.large instances created')

# Creates a security group


def create_security_group():
    response = ec2_CLIENT.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    try:
        security_group = ec2_RESSOURCE.create_security_group(GroupName='security_group',
                                             Description='None',
                                             VpcId=vpc_id,
                                             )
        security_group_id = security_group.group_id
        security_group.authorize_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpProtocol': 'TCP',
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0',
                            'Description': "Flask_authorize"
                        },
                    ]
                }
            ]
        )
        security_group.authorize_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpProtocol': 'TCP',
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0',
                            'Description': "Flask_authorize"
                        },
                    ]
                }
            ]
        )
        security_group.authorize_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpProtocol': 'TCP',
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0',
                            'Description': "Flask_authorize"
                        },
                    ]
                }
            ]
        )
        print('Security Group Created %s in vpc %s.' %
              (security_group_id, vpc_id))
        print(security_group_id)
        return security_group_id
    except ClientError as e:
        print(e)

# Launches all instances


def launch_all_instances():
    security_group_id = create_security_group()
    create_t2_instances(security_group_id)
    create_m4_instances(security_group_id)
    print('all done')


launch_all_instances()
