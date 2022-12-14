import boto3
from botocore.exceptions import ClientError
import paramiko
import time
import json
import requests
import threading
import datetime


ec2_RESSOURCE = boto3.resource('ec2', region_name='us-east-1')
ec2_CLIENT = boto3.client('ec2')
elb = boto3.client('elbv2')
cloudwatch = boto3.client('cloudwatch')


# Creates a security group with 3 inbound rules allowing TCP traffic through custom ports
def create_security_group(vpc_id, ports):
    # We will create a security group in the existing VPC
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
            ec2_CLIENT.authorize_security_group_egress(
                GroupId=security_group_id,
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



def create_commands(cluster_number,instance_number):
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
@app.route('/{}')
def myFlaskApp():
    return 'Instance number {} is responding now!'
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80) " | sudo tee app.py '''.format(cluster_number,instance_number),
    # nohup is used to keep the application running
    # the argument is the public IPV4 address of the instance, used to define the server name 
    'sudo nohup env "PATH=$PATH" python3 app.py &']
    return commands

def create_target_groups():
    response = ec2_CLIENT.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    cluster1 = elb.create_target_group(
        Name='cluster1',
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        TargetType='instance',
        IpAddressType='ipv4')
    cluster2 = elb.create_target_group(
        Name='cluster2',
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        TargetType='instance',
        IpAddressType='ipv4')
    cluster1_arn = cluster1["TargetGroups"][0]["TargetGroupArn"]
    cluster2_arn = cluster2["TargetGroups"][0]["TargetGroupArn"]
    print(cluster1, cluster2)
    return cluster1_arn, cluster2_arn

# lots of hardcoding


def create_load_balancer(security_group_id, subnets):
    response = elb.create_load_balancer(
        Name='firstelb',
        Subnets=subnets,
        SecurityGroups=[
            security_group_id,
        ],
        Scheme='internet-facing',
        Type='application',
        IpAddressType='ipv4'
    )
    return response

# need to pass the intances ids

def setup_listeners(elb_arn, cluster_1_arn, cluster_2_arn):
    listener = elb.create_listener(
        LoadBalancerArn=elb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': cluster_1_arn}]
    )
    # forwards to cluster1 arn
    rule1 = elb.create_rule(
        ListenerArn=listener["Listeners"][0]["ListenerArn"],
        Conditions=[
            {"Field": "path-pattern", "PathPatternConfig": {"Values": ["/cluster1"]}}],
        Priority=1,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': cluster_1_arn
            }]
    )
    # forwards to cluster2 to arn
    rule2 = elb.create_rule(
        ListenerArn=listener["Listeners"][0]["ListenerArn"],
        Conditions=[
            {"Field": "path-pattern", "PathPatternConfig": {"Values": ["/cluster2"]}}],
        Priority=2,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': cluster_2_arn
            }]
    )
    return listener, rule1, rule2

def create_elb_target_groups_listeners_rules(security_group_id, vpc_id, target_cluster_1, target_cluster_2):
    subnets = list(ec2_RESSOURCE.subnets.filter(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]},{"Name": "availabilityZone", "Values": ["us-east-1a", "us-east-1b"]}]
    ))
    subnet_ids = [sn.id for sn in subnets]

    elb_created = create_load_balancer(security_group_id, subnet_ids)
    print("ELB : ", elb_created)
    elb_arn = elb_created['LoadBalancers'][0]['LoadBalancerArn']
    cluster_1_arn, cluster_2_arn = create_target_groups()
    listener, rule_1, rule_2 = setup_listeners(elb_arn, cluster_1_arn, cluster_2_arn)
    print(listener, rule_1, rule_2)
    
    cluster_1 = elb.register_targets(
        TargetGroupArn=cluster_1_arn,
        Targets=target_cluster_1,
    )
    cluster_2 = elb.register_targets(
        TargetGroupArn=cluster_2_arn,
        Targets=target_cluster_2,
    )
    return elb_created, cluster_1, cluster_2

def call_endpoint_http(elb_dns,cluster_str):
    url = "http://"+elb_dns+cluster_str
    headers = {'content-type': 'application/json'}
    r = requests.get(url, headers=headers)

def test_1(elb_created):
    for i in range(1000):
        call_endpoint_http(elb_created['LoadBalancers'][0]['DNSName'],"/cluster1")
        call_endpoint_http(elb_created['LoadBalancers'][0]['DNSName'],"/cluster2")

def test_2(elb_created):
    for _ in range(500):
        call_endpoint_http(elb_created['LoadBalancers'][0]['DNSName'],"/cluster1")
        call_endpoint_http(elb_created['LoadBalancers'][0]['DNSName'],"/cluster2")

    time.sleep(60)

    for _ in range(1000):
        call_endpoint_http(elb_created['LoadBalancers'][0]['DNSName'],"/cluster1")
        call_endpoint_http(elb_created['LoadBalancers'][0]['DNSName'],"/cluster2")

def main():
    response = ec2_CLIENT.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    
    # Launches custom security group
    security_group_id = create_security_group(vpc_id, [22, 80, 443])

    # Launches all instances
    Instances_t2=create_instance(1,5,"t2.large","vockey","flask_t2_large_",security_group_id,"us-east-1a")
    Instances_m4=create_instance(6,9,"m4.large","vockey","flask_m4_large_",security_group_id,"us-east-1b")


    t2_IDs = [{'Id':instance.instance_id} for instance in Instances_t2]
    m4_IDs = [{'Id':instance.instance_id} for instance in Instances_m4]

    DNS_addresses_t2=[]
    IP_addresses_t2=[]

    for instance in Instances_t2:
        instance.wait_until_running()
        # Reload the instance attributes
        instance.load()
        DNS_addresses_t2.append(instance.public_dns_name)
        IP_addresses_t2.append(instance.public_ip_address)
        print("DNS = ",instance.public_dns_name)
        print("IPV4 = ",instance.public_ip_address)
        # Enable detailed monitoring
        instance.monitor(
            DryRun=False
        )

    DNS_addresses_m4=[]
    IP_addresses_m4=[]

    for instance in Instances_m4:
        instance.wait_until_running()
        # Reload the instance attributes
        instance.load()
        DNS_addresses_m4.append(instance.public_dns_name)
        IP_addresses_m4.append(instance.public_ip_address)
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
    time.sleep(10)

    for i in range(4):
        print("Connecting to ", DNS_addresses_m4[i])
        c.connect( hostname = DNS_addresses_m4[i], username = "ubuntu", pkey = k )
        print("Connected")
        commands = create_commands("cluster1",i+1)
 
        for command in commands[:-1]:
            print("Executing {}".format( command ))
            stdin , stdout, stderr = c.exec_command(command)
            print(stdout.read())
            print(stderr.read())
        
        # The last command to be executed does not send anything to stdout, so we don't read it not to be stuck
        print("Executing {}".format( commands[-1] ))
        stdin , stdout, stderr = c.exec_command(commands[-1])
        print("Go to http://"+str(IP_addresses_m4[i]))


    for i in range(5):
        print("Connecting to ", DNS_addresses_t2[i])
        c.connect( hostname = DNS_addresses_t2[i], username = "ubuntu", pkey = k )
        print("Connected")
        commands = create_commands("cluster2",5+i)
 
        for command in commands[:-1]:
            print("Executing {}".format( command ))
            stdin , stdout, stderr = c.exec_command(command)
            print(stdout.read())
            print(stderr.read())
        
        # The last command to be executed does not send anything to stdout, so we don't read it not to be stuck
        print("Executing {}".format( commands[-1] ))
        stdin , stdout, stderr = c.exec_command(commands[-1])
        print("Go to http://"+str(IP_addresses_t2[i]))

    '''
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

    
    # Loop through the instances
    for i in range(9):
        print("Connecting to ", DNS_addresses[i])
        c.connect( hostname = DNS_addresses[i], username = "ubuntu", pkey = k )
        print("Connected")
        commands = create_commands("cluster1",i+1)
 
        for command in commands[:-1]:
            print("Executing {}".format( command ))
            stdin , stdout, stderr = c.exec_command(command)
            print(stdout.read())
            print(stderr.read())
        
        # The last command to be executed does not send anything to stdout, so we don't read it not to be stuck
        print("Executing {}".format( commands[-1] ))
        stdin , stdout, stderr = c.exec_command(commands[-1])
        print("Go to http://"+str(IP_addresses[i]))
    '''
    time.sleep(5)
    c.close()

    elb_created, cluster_1, cluster_2 = create_elb_target_groups_listeners_rules(security_group_id, vpc_id, m4_IDs, t2_IDs)
    #print(cluster_1, cluster_2)
    
    print('Launching complete')

    waiter = elb.get_waiter('load_balancer_available')
    print("Waiting for ELB to run")

    waiter.wait(LoadBalancerArns=[elb_created['LoadBalancers'][0]['LoadBalancerArn']])

    print("ELB runs")
    test_scenario_1 = threading.Thread(target=test_1, args=(elb_created,))
    test_scenario_2 = threading.Thread(target=test_2, args=(elb_created,))

    test_scenario_1.start()
    test_scenario_2.start()

    test_scenario_1.join()
    test_scenario_2.join()
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'test',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ApplicationELB',
                        'MetricName': 'RequestCount',
                        'Dimensions': [
                            {
                                    'Name': "LoadBalancer",
                                    'Value': 'firstelb',
                                },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum'
                    },
            },
        ],
        StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
        EndTime=datetime.datetime.utcnow()
    )
    print(response)

main()