#!/bin/bash
# usage:
# ./buildimage.sh <port 80 forwarder>
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo downloading FlowViewer 4.6 source
if ! [ -f FlowViewer_4.6/FV.cgi ]; then
	wget -O FlowViewer_4.6.tar https://sourceforge.net/projects/flowviewer/files/FlowViewer_4.6.tar/download
	echo extracting FlowViewer
	tar xvf FlowViewer_4.6.tar
fi
echo downloading user guide
if ! [ -f FlowViewer_4.6/FlowViewer.pdf ]; then
	wget -O FlowViewer_4.6/FlowViewer.pdf https://sourceforge.net/projects/flowviewer/files/FlowViewer.pdf/download
fi
echo building initial image
docker build -t ahusking/docker-flowviewer:0.1 -t ahusking/docker-flowviewer:latest .
echo starting flowviewer container
docker run -d --name docker-flowviewer -v $DIR/data:/data/ -v $DIR/config/flow-capture.conf:/etc/flow-tools/flow-capture.conf -v $DIR/config/FlowViewer_Configuration.pm:/usr/lib/cgi-bin/FlowViewer/FlowViewer_Configuration.pm  -p $1:80 ahusking/docker-flowviewer
echo creating Host directories/Config
bash scripts/CreateHostDirs.sh
docker ps | grep --color=never 'docker-flowviewer\|CONTAINER ID'
