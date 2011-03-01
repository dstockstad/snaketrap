from traps.models import *
from traps.error_handling import *
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext
import syslog

# Custom search
class CustomSearch:
	def f_search(self, result_list, args):
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
		if args.search_column != '' and args.search_type != '':
			# Strip beginning , if there is one
			if args.search_column.startswith("|||"):
				args.search_column = args.search_column[3:]
			if args.search_type.startswith("|||"):
				args.search_type = args.search_type[3:]
			if str(args.query).startswith("|||"):
				args.query = str(args.query)[3:]
			s_s_col, s_s_type, s_q = args.search_column.split("|||"), args.search_type.split("|||"), args.query.split("|||")
			if len(s_s_col) != len(s_s_type):
				syslog.syslog("BLEH")
				CErr = CustomError()
				CErr.object = 'Argument Error'
				CErr.custom_error_type = 'search_column, search_type and query have different number of elements in them'
				return render_to_response('traps/error.html', {"custom_errors": CErr})
			# Split and loop
			i = 0
			for s_col, s_type, q in map(None, s_s_col, s_s_type, s_q):
				if s_type == 'null' or s_type == 'nnull':
					if s_q[i] == '' or s_q[i] == "na":
						s_q[i] = "na"
					else:
						s_q.insert(i, "na")
				i = i + 1

			syslog.syslog(str(s_s_col))
			syslog.syslog(str(s_s_type))
			syslog.syslog(str(s_q))

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

			args.search_column = "|||".join(s_s_col)
			args.search_type = "|||".join(s_s_type)
			args.query = "|||".join(s_q)
		return(result_list)

