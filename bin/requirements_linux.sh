#!/bin/bash

# Init
mkdir -p ~/temp/gae-init-temp
cd ~/temp/gae-init-temp

# Cloud SDK and App Engine
curl https://sdk.cloud.google.com | bash
gcloud components install app-engine-python

# Node.js
sudo apt-get install nodejs

# Gulp.js
sudo npm install -g gulp

# Python related
curl -O https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo pip install virtualenv

# Git
sudo apt-get install git

# Clean up
rm -rf ~/temp/gae-init-temp
