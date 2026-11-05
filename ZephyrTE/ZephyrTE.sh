#!/bin/bash
thisdir=$(dirname "$0")
cd $thisdir

python3 ZephyrTE.py "$@"

cd $HOME
