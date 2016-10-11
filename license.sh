#!/bin/bash
cd ~/ocrplate
export PAYLOAD_FILE=./openstack.json
python3 s3_python.py
