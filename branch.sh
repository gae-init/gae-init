#!/bin/sh
git fetch upstream
git checkout -b "$1" upstream/master
git push origin "$1"
