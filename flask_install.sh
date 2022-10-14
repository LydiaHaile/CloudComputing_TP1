value=$(<dns_adress.txt)
for str in ${value[@]}; do
    ssh -i labsuser.pem ubuntu@$str
done


ssh -i labsuser.pem ubuntu@ec2-3-226-235-167.compute-1.amazonaws.com


sudo apt-get update && sudo apt-get -y install python3-pip && sudo pip3 install flask &&
mkdir flask_application && cd flask_application


pip3 install Flask

