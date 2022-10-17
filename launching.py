import boto3
from botocore.exceptions import ClientError
import paramiko
import time


ec2_RESSOURCE = boto3.resource('ec2', region_name='us-east-1')
ec2_CLIENT = boto3.client('ec2')

# Creates a security group with 3 inbound rules allowing TCP traffic through custom ports
def create_security_group(ports):
    # We will create a security group in the existing VPC
    response = ec2_CLIENT.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    try:
        security_group = ec2_RESSOURCE.create_security_group(GroupName='security_group',
                                             Description='Flask_Security_Group',
                                             VpcId=vpc_id,
                                             )
        security_group_id = security_group.group_id
        for port in ports: # In our use case, ports = [22, 80, 443]
            security_group.authorize_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'FromPort': port,
                    'ToPort': port,
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

def create_instance(id_min,id_max,instance_type,keyname,name,security_id,availability_zone):
    Instances=[]
    for i in range(id_min,id_max+1):
        Instances+=ec2_RESSOURCE.create_instances(
            ImageId="ami-08c40ec9ead489470",
            InstanceType=instance_type,
            KeyName=keyname,
            MinCount=1,
            MaxCount=1,
            # Specify the number of the instances in its Tag Name
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value':  name+str(i)
                        },
                    ]
                },
            ],
            SecurityGroupIds=[security_id],
            Placement={
                'AvailabilityZone': availability_zone})
    print('{} instances created'.format(instance_type))
    return Instances



def create_commands(instance_number):
    ### stores in a list the set of commands needed to deploy Flask on an instance
    commands = ['sudo apt-get update', 
    'yes | sudo apt-get install python3-pip',
    # adds to path the location of the flask module
    'export PATH="/home/ubuntu/.local/bin:$PATH"',
    'sudo pip3 install Flask',
    'mkdir flask_application', 
    'cd flask_application',
    # python script containing the application definition
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
    # nohup is used to keep the application running
    # the argument is the public IPV4 address of the instance, used to define the server name 
    'sudo nohup env "PATH=$PATH" python3 app.py $(ec2metadata --public-ipv4) &']
    return commands


def main():
    # Launches custom security group
    security_group_id = create_security_group([22, 80, 443])

    # Launches all instances
    Instances_t2=create_instance(1,5,"t2.large","vockey","flask_t2_large_",security_group_id,"us-east-1a")
    Instances_m4=create_instance(6,9,"m4.large","vockey","flask_m4_large_",security_group_id,"us-east-1b")

    Instances=Instances_t2+Instances_m4
    DNS_addresses=[]
    IP_addresses=[]
    for instance in Instances:
        instance.wait_until_running()
        # Reload the instance attributes
        instance.load()
        DNS_addresses.append(instance.public_dns_name)
        IP_addresses.append(instance.public_ip_address)
        print("DNS = ",instance.public_dns_name)
        print("IPV4 = ",instance.public_ip_address)
        # Enable detailed monitoring
        instance.monitor(
            DryRun=False
        )

    # Configure SSH connection to AWS
    k = paramiko.RSAKey.from_private_key_file("labsuser.pem")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # wait to make sure connection will be possible
    time.sleep(5)

    # Loop through the instances
    for i in range(9):
        print("Connecting to ", DNS_addresses[i])
        c.connect( hostname = DNS_addresses[i], username = "ubuntu", pkey = k )
        print("Connected")
        commands = create_commands(i+1)
 
        for command in commands[:-1]:
            print("Executing {}".format( command ))
            stdin , stdout, stderr = c.exec_command(command)
            print(stdout.read())
            print(stderr.read())
        
        # The last command to be executed does not send anything to stdout, so we don't read it not to be stuck
        print("Executing {}".format( commands[-1] ))
        stdin , stdout, stderr = c.exec_command(commands[-1])
        print("Go to http://"+str(IP_addresses[i]))

    c.close()
    print('Launching complete')


main()