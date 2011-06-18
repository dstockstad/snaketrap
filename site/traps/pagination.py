from django.core.paginator import Paginator, InvalidPage, EmptyPage
def f_paginator(request, qset, args):
	# Split up query into pages
	paginator = Paginator(qset, int(args.pagesize))

	# If page request is out of range, deliver last page of results.
	try:
		qset = paginator.page(args.page)
	except (EmptyPage, InvalidPage):
		qset = paginator.page(paginator.num_pages)
	return qset

def piston_paginator(qset, args):
	if args.pagesize == 0:
		return qset
	if args.page < 1:
		args.page = 1

	if args.page == 1:
		list = qset[0:args.pagesize]
	elif args.page * args.pagesize > qset.count() and (args.page * args.pagesize) - args.pagesize < qset.count():
		list = qset[(args.page * args.pagesize) - args.pagesize:]
	else:
		list = qset[(args.page * args.pagesize) - args.pagesize:args.page * args.pagesize]
	return list
