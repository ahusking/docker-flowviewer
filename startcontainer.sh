#!/bin/bash
# usage:
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# ./startcontainer <containerID> <port number> <path to flow-capture.conf> <path to FlowViewer folder>
docker run -d -ti --name docker-flowviewer -v $DIR/data:/data/ -v $DIR/config/flow-capture.conf:/etc/flow-tools/flow-capture.conf -v $DIR/config/FlowViewer_Configuration.pm:/usr/lib/cgi-bin/FlowViewer/FlowViewer_Configuration.pm  -p $2:80 $1  bash
