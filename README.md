# CloudComputing_TP1

## Docummentation of Progress

### Fri 7 Oct 
**launching.py**
The python script creates nine ec2 instances spread in two availablity zones (us-east-1a, us-east-1b). 

methods:
1. create_key_pair(): 
    - the key-name is hard coded (*flask*) 
    - the key-value is written to a text file named (*temp.txt*)

2. create_security_group():
    - creates the security group used for the ec2 instances, 

3. create_t2_instances(sg_id, keyname):
    - method creates 5 instances of type *t2.large*

4. create_m4_instances(sg_id, keyname):
    -  method creates 4 instances of type *m4.large*

5. launch_all_instances():
    - starts the script and calls the remainder of the metods defined in the script. 

The script start by calling the *launch_all_instances()* method, which calls all the remaining methods. 

OBS: *lines 48-56 in create_security_group* --> not working yet, security group is created but without any inbound rules. 

**terminate.py**
This python script was created inorder to:
1. terminate all running instances 
    - which is important to preserve resources when the instances are not being used. 
2. delete all security groups 
    - which needs to be done so that the name for the security group (*Security Group*) can be reused when the launching.py script is re-ran. 
3. delete key-pair 
    - which needs to be done so that the key_name for the key-pair (*falsk*) can be reused when the script launching.py is re-ran.
4. remove *temp.txt* (the file that holds the key-value) 
    - which is important out of a security perspective. 

**flask_export.sh**
?

**flash_install.sh**
This bash-file was created to enable installation of flask. 

**flask_application**
The purpose of this bash-file is to deploy applications on ec2 instances. 

**.gitignore**
A gitingore-file was created and includes the environment of the project - something that must be configured on each individual machine. This can in part be done with one of the bash-files - *flask_install* - but installation of boto3, aws cli and python is also required. 

