#!/bin/bash
# usage:
# ./startcontainer <containerID> <port number> (optional -it or other docker flag for debugging)
docker run -d $3 -p $2:80 $1 bash -n docker-flowviewer
