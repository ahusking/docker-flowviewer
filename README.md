docker-flowviewer
=============
Scripts to build FlowViewer (https://sourceforge.net/projects/flowviewer) Docker image and container.
This script is targeted for FlowViewer 4.6
after cloning the repo, simply run one of the following two commands:

prior to running the script to build/start the image you need to create the following config files (you can use the .example files for both as a starter)
config/flow-capture.conf -- configures the flow capture software
config/FlowViewer_Configuration.pm -- configures the FlowViewer web application

Note: FlowCapture is only exposing port 9996 outside the docker container, I need to figure a way to dynamically do this based on the config file.

For a dynamic web port assignment:
./buildimage.sh

To specify the web port:
./buildimage.sh 80



