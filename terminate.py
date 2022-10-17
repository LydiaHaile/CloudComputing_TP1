import boto3
from botocore.exceptions import ClientError
import time

ec2_RESSOURCE = boto3.resource('ec2')
ec2_CLIENT = boto3.client('ec2')

# Delete all instances
resp = ec2_CLIENT.describe_instances()
# Lists the id of all instances
newlist=[]
for reservation in resp['Reservations']:
    for instance in reservation['Instances']:
        newlist.append(instance['InstanceId'])
try:
    ec2_CLIENT.terminate_instances(InstanceIds=(newlist))
    print("Instances removed")
except ClientError as e:
    print(e)

# Delete security group
try:
    response = ec2_CLIENT.describe_vpcs()
    vpcid = response.get('Vpcs', [{}])[0].get('VpcId', '')

    print('Removing VPC ({}) from AWS'.format(vpcid))
  
    vpc = ec2_RESSOURCE.Vpc(vpcid)
    # delete our endpoints
    for ep in ec2_CLIENT.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        ec2_CLIENT.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
    time.sleep(30)
    security_groups_dict = ec2_CLIENT.describe_security_groups()
    security_groups = security_groups_dict['SecurityGroups']
    L=[]
    for groupobj in security_groups:
        # We don't want to remove the default security group
        if groupobj['GroupName']!='default':
            L.append(groupobj['GroupId'])
    for elm in L:
        response = ec2_CLIENT.delete_security_group(GroupId=elm)
        print('Security Group Deleted', response)
except ClientError as e:
    print(e)