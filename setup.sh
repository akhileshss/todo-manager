#!/bin/bash

[[ $_ != $0 ]] && echo "Setting up the devel environment" || { echo "Please source this script:\n>> source setup.sh"; exit -1; }

source ~/.bash_profile

export DEVEL_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

export DEVEL_VENV="todo-manager"

# Python setup
workon $DEVEL_VENV
cd $DEVEL_ROOT
echo 'DEVEL_ROOT="'$DEVEL_ROOT'"'
export PYTHONPATH=$DEVEL_ROOT:$PYTHONPATH

# Golang setup
gvm use go1.22.3
export GOPATH=$DEVEL_ROOT/go
export PATH=$PATH:$GOPATH/bin

