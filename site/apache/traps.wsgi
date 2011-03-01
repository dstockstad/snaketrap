import os
import sys

from os.path import abspath, dirname, join
from site import addsitedir

from django.conf import settings

sys.path.append('/usr/share')
sys.path.append('/usr/share/snaketrap')

os.environ["DJANGO_SETTINGS_MODULE"] = "snaketrap.settings"
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
