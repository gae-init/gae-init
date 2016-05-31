#!/bin/bash

# Cloud SDK and App Engine
curl https://sdk.cloud.google.com | bash
gcloud components install app-engine-python

# Node.js
sudo apt-get install nodejs

# Gulp.js
sudo npm install -g gulp

# Python related
curl https://bootstrap.pypa.io/get-pip.py | sudo python
sudo pip install virtualenv

# Git
sudo apt-get install git
