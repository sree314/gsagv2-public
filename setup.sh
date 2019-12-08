#!/usr/bin/env bash

mv /autograder/source/ssh/{config,deploy*} ~/.ssh/

ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

apt-get install -y python python-pip python-dev

apt-get install -y python3-yaml

apt-get install -y cbmc z3

chmod +x /autograder/source/scripts/*.py

wget http://mirrors.kernel.org/ubuntu/pool/universe/c/cbmc/cbmc_5.10-5_amd64.deb

dpkg -i cbmc_5.10-5_amd64.deb

if [ -f /autograder/source/assignment/setup_assignment.sh ]; then
	source /autograder/source/assignment/setup_assignment.sh
fi;
