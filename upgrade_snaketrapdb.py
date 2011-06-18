#!/usr/bin/env python
import psycopg2
import sys
if len(sys.argv) != 6:
	sys.stdout.write("Invalid number of arguments. Usage: %s %s %s %s %s %s\n" % (sys.argv[0], 'database', 'host', 'port', 'user', 'password'))
	sys.exit(2)

conn = psycopg2.connect(database=str(sys.argv[1]), host=str(sys.argv[2]), port=str(sys.argv[3]), user=str(sys.argv[4]), password=str(sys.argv[5]))
cur = conn.cursor()
cur.execute("ALTER TABLE snmptt_def ALTER COLUMN date_added DROP NOT NULL;")

try:
	cur.execute("INSERT INTO snaketrap_info (key, value) VALUES('version', '0.1.2');")
except psycopg2.IntegrityError:
	conn.rollback()
	try:
		cur.execute("UPDATE snaketrap_info SET value='0.1.2' WHERE key='version';")
		conn.commit()
	except:
		sys.stdout.write("Failed to write version information\n")
		sys.exit(1)
except psycopg2.ProgrammingError:
	conn.rollback()
	sys.stdout.write("Failed to write version information\n")
	sys.exit(1)
conn.commit()
cur.close()
conn.close()
