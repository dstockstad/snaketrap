#!/usr/bin/env python
import sys
try:
	import django
except:
	print("You don't have django installed.")
	sys.exit(1)

try:
	import psycopg2
except:
	print("You don't have psycopg2 installed. This install script assumes you will use postgresql and needs psycopg2 installed")
	sys.exit(1)
