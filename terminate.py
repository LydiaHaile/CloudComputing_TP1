import boto3
import os
from botocore.exceptions import ClientError

# Create EC2 client
ec2 = boto3.client('ec2')

resp =ec2.describe_instances()
newlist=[]
for reservation in resp['Reservations']:
 for instance in reservation['Instances']:
         newlist.append(instance['InstanceId'])
print(ec2.terminate_instances(InstanceIds=(newlist)))


# Delete security group
try:
    security_groups_dict = ec2.describe_security_groups()
    security_groups = security_groups_dict['SecurityGroups']
    L=[]
    for groupobj in security_groups:
        if groupobj['GroupName']!='default':
            L.append(groupobj['GroupId'])
    for elm in L:
        response = ec2.delete_security_group(GroupId=elm)
        print('Security Group Deleted', response)
except ClientError as e:
    print(e)

ec2 = boto3.client('ec2')


response = ec2.delete_key_pair(KeyName='flask')
print(response)

try:
    os.remove("temp.txt")
except OSError:
    pass
