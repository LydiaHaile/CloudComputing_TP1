value=$(<dns_adress.txt)
number=1
for str in ${value[@]}; do
    ssh -i labsuser.pem ubuntu@$str "sudo apt-get update ; sudo apt-get install python3-venv;

    mkdir flask_app;
    cd flask_app;
    python3 -m venv venv;
    source venv/bin/activate;
    pip install Flask ;

    instance_ip=$(ec2metadata --public-ipv4) && echo \"from flask import Flask
    app = Flask(__name__)
    @app.route('/')
    def myFlaskApp():

            return \"Instance number "$number" is responding now!\"

    if __name__ == \"__main__\":
            app.config.update(
                    SERVER_NAME="\"$instance_ip\""
            )
            app.run(host='0.0.0.0', port=80) \" | sudo tee app.py ;

    sudo env "PATH=$PATH" python app.py"
    

    number++
done