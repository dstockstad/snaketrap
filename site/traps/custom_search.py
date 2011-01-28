from traps.models import *
from traps.error_handling import *
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext
import syslog

# Custom search
class CustomSearch:
	def f_search(self, result_list, search_column, search_type, query):
		# Translate search arguments to sql
		sql_search_type = {
			'like': 'ILIKE',
			'nlike': 'NOT ILIKE',
			'eq': '=',
			'neq': '!=',
			'gt': '>',
			'gte': '>=',
			'lt': '<',
			'lte': '<=',
			'null': 'IS NULL',
			'nnull': 'IS NOT NULL',
		}

		# Check if search arguments are empty
		if search_column != '' and search_type != '' and query != '':
			# Strip beginning , if there is one
			if search_column.startswith("|||"):
				search_column = search_column[3:]
			if search_type.startswith("|||"):
				search_type = search_type[3:]
			if str(query).startswith("|||"):
				query = str(query)[3:]

			s_s_col, s_s_type, s_q = search_column.split("|||"), search_type.split("|||"), query.split("|||")
			syslog.syslog(str(s_s_col))
			syslog.syslog(str(s_s_type))
			syslog.syslog(str(s_q))
			if len(s_s_col) != len(s_s_type) or len(s_s_col) != len(s_q):
				CErr = CustomError()
				CErr.object = 'Argument Error'
				CErr.custom_error_type = 'search_column, search_type and query have different number of elements in them'
				return render_to_response('traps/error.html', {"custom_errors": CErr})
			# Split and loop
			for s_col, s_type, q in map(None, s_s_col, s_s_type, s_q):
				# Add % around query if LIKE or NOT LIKE is specified as an argument
				if s_type == 'like' or s_type == 'nlike':
					query_padding = '%'
				else:
					query_padding = ''

				if s_type != 'null' and s_type != 'nnull':
					result_list = result_list.extra(where=[str(s_col) + ' ' + sql_search_type[str(s_type)] + ' %s'], params=[str(query_padding) + unicode(q) + str(query_padding)])
				else:
					result_list = result_list.extra(where=[str(s_col) + ' ' + sql_search_type[str(s_type)]])

		return(result_list)

