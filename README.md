# CloudComputing_TP1

## Docummentation of Progress

### Fri 7 Oct

COPY AWS CLI into creds.txt
Download labsuser.pem and put it in working directory
chmod +x script.sh
./script.sh

**launching.py**
The python script creates 9 ec2 instances spread in two availablity zones (us-east-1a, us-east-1b).

methods:

1. create_security_group(ports):

   - creates the security group used for the ec2 instances, allowing TPC traffic through ports (in our use case, ports = [22, 80, 443]),

2. create_instances(id_min,id_max,instance_type,keyname,name,security_id,availability_zone):

   - method creates id_max+1 - id_min instances of type instance_type

3. launch_all_instances():
   - starts the script and calls the remainder of the metods defined in the script.

The script start by calling the _launch_all_instances()_ method, which calls all the remaining methods.

**terminate.py**
This python script was created inorder to:

1. terminate all running instances
   - which is important to preserve resources when the instances are not being used.
2. delete our VPC endpoint
3. delete all security groups
   - which needs to be done so that the name for the security group (_Security Group_) can be reused when the launching.py script is re-ran.

**.gitignore**
A gitingore-file was created and includes the environment of the project - something that must be configured on each individual machine. This can in part be done with one of the bash-files - _flask_install_ - but installation of boto3, aws cli and python is also required.
