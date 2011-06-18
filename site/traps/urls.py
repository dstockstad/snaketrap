"""
This file is part of SnakeTrap.

SnakeTrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SnakeTrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SnakeTrap.  If not, see <http://www.gnu.org/licenses/>.
"""

from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Piston
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from traps.api import SnaketrapApi

auth = HttpBasicAuthentication(realm="SnakeTrap")
ad = { 'authentication': auth }

api_resource = Resource(handler=SnaketrapApi, **ad)

urlpatterns = patterns('',
    (r'^$', 'traps.views.trap_listing'),
    (r'^api/(?P<requested_info>.*)/(?P<search_column>.*)/(?P<search_type>.*)/(?P<query>.*)/$', api_resource),
    (r'^api/(?P<requested_info>.*)/$', api_resource),
    (r'^api/$', api_resource), 
    (r'^traps/$', 'traps.views.trap_listing'),
    (r'^remove_traps/$', 'traps.views.trap_remove'),
    (r'^remove_unknown_traps/$', 'traps.views.unknown_trap_remove'),
    (r'^unknown_traps/$', 'traps.views.unknown_trap_listing'),
    (r'^snmptt_def/$', 'traps.views.snmptt_def_listing'),
    (r'^snmptt_def_commit/$', 'traps.views.snmptt_def_commit'),
    (r'^snmptt_def_mass_change$', 'traps.views.snmptt_def_mass_change'),
    (r'^snmptt_def_mass_change_commit$', 'traps.views.snmptt_def_mass_change_commit'),
    (r'^snmptt_def_propagate$', 'traps.views.snmptt_def_propagate'),
    (r'^snmptt_def_propagate_commit$', 'traps.views.snmptt_def_propagate_commit'),
    (r'^mibs/$', 'traps.views.mib_listing'),
    (r'^mibs/upload$', 'traps.views.upload_file'),
    (r'^about/$', 'traps.views.about'),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DOC_ROOT, 'show_indexes': True}),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', 'traps.views.logout_view'),
    (r'^admin/', admin.site.urls),
)
