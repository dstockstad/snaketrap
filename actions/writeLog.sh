#!/bin/bash
# LOGDIR is not taken as an argument as a precaution if someone tries to write in files on the system. 
LOGDIR=/var/log/snaketrap
# Make sure this directory is writable for the user running snmptt

if [ -z "$4" ]; then
	echo "usage: $0 <logfile without path> <hostname> <trap name> <trap output>"
	echo "for example: $0 \$r \$r \$N \"\$*\""
	echo "this will create a logfile named after hostname in $LOGDIR"
	exit 2
fi

if [ ! -w $LOGDIR ]; then
	echo "$LOGDIR is not writable or doesn't exist, exiting..."
	exit 2
fi

LOGFILE="$LOGDIR/$1"
HOSTNAME="$2"
TRAPNAME="$3"
OUTPUT="$4"

echo "`date "+%Y-%m-%d %H:%M:%S"` $HOSTNAME $TRAPNAME $OUTPUT" >> "$LOGFILE"
