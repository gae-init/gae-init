#!/bin/bash

if [[ "$OSTYPE" == "linux-gnu" ]]; then
  source requirements_linux.sh
elif [[ "$OSTYPE" == "darwin"* ]]; then
  source requirements_osx.sh
fi
