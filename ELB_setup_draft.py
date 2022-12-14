import boto3
from botocore.exceptions import ClientError


ec2_CLIENT = boto3.client('ec2')
elb = boto3.client('elbv2')

# we can move all functions to the launching.py script


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
    return cluster1_arn, cluster2_arn

# lots of hardcoding


def create_load_balancer():
    response = elb.create_load_balancer(
        Name='firstelb',
        Subnets=[
            'subnet-06d153050f47d1d66', 'subnet-0fed2534cd76e2033'
        ],
        SecurityGroups=[
            'sg-05b36275a2a8748e2',
        ],
        Scheme='internet-facing',
        Type='application',
        IpAddressType='ipv4'
    )

# need to pass the intances ids


def connect_instances_to_target():
    cluster1_arn, cluster2_arn = create_target_groups()
    # cluster1 instances ids []
    # cluster2 instances ids []
    cluster1 = elb.register_targets(
        TargetGroupArn=cluster1_arn,
        Targets=[
            {
                'Id': 'i-80c8dd94',
            },
            {
                'Id': 'i-ceddcd4d',
            },
        ],
    )
    cluster2 = elb.register_targets(
        TargetGroupArn=cluster2_arn,
        Targets=[
            {
                'Id': 'i-80c8dd94',
            },
            {
                'Id': 'i-ceddcd4d',
            },
        ],
    )


# use create_listernes() to connect target groups to the load balancer
# can be found in boto3 docs
# remove hard coding, then it should be all set


def setup_listeners():
    listener = elb.create_listener(
        LoadBalancerArn='arn:aws:elasticloadbalancing:us-east-1:985144913653:loadbalancer/app/firstelb/af9c82ac155c40d1',
        Protocol='HTTP',
        Port=80,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:985144913653:targetgroup/cluster1/7830b04465887e0f'}]
    )
    # forwards to cluster1 arn
    rule1 = elb.create_rule(
        ListenerArn=listener["Listeners"][0]["ListenerArn"],
        Conditions=[
            {
                'Field': 'path-pattern',
                'Values': [
                    '/cluster1/*',
                ]}],
        Priority=1,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:985144913653:targetgroup/cluster1/7830b04465887e0f'
            }]
    )
    # forwards to cluster2 to arn
    rule2 = elb.create_rule(
        ListenerArn=listener["Listeners"][0]["ListenerArn"],
        Conditions=[
            {
                'Field': 'path-pattern',
                'Values': [
                    '/cluster2/*',
                ]}],
        Priority=2,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:985144913653:targetgroup/cluster2/2a83080f40af2c2e'
            }]
    )


setup_listeners()
