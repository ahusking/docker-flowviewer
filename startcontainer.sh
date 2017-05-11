#!/bin/bash
# usage:
# ./startcontainer <containerID> <port number> <path to flow-capture.conf> <path to FlowViewer folder>
docker run -d -ti --name docker-flowviewer -v config/flow-capture.conf:/etc/flow-utils/flow-capture.conf -v config/FlowViewer_Configuration.pm:/usr/lib/cgi-bin/FlowViewer/FlowViewer_Configuration.pm -v $4:/usr/lib/cgi-bin/FlowViewer -p $2:80 $1  bash
