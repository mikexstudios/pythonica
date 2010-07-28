"""	Pythonica.py

This module does input and output parsing.  All the real work is done
by PythonicaCore.
"""

import string
import re
import sys
from pythonicacore import *

gEntryNum = 1
gSymToName = {}
gNameToSym = {}
gNameToPrec = {}
gNonchainable = ('ReplaceAll','Rule','Power','Minus','Divide')
# note: instead of just "nonchainable", we should note whether
# each function groups left, groups right, or chains
# (compare -> and /. in Mathematica; right and left, resp.)

#----------------------------------------------------------------------
def buildOperTables():
	global gSymToName, gNameToPrec
	ops = ( '/.',	'ReplaceAll',
			'->',	'Rule',
			'==',	'Equal',
			'=',	'Set',
			'=.',	'Unset',
			'+',	'Plus',
			'-',	'Minus',
			'*',	'Times',
			'/',	'Divide',
			'^',	'Power')
	for i in range(0,len(ops)/2):
		gSymToName[ops[i*2]] = ops[i*2+1]
		gNameToSym[ops[i*2+1]] = ops[i*2]
		gNameToPrec[ops[i*2+1]] = i
buildOperTables()

#----------------------------------------------------------------------
def endOfExpr(s):
	# return the position at which this token ends
	# it may be delimited by a delimiter, or the end of the string
	p = 0
	maxp = len(s)
	while p < maxp:
		# check for non-alphanumeric chars
		if not s[p].isalnum() and s[p] not in ['[','(','.']:
			return p
#		# check for one-char opers
#		if s[p] in (gSymToName.keys() + [',',' ']):
#			#if p>0: return p
#			return p
#		# check for two-char opers
#		if p < maxp-1 and s[p:p+2] in gSymToName.keys():
#			return p

		# check for groupings...
		if s[p] == '[':					# if we start a '[...]',
			# make sure this isn't a slice
			if p > 0 and s[p+1] == '[':
				# it's a slice
				return p
			nest = 1
			while nest:					# ...finish it
				p += 1
				if s[p] == '[': nest += 1
				if s[p] == ']': nest -= 1
			return p + 1
		if s[p] == '(':					# if we start a '(...)',
			if p == 0:					# Make sure we're at the beginning of the string
				nest = 1
				while nest:					# ...finish it
					p = p + 1
					if s[p] == '(': nest = nest + 1
					if s[p] == ')': nest = nest - 1
				return p + 1
			else:
				# We're in the middle of the string. End the token now
				return p
		p += 1
	return p

#----------------------------------------------------------------------
def endOfArg(s):
	# returns the position where this argument ends
	# an argument ends on a comma or end of string, ignoring commas in groups
	p = 0
	maxp = len(s)
	while p < maxp:
		if s[p] == ',':
			return p
		
		if s[p] == '[':
			nest = 1
			while nest:
				p += 1
				if s[p] == '[': nest += 1
				if s[p] == ']': nest -= 1
		if s[p] == '(':
			nest = 1
			while nest:
				p += 1
				if s[p] == '(': nest += 1
				if s[p] == ')': nest -= 1
		p += 1
	return p

#----------------------------------------------------------------------
def splitExprs(s):
	# split on delimiters, ignoring those nested in '[...]' or '(...)'
	outexpr = []
	outdelim = []
	while s:
		end = endOfExpr(s)
		outexpr.append(s[:end])
		if end >= len(s):
			outdelim.append('')
		elif s[end:end+2] in ['[[',']]']:
			outdelim.append(s[end])
		elif s[end:end+2] in gSymToName.keys():
			outdelim.append(s[end:end+2])
		elif s[end] in gSymToName.keys():
			outdelim.append(s[end])
		elif not s[end].isalnum():
			outdelim.append(s[end])
		else:
			outdelim.append('*')
			end -= 1
		s = s[end+len(outdelim[-1]):]
	return outexpr,outdelim

#----------------------------------------------------------------------
def splitArgs(s):
	# split arguments - split on commas, skipping groups
	outexpr = []
	while s:
		end = endOfArg(s)
		outexpr.append(s[:end])
		s = s[end+1:]
	return outexpr
		

#----------------------------------------------------------------------
def subPercent(s):
	"""subPercent(s): replace one '%' with Out[-1],
	'%%' with the Out[-2], etc., and %n (where n is
	an integer) with the Out[n]."""
	while 1:
		l = len(s)
		pos = s.find('%')
		if pos < 0: return s
		cnt = 1
		while pos+cnt < l and s[pos+cnt] in '%0123456789':
			cnt = cnt+1
		substr = s[pos:pos+cnt]
		if len(substr) > 1 and substr[1] != '%':
			rep = 'Out[' + substr[1:] + ']'
		else:
			rep = 'Out[-' + str(len(substr)) + ']'
		s = s[:pos] + rep + s[pos+cnt:]

#----------------------------------------------------------------------
def stripSpaces(s):
	"""stripSpaces(s): strip all spaces from the input string,
	except that if a space occurs between any combination of
	numbers and symbols, convert it to '*'."""
	
	out = ''
	hadsym = 0		# flag: did we just have a symbol or number?
	hadspace = 1	# flag: did we just have some whitespace?
	symchars = string.letters + string.digits
	for c in s:
		if c != ' ':
			if hadspace:
				# we just had a space...
				if c in symchars:
					# and now we see a symbol
					# if we had a symbol before that, throw in a '*'
					if hadsym: out = out + '*'
			hadsym = (c in symchars)
			out = out + c
			hadspace = 0
		else:
			hadspace = 1
	return out

#----------------------------------------------------------------------
def isNumber(s):
	# detect if s is a number - allows negative sign and a single period
	if len(s) == 0:
		return False
	if s[0] == '-': s = s[1:]
	if s.find('.') != s.rfind('.'):
		# too many periods
		return False
	for char in s:
		if char not in "0123456789.":
			return False
	return True

#----------------------------------------------------------------------
def parseOneExpr(s):
	"""parseOneExpr(s): build one token from the string s.
	This string should immediately be a token, and contain no
	paretheses, operators, etc., except within arguments."""
	
	wip = []
	# get first token
	delim = re.search(r'[][, ]', s)
	if not delim:
		delim = -1
		token = s
		delimchar = '\n'
	else:
		delim = delim.span()[0]
		token = s[:delim]
		delimchar = s[delim]
	expr = None
	
	# do we have a FullForm expression (e.g., Head[args])?
	if delimchar == '[':
		# check for a list
		if token == '':
			expr = ExprList()
		else:
			# check for a built-in symbol; otherwise, use ExprSymbol
			try: expr = eval('Expr' + token + '()' )
			except: expr = Expr([],token)
		# ...find all the elements for this expression
		estr = s[:endOfExpr(s)+1]
		estr = estr[delim+1:-1]
		estrlist = splitArgs(estr)
#		print "args:", estrlist
		expr.setData(map(parse, estrlist))

	# if not, then do we have a number?
#	elif token[0] in '0123456789' or (len(token)>1 and \
#		 token[0] == '-' and token[1] in '0123456789'):
#		# a Number...
#		expr = ExprNumber(float(token))
	elif isNumber(token):
		# A number...
		expr = ExprNumber(float(token))
	
	# if not, do we have a complex number?
	elif token[-1] == 'j' and (len(token) == 1 or isNumber(token[:-1])):
		# A complex number...
		if len(token) == 1:
			expr = ExprComplex((0,1))
		else:
			expr = ExprComplex((0,float(token[:-1])))

	# if neither of those, then it must be a symbol
	else:
		# a Symbol...
		# Symbols can't start with numbers, tho
		if token[0].isdigit() or (token[0] == '-' and token[1].isdigit()):
			raise "Symbol::parse", "Symbols can't start with a digit."
		expr = ExprSymbol(token)
	return expr

#----------------------------------------------------------------------
def parse(s):
	global gSymToName, gNameToPrec, gNonchainable
	# split into tokens...
	estrlist,delimlist = splitExprs(s)
	# crawl through tokens, combining where operators are found
	wip = []			# stack of expressions
#	print "estrlist:", estrlist
#	print "delimlist:", delimlist
	
	# evaluate each token, considering its following delimiter
	for i in range(0,len(estrlist)):
		if estrlist[i]:
			if estrlist[i][0] == '(':
				# if we have parentheses, parse their contents!
				expr = parse(estrlist[i][1:-1])
			else:
				# otherwise, load a single expression
				expr = parseOneExpr(estrlist[i])
		else: expr = None

		if delimlist[i] in gSymToName.keys():
			# we have an operator...
			opername = gSymToName[delimlist[i]]
			try:
				operclass = eval('Expr' + opername)
			except:
				raise "Bug", "Undefined operator " + opername

			if not wip:
				# first expression we've seen; throw it on the stack
				wip.append(operclass(expr))

			elif not wip[-1].Head():
				# current expression is headless -- make it us
				wip[-1].head = opername
				if expr: wip[-1].data.append(expr)

			elif wip[-1].Head() == opername and opername not in gNonchainable:
				# same operator; append to previous data
				wip[-1].data.append(expr)

			else:
				# figure out where to stuff token,
				# according to precedence rules
				myPrecedence = gNameToPrec[opername]
				curPrecedence = gNameToPrec[wip[-1].Head()]
				if curPrecedence < myPrecedence:
					# current head has lower precedence... start a new level
#					print opername, "higher than", wip[-1].Head()
					wip.append(operclass(expr))
					wip[-2].data.append(wip[-1])
				else:
					# current head has higher precedence...
					# add expr to current, then move it within us
#					print opername, "lower than", wip[-1].Head()
					if expr: wip[-1].data.append(expr)
					which = len(wip)-2
					while which >= 0:
						if gNameToPrec[ wip[which].Head() ] >= myPrecedence:
#							print "...lower than", wip[which].Head()
							pass
						else:
#							print "...but not lower than", wip[which].Head()
							break
						which -= 1
					which += 1 # we want to wrap around one level higher
#					print "Stuffing around wip", which
					if wip[which].Head() != opername or opername in gNonchainable:
						if which == 0:
							wip[0] = operclass(wip[0])
							del wip[1:]
						else:
							wip[which-1].data[-1] = operclass(wip[which-1].data[-1])
							wip[which] = wip[which-1].data[-1]
					else:
						# get rid of wip entries above which
						del wip[which+1:]
		elif delimlist[i] == '[':
			# we have a slice
			expr = ExprSlice(expr)
			if wip:
				wip[-1].data.append(expr)
			wip.append(expr)
		elif delimlist[i] == ']':
			# end of slice
			args = parse(estrlist[i])
			if args.Head() != 'List': # this should never happen
				raise 'parse::syntax', "Syntax error after token '%s'." % estrlist[i]
			wip[-1].data.append(args.data)
		elif delimlist[i] == '':
			if not wip:
				wip.append(expr)
			else:
				wip[-1].data.append(expr)
		else:
			raise "parse::operators", "Undefined operator '%s'." % delimlist[i]
#		print "wip:", tostr(wip)
	if len(wip) >= 1:
		return wip[0]
	else:
		return None

#----------------------------------------------------------------------
def unparse(expr, leftprec=-1, rightprec=-1):
	# is this expression something we have an operator for?
	head = expr.Head()
	if head not in gNameToPrec.keys():
		# nope, no operator... just print normally
		out = str(expr)
		return out
	# yep, we have an operator... get it, and its precedence
	prec = gNameToPrec[head]
	# (for readability, we'll code a couple of formatting hacks)
	op = gNameToSym[head]
	if op == '*': op = ' '
	elif op != '^': op = ' ' + op + ' '
	# combine data using operator -- pass precedence info
	out = ''
	# leftmost argument gets has our left, and us for the right
	if len(expr.data) > 0:
		if len(expr.data) == 1: r = rightprec
		else: r = prec
		out = unparse(expr.data[0],leftprec,r)
	# middle arguments have us on both left and right
	if len(expr.data) > 2:
		out = out + op + \
		  op.join(map(lambda x,p=prec:unparse(x,p,p),expr.data[1:-1]))
	# last argument has our right, and us for the left
	if len(expr.data) > 1:
		out = out + op + \
				unparse(expr.data[-1],prec,rightprec)
	# use parenthesis if we're lower precedence than our neighbors
	if prec < leftprec or prec < rightprec:
		out = '(' + out + ')'
	return out

#----------------------------------------------------------------------
def handleInput(s, surpressOutput=0):
	"""handleInput(s, surpressOutput=0): handle the given input,
	generating output if the second parameter is 0.  Return a
	tuple of (input-expr, output-expr)."""
	
	s = stripSpaces(subPercent(s))
	if s:
		inexp = parse(s)
		if inexp != None:
			eval = inexp.Eval()
			if surpressOutput:
				simp = eval.Simplify()
				while simp != eval:
					eval = simp
					simp = eval.Simplify()
			else:
				print
				print "in FullForm:", inexp
				print "evaluates to:", eval
				# now simplify
				simp = eval.Simplify()
				while simp != eval:
					print "simplifies to:", simp
					eval = simp
					simp = eval.Simplify()
			return inexp,simp
	return None,None

#----------------------------------------------------------------------
def mainLoop():
	global gEntryNum
	s = 'foo'
	while s:
		inexp = None
		outexp = None
		try:
			numstr = '[' + str(gEntryNum) + ']'
			s = raw_input("In" + numstr + " :=   ")
			# break on ';' and surpress output for all but the last
			commands = s.split(";")
			for c in commands[:-1]:
				inexp,outexp = handleInput(c,1)
			# on the last one, don't surpress output
			if commands[-1]:
				inexp,outexp = handleInput(commands[-1])
				if outexp:
					print
					print "Out" + numstr, "=  ", unparse(outexp)
		except EOFError:
			raise
		except:
			# only display the message and keep going if this is the main module
			info = sys.exc_info()
			if __name__ == '__main__':
				if not isinstance(info[0], types.ClassType):
					print "%s: %s" % info[:2]
				else:
					print "Syntax Error"
			else:
				raise
		print
		
		# Turn the inexp/outexp into a None expression if they're None
		if inexp == None:
			inexp = Expr()
		if outexp == None:
			outexp = Expr()
		# store the in/out data for future reference
		StoreInOut( inexp,outexp )
		gEntryNum = gEntryNum + 1

#----------------------------------------------------------------------

if __name__ == '__main__':
	try:
		mainLoop()
		raw_input("Press Return.")
	except EOFError:
		print "" # print a newline
