#!/bin/bash

# Hello, World!
cd ~
git clone https://github.com/gae-init/gae-init.git hello-world
cd hello-world
npm install
# For the back-end
python run.py -s -p 3000
# On another terminal for the front-end
npm start
