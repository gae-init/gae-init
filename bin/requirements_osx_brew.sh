#!/bin/bash

# Init
mkdir -p ~/temp/gae-init-temp
cd ~/temp/gae-init-temp

# Cloud SDK and App Engine
curl https://sdk.cloud.google.com | bash
gcloud components install app-engine-python

# Node.js
brew install node

# Gulp.js
npm install -g gulp

# Python related
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install virtualenv

# Git
brew install git

# Clean up
rm -rf ~/temp/gae-init-temp
