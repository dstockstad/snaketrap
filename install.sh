#!/bin/bash
. install.cfg

if [ "$UID" != 0 ]; then
	echo "You must be root to run this installation script"
	exit 1
fi

echo "PLEASE MAKE SURE YOU HAVE CREATED A DATABASE AND A USER TO ACCESS IT BEFORE RUNNING THIS SCRIPT!"
echo "ALSO MAKE SURE YOU HAVE ALL REQUIREMENTS LISTED IN README!"
echo "Press Enter to continue"
read key

if [ -z $site_dir ] || [ -z $action_dir ] || [ -z $mib_dir ] || [ -z $tmp_dir ] || [ -z $apache_user ] || [ -z $apache_group ] || [ -z $snaketrap_apache_conf ]; then
	site_dir=/usr/share/snaketrap
	action_dir=/var/snaketrap/actions
	mib_dir=/var/snaketrap/mibs
	tmp_dir=/var/snaketrap/tmp
	apache_user=apache
	apache_group=apache
	snaketrap_apache_conf=/etc/httpd/conf.d/snaketrap.conf
	net_snmp_mib_dir=/usr/share/snmp/mibs
	snmpttconvertmib=/usr/sbin/snmpttconvertmib
	output_snmptt_def=/etc/snmp/snmptt_def.conf

	echo "Failed to parse install.cfg. Will use the following default settings:\n"
	echo "site_dir = $site_dir"
	echo "action_dir = $action_dir"
	echo "mib_dir = $mib_dir"
	echo "tmp_dir = $tmp_dir"
	echo "apache_user = $apache_user"
	echo "apache_group = $apache_group"
	echo "snaketrap_apache_conf = $snaketrap_apache_conf"
	echo "net_snmp_mib_dir = $net_snmp_mib_dir"
	echo "snmpttconvertmib = $snmpttconvertmib"
	echo "output_snmptt_def = $output_snmptt_def"
	echo "Edit install.cfg to change defaults."
else
	echo "Successfully parsed install.cfg. Will use the following settings:"
	echo "site_dir = $site_dir"
	echo "action_dir = $action_dir"
	echo "mib_dir = $mib_dir"
	echo "tmp_dir = $tmp_dir"
	echo "apache_user = $apache_user"
	echo "apache_group = $apache_group"
	echo "snaketrap_apache_conf = $snaketrap_apache_conf"
	echo "net_snmp_mib_dir = $net_snmp_mib_dir"
	echo "snmpttconvertmib = $snmpttconvertmib"
	echo "output_snmptt_def = $output_snmptt_def"
	echo "Edit install.cfg to change defaults."
fi		

if [ ! -x "$snmpttconvertmib" ]; then
	echo "$snmpttconvertmib doesn't exist or is not executable"
	exit 1
fi

# Run some tests to get python version and check if Django and psycopg2 is installed
./tests.py
if [ "$?" -ne 0 ]; then
	echo "You have failed to meet the requirements, exiting..."
	exit 1
fi

printf "Do you want to perform an installation with these settings? [y/N] "
read input
if [ "e$input" != "ey" ]; then
	echo "Exiting..."
	exit 1
fi

DATE=`date +"%Y-%m-%d_%H%M%S"`

if [ -d $site_dir ]; then
	echo "[ site_dir ] $site_dir exists, moving to `dirname $site_dir`/`basename $site_dir`_$DATE"
	mv $site_dir `dirname $site_dir`/`basename $site_dir`_$DATE
fi

if [ -d $action_dir ]; then
	echo "[ action_dir ] $action_dir exists, moving to `dirname $action_dir`/`basename $action_dir`_$DATE"
	mv $action_dir `dirname $action_dir`/`basename $action_dir`_$DATE
fi

if [ -d $mib_dir ]; then
	echo "[ mib_dir ] $mib_dir exists, moving to `dirname $mib_dir`/`basename $mib_dir`_$DATE"
	mv $mib_dir `dirname $mib_dir`/`basename $mib_dir`_$DATE
fi

if [ -d $tmp_dir ]; then
	echo "[ tmp_dir ] $tmp_dir exists, moving to `dirname $tmp_dir`/`basename $tmp_dir`_$DATE"
	mv $tmp_dir `dirname $tmp_dir`/`basename $tmp_dir`_$DATE
fi

mkdir -p $mib_dir
mkdir -p $tmp_dir
mkdir -p $site_dir
mkdir -p $action_dir
cp -rp site/* $site_dir
cp -rp actions/* $action_dir

chown $apache_user:$apache_group $action_dir $mib_dir $tmp_dir
chmod 755 $action_dir $action_dir/* $mib_dir $tmp_dir

while [ "e$django_admin" == "e" ]; do
	printf "Enter the name of the admin (Example: John Doe): "
	read django_admin
done

while [ "e$django_admin_email" == "e" ]; do
	printf "Enter the email of the admin (Example: john.doe@mail.example.com): "
	read django_admin_email
done

printf "Enter the hostname of your database (press enter for default [localhost]: "
read db_hostname

if [ "e$db_hostname" == "e" ]; then
	db_hostname=localhost
fi

printf "Enter your database name (press enter for default [snaketrap]): "
read db_dbname

if [ "e$db_dbname" == "e" ]; then
	db_dbname=snaketrap
fi

while [ "e$db_user" == "e" ]; do
	printf "Enter your database username: "
	read db_user
done

while [ "e$db_pass" == "e" ]; do
	printf "Enter your database password (will not echo): "
	read -s db_pass
	printf "\n"
done

printf "Enter the url prefix for the site, or press enter for the default [/snaketrap] "
read url_prefix
if [ "e$url_prefix" == "e" ]; then
	url_prefix=/snaketrap
fi
wsgi_url_prefix=$url_prefix
if [ "$url_prefix" == "/" ]; then
	url_prefix=""
	wsgi_url_prefix=/
fi

cp -pf conf/settings_pre.py conf/settings.py

cat <<- EOF >> conf/settings.py
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '$url_prefix/media/'

LOGIN_REDIRECT_URL = '$url_prefix/traps'
LOGIN_URL = '$url_prefix/accounts/login'
ROOT_URLCONF = '`basename $site_dir`.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '$site_dir/templates/',
)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
STATIC_DOC_ROOT = '$site_dir/site_media/'
MEDIA_URL ='$url_prefix/site_media'

SNAKETRAP = {
	'action_dir': '$action_dir',
	'temp_dir': '$tmp_dir',
	'snmp_mib_dir': '$mib_dir',
	'snmpttconvertmib': '$snmpttconvertmib',
	'output_snmptt_def': '$output_snmptt_def',
}

ADMINS = (
    ('$django_admin', '$django_admin_email'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '$db_dbname',                      # Or path to database file if using sqlite3.
        'USER': '$db_user',                      # Not used with sqlite3.
        'PASSWORD': '$db_pass',                  # Not used with sqlite3.
        'HOST': '$db_hostname',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

URL_PREFIX = '$url_prefix'
EOF

cat <<- EOF > conf/traps.wsgi
import os
import sys

from os.path import abspath, dirname, join
from site import addsitedir

from django.conf import settings

sys.path.append('`dirname $site_dir`')
sys.path.append('$site_dir')

os.environ["DJANGO_SETTINGS_MODULE"] = "`basename $site_dir`.settings"
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
EOF

cat <<- EOF > conf/snaketrap.conf
LoadModule wsgi_module modules/mod_wsgi.so

Alias $url_prefix/site_media/ $site_dir/site_media/
Alias $url_prefix/media $site_dir/admin_media/

<Directory $site_dir/site_media>
Order deny,allow
Allow from all
</Directory>

WSGIScriptAlias $wsgi_url_prefix $site_dir/apache/traps.wsgi
WSGIPassAuthorization On

<Directory $site_dir/apache>
Order deny,allow
Allow from all
</Directory>

<Directory $site_dir/admin_media/>
Order deny,allow
Allow from all
</Directory>
EOF


cat <<- EOF > conf/urls.py
from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    # Example:
    (r'^', include('`basename $site_dir`.traps.urls')),
)
EOF

cat <<- EOF > conf/install.post.py
#!/usr/bin/env python
import os
import sys
os.environ["DJANGO_SETTINGS_MODULE"] = "`basename $site_dir`.settings"

from os.path import abspath, dirname, join
from site import addsitedir

from django.conf import settings

sys.path.append('`dirname $site_dir`')
sys.path.append('$site_dir')

from traps.models import Action

a = Action(action_name='Send Trap to Nagios', commandline='sendTrapToNagios.py \$ARG1\$ \$ARG2\$ \$ARG3\$ \$ARG4\$', help='\$r \$N 2 "\$-*"')
a.save()
a = Action(action_name='Mail User', commandline='mail.sh \$ARG1\$ \$ARG2\$ \$ARG3\$ \$ARG4\$', help='\$r \$N "\$-*" someone@mail.example.com')
a.save()
EOF

if [ ! -f "$output_snmptt_def" ]; then
	echo "$output_snmptt_def doesn't exist, will create one"
	touch "$output_snmptt_def"
	chown $apache_user:$apache_group "$output_snmptt_def"
fi

printf "Wrote settings. It is recommended to install settings unless you have old settings you want to use.\n"
printf "Do you want to install settings? [Y/n] "
read input

if [ "e$input" == "ey" ] || [ "e$input" == "e" ]; then
	mv -f conf/settings.py `dirname $site_dir`/`basename $site_dir`/settings.py
	mv -f conf/urls.py `dirname $site_dir`/`basename $site_dir`/urls.py
	mv -f conf/traps.wsgi `dirname $site_dir`/`basename $site_dir`/apache/traps.wsgi
	if [ ! -d `dirname $snaketrap_apache_conf` ]; then
		mkdir -p `dirname $snaketrap_apache_conf`
	fi
	if [ -f $snaketrap_apache_conf ]; then
		echo "[ snaketrap_apache_conf ] $snaketrap_apache_conf already exists, backing up to "$snaketrap_apache_conf"_`date +"%Y-%m-%d_%H%M%S"`."
		mv $snaketrap_apache_conf "$snaketrap_apache_conf"_`date +"%Y-%m-%d_%H%M%S"`
	fi
	mv -f conf/snaketrap.conf $snaketrap_apache_conf
else
	printf "You need to edit/create the following files:\n$site_dir/urls.py\n$site_dir/settings.py\n$snaketrap_apache_conf\n"
	printf "Then you need to do:\ncd $site_dir\npython manage.py syncdb\n"
	echo "Installation Complete!!!"
	exit 0
fi
printf "Installed settings. It is recommended to install the database unless you already have a database.\n"
printf "Do you want to install the database? [y/N] "
read input

if [ "e$input" != "ey" ]; then
	echo "Not creating a database"
	echo "Installation Complete! Don't forget to create a database if you don't already have one."
	exit 0
fi

mv -f conf/install.post.py `dirname $site_dir`/`basename $site_dir`/install.post.py

echo "Trying to create database tables."
cd $site_dir
python manage.py syncdb
if [ "$?" -ne 0 ]; then
	echo "Something went wrong when creating database tables, results where logged to $site_dir/install.log."
	echo "Installation completed with errors"
	exit 1
fi

printf "Created database tables. Do you want to add the included scripts to the database so that you may use them? [Y/n] "
read input
if [ "e$input" == "e" ] || [ "e$input" == "ey" ]; then
	python ./install.post.py
	if [ "$?" -ne 0 ]; then
		echo "Something went wrong when adding the scripts. You may need to add them manually."
	fi
fi

printf "Do you want to copy mibs from $net_snmp_mib_dir to $mib_dir? [Y/n] "
read input
if [ "e$input" == "e" ] || [ "e$input" == "ey" ]; then
	cp -p "$net_snmp_mib_dir"/* "$mib_dir"
fi
echo "Installation Completed!!!"
echo "Now restart apache and point your browser to http://`hostname`$url_prefix to start using this kick-ass system ;)"
