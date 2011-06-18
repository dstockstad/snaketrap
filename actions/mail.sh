#!/bin/bash
# Author: Dag Stockstad
#
# Make sure you've configured the system mail before using this script
#
# Path to mail executable
MAIL=/bin/mail

if [ -z "$4" ]; then
	echo "usage: $0 <hostname> <trap name> <trap output> <email>"
	echo "for example: $0 \$r \$N \"\$*\" someone@mail.example.com"
	exit 2
fi

HOSTNAME="$1"
TRAPNAME="$2"
OUTPUT="$3"
EMAIL="$4"

echo -e "Hostname: $HOSTNAME\nTrap Name: $TRAPNAME\nTrap Output: $OUTPUT" | mail -s "[ SnakeTrap ] $TRAPNAME was received from $HOSTNAME" "$EMAIL"
