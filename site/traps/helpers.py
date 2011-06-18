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

import datetime
import time
import os

from traps.error_handling import *

# Helper functions for views
def deleteFiles(filelist, directory):
	output = []
	for file in filelist:
		os.remove(str(directory) + '/' + str(file))

def check_dirs(dirs, request):
	CErr = CustomError()
	for dir in dirs:
		if os.path.isdir(dir) == False:
			CErr.object = 'Directory Error'
			CErr.custom_error_type = dir + " doesn't exist"
			return CErr
	return(None)

def list_dates(start_year=2011, start_month=1, start_day=1, last_year=2011, last_month=2, last_day=26):
	date_list = []

	begin_year = datetime.date(start_year, start_month, start_day)
	end_year = datetime.date(last_year, last_month, last_day)
	one_day = datetime.timedelta(days=1)

	next_day = begin_year
	if start_year == last_year:
		last_year = last_year + 1

	for year in range(start_year, last_year):
		for day in range(0, 366):  # includes potential leap year
			if next_day > end_year:
				break
			date_list.append("".join(next_day.isoformat().split("-")))
			next_day += one_day

	return(date_list)

