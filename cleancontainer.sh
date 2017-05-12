#!/bin/bash
docker rmi -f ahusking/docker-flowviewer:latest
docker rmi -f ahusking/docker-flowviewer:0.1
docker rm -f docker-flowviewer
