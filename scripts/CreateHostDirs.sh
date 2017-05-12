#!/bin/bash
declare -x devices
echo !!! WARNING THIS WILL REMOVE ANY LINE WITH @DEVICES IN THE CONFIG FILE AND GENERATE A NEW ONE !!!
while IFS= read -r line; do
	
    #local devices="("	
    read HOSTDIR <<< $(echo $line | awk '{split($0,a," "); print a[8]}')
    if ! [ -z "${HOSTDIR}" ]; then
	echo ${HOSTDIR##*/}
	devices="$devices,\"${HOSTDIR##*/}\""
	echo creating .$HOSTDIR
	mkdir -p .$HOSTDIR
	#echo $devices
    fi
done < "config/flow-capture.conf" 

mkdir -p ./data/flows/all_routers
devices="($devices)"
devices=${devices/\(\,/\(}
echo adding following devices to config file: $devices
echo Note: copying from .example, somethings broken and its late 
cat ./config/FlowViewer_Configuration.pm.example | grep -v "@devices" > ./config/FlowViewer_Configuration.pm
echo "@devices = $devices" >> ./config/FlowViewer_Configuration.pm
#@devices                 = ("router_1","router_2","router_3","router_4","router_5","router_6"); # for flow-tools
