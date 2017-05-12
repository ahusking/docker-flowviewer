#!/bin/bash
while IFS='' read -r line || [[ -n "$line" ]]; do

    read HOSTDIR <<< $(echo $line | awk '{split($0,a," "); print a[8]}')
    if ! [ -z "${HOSTDIR}" ]; then
	echo creating $HOSTDIR
	mkdir -p $HOSTDIR
    fi
done < "../config/flow-capture.conf"
mkdir -p ../data/flows/all_routers
