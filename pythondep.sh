#! /bin/sh
echo "Run script in root directory of the repo"
apt-get update
apt-get -y install python-pip
pip -V
pip install -r requirements.txt
