import boto3
from botocore.exceptions import ClientError
import paramiko
import time


ec2_RESSOURCE = boto3.resource('ec2', region_name='us-east-1')
ec2_CLIENT = boto3.client('ec2')

# Creating 5 t2.large ec2 instances

def create_user_data(instance_number):
    user_data = ['sudo apt-get update', 
    'yes | sudo apt-get install python3-pip',
    'export PATH="/home/ubuntu/.local/bin:$PATH"',
    'sudo pip3 install Flask',
    'mkdir flask_application', 
    'cd flask_application',
#    'python3 -m venv venv',
#    'source venv/bin/activate',
#    'python3 -m pip3 install flask',
#    'instance_ip=$(ec2metadata --public-ipv4)', 
    '''echo "import sys
from flask import Flask
app = Flask(__name__)
@app.route('/')
def myFlaskApp():
    return 'Instance number {} is responding now!'
    
if __name__ == '__main__':
    app.config.update(
        SERVER_NAME=str(sys.argv[1])
    )
    app.run(host='0.0.0.0', port=80) " | sudo tee app.py '''.format(instance_number),
    'sudo nohup env "PATH=$PATH" python3 app.py $(ec2metadata --public-ipv4) &']
#    'export FLASK_APP=flask_app.py',
#    'flask --app flask_app.py run -h \'0.0.0.0\' -p 80']
    print(user_data)
    return user_data

def create_t2_instances(sg_id):
    Instances=[]
    for i in range(1,6):
        Instances+=ec2_RESSOURCE.create_instances(
            ImageId="ami-08c40ec9ead489470",
            InstanceType="t2.large",
            KeyName="vockey",
            MinCount=1,
            MaxCount=1,
            #UserData = u_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value':  'flask_t2_large_'+str(i)
                        },
                    ]
                },
            ],
            SecurityGroupIds=[sg_id],
            Placement={
                'AvailabilityZone': 'us-east-1a'})
    print('t2.large instances created')
    return Instances

# Creating 4 m4.large instances


def create_m4_instances(sg_id):
    Instances=[]
    for i in range(6,10):
        Instances+=ec2_RESSOURCE.create_instances(
            ImageId="ami-08c40ec9ead489470",
            InstanceType="m4.large",
            KeyName="vockey",
            MinCount=1,
            MaxCount=1,
            #UserData = u_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value':  'flask_m4_large_'+str(i)
                        },
                    ]
                },
            ],
            SecurityGroupIds=[sg_id],
            Placement={
                'AvailabilityZone': 'us-east-1b'})
    print('m4.large instances created')
    return Instances

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
        return security_group_id
    except ClientError as e:
        print(e)

# Launches all instances


def launch_all_instances():
    security_group_id = create_security_group()
    Instances_t2=create_t2_instances(security_group_id)
    Instances_m4=create_m4_instances(security_group_id)
    Instances=Instances_t2+Instances_m4
    temp_dns=[]
    temp_ip=[]
    for instance in Instances:
        instance.wait_until_running()
        # Reload the instance attributes
        instance.load()
        temp_dns.append(instance.public_dns_name)
        temp_ip.append(instance.public_ip_address)
        print("DNS = ",instance.public_dns_name)
        print("IPV4 = ",instance.public_ip_address)
        # Enable detailed monitoring
        instance.monitor(
        DryRun=False
        )
    print(temp_dns)
    #ip_address = open("ip_address.txt", "w")
    #ip_address.write(temp_ip[:-1])
    #ip_address.close()
    k = paramiko.RSAKey.from_private_key_file("labsuser.pem")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    time.sleep(5)
    for i in range(9):
        print("connecting to ",temp_dns[i])
        c.connect( hostname = temp_dns[i], username = "ubuntu", pkey = k )
        print("connected")
        commands = create_user_data(i+1)
        for command in commands[:-1]:
            print("Executing {}".format( command ))
            stdin , stdout, stderr = c.exec_command(command)
            #print(stdin.read())
            print(stdout.read())
            print(stderr.read())
        print("Executing {}".format( commands[-1] ))
        stdin , stdout, stderr = c.exec_command(commands[-1])
        print(temp_ip[i])
    c.close()
    print('all done')


launch_all_instances()


