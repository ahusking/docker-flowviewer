#!/bin/bash
# usage:
# ./startcontainer <containerID> <port number> <path to flow-capture.conf>
docker run -d -n docker-flowviewer -v $3:/etc/flow-utils/flow-capture.conf -p $2:80 $1 
