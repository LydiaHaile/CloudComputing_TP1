import boto3
from botocore.exceptions import ClientError
temp = open("temp.txt", "w")


ec2 = boto3.resource('ec2')

# Creating a key pair, should be modified to save the key_pair locally


def create_key_pair():
    ec2 = boto3.client('ec2')
    key_value = ec2.create_key_pair(KeyName='flask')
    print('Key pair named ' + key_value['KeyName']+' created')
    temp.write(key_value['KeyMaterial'])
    temp.close()
    return key_value['KeyName']

# Creating 5 t2.large ec2 instances


def create_t2_instances(sg_id, keyname):
    ec2.create_instances(
        ImageId="ami-08c40ec9ead489470",
        MinCount=1,
        MaxCount=5,
        InstanceType="t2.large",
        KeyName=keyname,
        SecurityGroupIds=[sg_id],
        Placement={'AvailabilityZone': 'us-east-1a'})
    print('t2.large instances created')

# Creating 4 m4.large instances


def create_m4_instances(sg_id, keyname):
    ec2.create_instances(
        ImageId="ami-08c40ec9ead489470",
        MinCount=1,
        MaxCount=4,
        InstanceType="m4.large",
        KeyName=keyname,
        SecurityGroupIds=[sg_id],
        Placement={
            'AvailabilityZone': 'us-east-1b'})
    print('m4.large instances created')

# Creates a security group


def create_security_group():
    ec2 = boto3.client('ec2')
    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    try:
        response = ec2.create_security_group(GroupName='Security Group',
                                             Description='None',
                                             VpcId=vpc_id)
        security_group_id = response['GroupId']
        print('Security Group Created %s in vpc %s.' %
              (security_group_id, vpc_id))
        print(security_group_id)
        return security_group_id
    except ClientError as e:
        print(e)

# Launches all instances


def launch_all_instances():
    key_name = create_key_pair()
    security_group_id = create_security_group()
    create_t2_instances(security_group_id, key_name)
    create_m4_instances(security_group_id, key_name)
    print('all done')


launch_all_instances()
