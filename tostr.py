#	converts things to strings -- even tuples, lists, and dicts

import types
import string

def tostr(x):
	t = type(x)
	if t == types.DictionaryType:
		return '{' + string.join( \
			map( lambda k,d=x: tostr(k)+": "+tostr(d[k]), \
			x.keys() ), ", " ) + "}"
		

	if t == types.ListType:
		return '[' + string.join( \
			map( lambda i: tostr(i), x), \
			", " ) + "]"

	if t == types.TupleType:
		if len(x) == 1: return '(' + tostr(x[0]) + ",)"
		return '(' + string.join( \
			map( lambda i: tostr(i), x), \
			", " ) + ")"

	return str(x)
