#!/bin/bash

# I'm an amazing web server runner
#
# Author: Alex Shteinikov

PID_FILE="/PID/web.pid"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -z $1 ] ; then
    FILE="default"
else
    FILE=$1
fi

PROGRAM='python '$DIR'/tweenk.py '$FILE

if [ -f $DIR$PID_FILE ];
then
	echo '	Killing current web server '
	PID="$(cat $DIR$PID_FILE)"
	kill -9 $PID
	rm $DIR$PID_FILE
fi

echo '	Start server...'
echo '	Loading conf: '$FILE

$PROGRAM &

echo $! > $DIR$PID_FILE

echo "	Server is up now! Cya!"
