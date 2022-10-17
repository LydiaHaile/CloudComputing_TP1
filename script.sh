#!/bin/bash

pip3 install aws
pip3 install boto3
pip3 install paramiko

cat creds.txt > ~/.aws/credentials
chmod 400 labsuser.pem

python3 launching.py