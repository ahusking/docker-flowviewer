#!/bin/bash
# usage:
# ./startcontainer <containerID> <port number> <path to flow-capture.conf> <path to FlowViewer folder>
docker run -d -n docker-flowviewer -v $3:/etc/flow-utils/flow-capture.conf -v $4:/usr/lib/cgi-bin/FlowViewer -p $2:80 $1 
