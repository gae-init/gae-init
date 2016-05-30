#!/bin/bash

# Init
mkdir -p ~/temp/gae-init-temp
cd ~/temp/gae-init-temp

# Cloud SDK and App Engine
curl https://sdk.cloud.google.com | bash
gcloud components install app-engine-python

# Node.js
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  sudo apt-get install nodejs
elif [[ "$OSTYPE" == "darwin"* ]]; then
  brew install node
fi

# Gulp.js
sudo npm install -g gulp

# Python related
curl -O https://bootstrap.pypa.io/get-pip.py
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  sudo python get-pip.py
  sudo pip install virtualenv
elif [[ "$OSTYPE" == "darwin"* ]]; then
  python get-pip.py
  pip install virtualenv
fi

# Git
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  sudo apt-get install git
elif [[ "$OSTYPE" == "darwin"* ]]; then
  brew install git
fi

# Clean up
rm -rf ~/temp/gae-init-temp
