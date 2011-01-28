#!/usr/bin/env python
import sys
version = "".join(sys.version.split(" ")[0].split("."))
if int(version) < 240:
	print("You have an invalid python version. You need at least 2.4.0")
	sys.exit(1)

try:
	import django
except:
	print("You don't have django installed. You need at least 1.2.X")
	sys.exit(1)

try:
	import psycopg2
except:
	print("You don't have psycopg2 installed. This install script assumes you will use postgresql and needs psycopg2 installed")
	sys.exit(1)
