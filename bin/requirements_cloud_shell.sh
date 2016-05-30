#!/bin/bash

# Init
mkdir -p ~/temp/gae-init-temp
cd ~/temp/gae-init-temp

# Gulp.js
sudo npm install -g gulp

# Python related
curl -O https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo pip install virtualenv

# Clean up
rm -rf ~/temp/gae-init-temp
