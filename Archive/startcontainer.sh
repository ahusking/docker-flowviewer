#!/bin/bash
# usage:
# ./buildimage.sh <port 80 forwarder>
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
docker run -d --name docker-flowviewer -v $DIR/data:/data/ -v $DIR/config/flow-capture.conf:/etc/flow-tools/flow-capture.conf -v $DIR/config/FlowViewer_Configuration.pm:/usr/lib/cgi-bin/FlowViewer/FlowViewer_Configuration.pm  -p $1:80 ahusking/docker-flowviewer
bash scripts/CreateHostDirs.sh
