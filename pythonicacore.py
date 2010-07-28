#	PythonicaCore.py
#

import math
import random
from types import *
from tostr import *

gSymTable = {}
gInList = []
gOutList = []


def DataEval(data):
	# return an evaluated copy of the data
	return map(lambda d:d.Eval(), data)

def StoreInOut( indata, outdata ):
	global gInList, gOutList
	gInList.append(indata)
	gOutList.append(outdata)

#----------------------------------------------------------------------
#----------------------------------------------------------------------
class Expr:
	def __init__(self,data=None,head=None):
		if head: self.head = head
		self.setData(data)
		
	def __str__(self):
		return str(self.Head()) + '[' + \
			string.join(map(str,self.data), ',') + ']'
	
	def Head(self):
		try: return self.head
		except: return None
	
	def Name(self):
		try: return ExprSymbol(self.Head())
		except: return ExprSymbol(None)
	
	def __cmp__(self,other):
		if isinstance(other, Expr) and self.Head() == other.Head() and self.data == other.data:
			return 0
		else: return 1
		
	def Eval(self):
		return self
	
	def Simplify(self):
		return self
	
	def __repr__(self):
		return "<%s '%s'>" % (str(self.__class__), str(self))
	
	def setData(self, data):
		t = type(data)
		if not data: self.data = []
		elif t == TupleType: self.data = list(data)
		elif t == ListType: self.data = data
		else: self.data = [data]
		for i in range(len(self.data)):
			d = self.data[i]
			if type(d) == IntType or type(d) == FloatType or type(d) == ComplexType:
				self.data[i] = ExprNumber(d)
			elif not isinstance(d, Expr):
				raise "Expr::data", "Invalid data passed to Expr()!"

#----------------------------------------------------------------------
def ExprNumber(data=0):
	if type(data) == IntType or type(data) == FloatType:
		return ExprReal(data)
	elif type(data) == ComplexType:
		return ExprComplex(data)
	else:
		raise "ExprNumber::argx", "Invalid data passed to ExprNumber()"

#----------------------------------------------------------------------
class ExprReal(Expr):
	def __init__(self,data=0):
		self.setData(data)
		
	def __str__(self):
		if type(self.data) == IntType: return str(int(self.data))
		return str(self.data)
	
	def __int__(self):
		return int(self.data)
	
	def __float__(self):
		return float(self.data)

	def Head(self):
		return 'Real'
	
	def Name(self):
		if type(self.data) == IntType or int(data) == data:
			return ExprSymbol('Integer')
		else:
			return ExprSymbol('Real')
	
	def Eval(self):
		return self
	
	def setData(self,data):
		t = type(data)
		if not data: self.data = 0
		elif t == TupleType or t == ListType:
			if len(data) > 1:
				raise "Real::argx", "Real called with %i arguments; 0 or 1 arguments are expected." % len(data)
			elif len(data) == 1:
				if int(data) == data:
					self.data = int(data[0])
				else:
					self.data = float(data[0])
			else:
				self.data = 0
		elif t == FloatType and int(data) != data:
			self.data = float(data)
		else:
			self.data = int(data)

#----------------------------------------------------------------------
class ExprComplex(Expr):
	def __init__(self,data=None):
		self.setData(data)
	
	def __str__(self):
		return str(self.data)
	
	def __float__(self):
		return abs(self.data)
	
	def Head(self):
		return 'Complex'
	
	def Eval(self):
		return self
	
	def setData(self,data):
		t = type(data)
		if not data: self.data = complex(0,0)
		elif t == TupleType or t == ListType:
			if len(data) > 2:
				raise "Complex::argx", "Complex called with %i arguments; 0, 1 or 2 arguments are expected." % len(data)
			elif len(data) == 2:
				self.data = complex(data[0],data[1])
			elif len(data) == 1:
				self.data = complex(data[0])
			else:
				self.data = complex(0)
		else:
			self.data = complex(data)

#----------------------------------------------------------------------
class ExprSymbol(Expr):
	def __init__(self,data=''):
		self.setData(data)
		
	def __str__(self):	
		return str(self.data)
	
	def Head(self):
		return 'Symbol'

	def Eval(self):
		global gSymTable
		if self.data in gSymTable.keys():
			# warning: this could cause recursion!
#			print self.data, "defined as", str(gSymTable[self.data]),
			out = gSymTable[self.data].Eval()
#			print "-->", repr(out)
			return out
		return self
	
	def setData(self,data):
		self.data = data

# global predefined symbols
# lowercase is the symbol, uppercase is the built-in True/False
true = ExprSymbol('True')
false = ExprSymbol('False')

#----------------------------------------------------------------------
class ExprList(Expr):
	def Head(self):
		return 'List'
	
	def __str__(self):
		return '[' + string.join(map(str,self.data), ',') + ']'
	
	def Eval(self):
		data = DataEval(self.data)
		return ExprList(data)

#----------------------------------------------------------------------
class ExprSlice(Expr):
	def Head(self):
		return 'Slice'
	
	def __str__(self):
		return str(self.data[0]) + '[[' + string.join(map(str,self.data[1]), ',') + ']]'
	
	def Eval(self):
		if len(self.data) != 2:
			raise 'Slice::argx', 'Slice expects 2 or more arguments, %i arguments given.' % len(self.data)
		if type(self.data[1]) != ListType and type(self.data[1]) != TupleType:
			raise 'Slice::syntax', 'Syntax error in Slice definition.'
		if len(self.data[1]) == 0:
			raise 'Slice::argx', 'Slice expects 2 or more arguments, %i arguments given.' % (len(self.data[1]) + 1)
		expr = self.data[0].Eval()
		args = DataEval(self.data[1])
		for arg in args:
			if arg.Head() != 'Real' or int(arg.data) != arg.data:
				raise 'Slice::argt', 'Slice argument is not an integer.'
			if arg.data == 0:
				expr = expr.Name()
			elif (type(expr.data) != ListType and type(expr.data) != TupleType) or \
					abs(arg.data) > len(expr.data):
				raise 'Splice::depth', 'Slice argument %i is longer than the depth of the expression.' % arg.data
			else:
				if arg.data > 0:
					expr = expr.data[arg.data-1]
				else:
					expr = expr.data[arg.data]
		return expr
	
	def setData(self, data):
		t = type(data)
		if not data: self.data = []
		elif t == TupleType: self.data = list(data)
		elif t == ListType: self.data = data
		else: self.data = [data]
		for i in range(len(self.data)):
			d = self.data[i]
			if type(d) == IntType or type(d) == FloatType or type(d) == ComplexType:
				self.data[i] = ExprNumber(d)
			elif not isinstance(d, (Expr, list)):
				raise "Expr::data", "Invalid data passed to Expr()!"

#----------------------------------------------------------------------
class ExprRule(Expr):
	def Head(self):
		return 'Rule'

#----------------------------------------------------------------------
class ExprReplaceAll(Expr):
	def Head(self):
		return 'ReplaceAll'

	def Eval(self):
		global gSymTable
		if len(self.data) != 2:
			raise "ReplaceAll::argx", "ReplaceAll called with %i arguments; 2 arguments are expected." % len(data)
		# to do the substitution, temporarily replace
		# the given symbol with the given value
		if self.data[1].__class__ != ExprRule:
			raise "ReplaceAll::argx", "Replace all called with %s; ExprRule expected." % dadta[1].__class__
		symname = self.data[1].data[0].data
		if symname in gSymTable.keys(): oldval = gSymTable[symname]
		else: oldval = None
		gSymTable[symname] = self.data[1].data[1]
		out = self.data[0].Eval()
		if oldval: gSymTable[symname] = oldval
		else: del gSymTable[symname]
		return out

#----------------------------------------------------------------------
class ExprPlus(Expr):

	def Head(self):	return 'Plus'
	
	def Eval(self):
		data = DataEval(self.data)
		num = 0
		extras = []
		for d in data:
			if d.Head() == 'Real' or d.Head() == 'Complex':
				num += d.data
			else:
				extras.append(d)
		if extras:
			# we partially reduced it...
			if num and type(num) == IntType or type(num) == FloatType or \
					type(num) == ComplexType: extras.append(ExprNumber(num))
			elif len(extras) == 1:
				return extras[0].Eval()
			return ExprPlus(extras)
		else:
			# we completely reduced this to a Number
			return ExprNumber(num)

	def Simplify(self):
		# if any of our operands are the same, use a Times
		coeff = map(lambda x:1, self.data)
		data = []
		data[:] = self.data
		# convert expressions of the form '3x'
		for i in range(0,len(self.data)):
			data[i] = data[i].Simplify()
			if data[i].__class__ == ExprTimes and isinstance(data[i].data[0], ExprReal):
				coeff[i] = data[i].data[0].data
				if len(data[i].data) == 2:
					data[i] = data[i].data[1]
				else:
					data[i] = ExprTimes(data[i].data[1:])
		# now, combine terms additively
		for i in range(0,len(data)):
			if coeff[i]:
				for j in range(i+1,len(data)):
					if data[i] == data[j]:
						coeff[i] = coeff[i]+coeff[j]
						coeff[j] = 0
		# now we have coefficients, make the new list
		repl = []
		for i in range(0,len(coeff)):
			if coeff[i] == 1:
				repl.append( data[i] )
			elif coeff[i]:
				repl.append( ExprTimes([ExprNumber(coeff[i]),data[i]]) )
		if len(repl) == 1:
			return repl[0]
		elif len(repl) == 0: return ExprNumber(0)
		else:
			return ExprPlus(repl)
		
#----------------------------------------------------------------------
class ExprTimes(Expr):

	def Head(self): return 'Times'
	
	def Eval(self):
		data = DataEval(self.data)
		num = 1
		extras = []
		for d in data:
			if d.Head() == 'Real' or d.Head() == 'Complex':
				num = num * d.data
			else:
				extras.append(d)
		if extras and num != 0:
			# we partially reduced it...
			if num != 1: extras = [ExprNumber(num)] + extras
			elif len(extras) == 1:
				return extras[1].Eval()
			return ExprTimes(extras)
		else:
			# we completely reduced this to a Number
			return ExprNumber(num)

	def Simplify(self):
		data = []
		data[:] = self.data
		
		# first, try flattening -- if an argument is a Times,
		# absorb its arguments into our own
		for i in range(0,len(data)):
			if data[i].Head() == 'Times':
				data[i:i+1] = data[i].data
		
		
		# if any of our operands are the same, use a Power
		# build a list of terms, each stored as [coeff, base, power]
		terms = map(lambda x:[1,x.Simplify(),1], data)
		coeff = 1
		for i in range(0,len(terms)):
			# if it's a ExprNumber, collect separately
			if isinstance(terms[i][1], ExprReal):
				coeff = coeff * terms[i][1].data
				terms[i][0] = 0
			# if it's a ExprTimes, grab the coefficient
			if terms[i][1].__class__ == ExprTimes and \
					isinstance(terms[i][1].data[0], ExprReal):
				terms[i][0] = terms[i][1].data[0].data
				if len(terms[i][1].data) == 2:
					terms[i][1] = terms[i][1].data[1]
				else:
					terms[i][1] = ExprTimes(terms[i][1].data[1:])
			# if it's an ExprPower, grab the power
			if terms[i][1].__class__ == ExprPower and \
					isinstance(terms[i][1].data[1], ExprReal):
				terms[i][2] = terms[i][1].data[1].data
				terms[i][1] = terms[i][1].data[0]
		# now, combine terms additively
		for i in range(0,len(terms)):
			if terms[i][0]:
				for j in range(i+1,len(terms)):
					if terms[i][1] == terms[j][1]:
						terms[i][0] = terms[i][0] * terms[j][0]
						terms[i][2] = terms[i][2] + terms[j][2]
						terms[j][0] = 0
		# now we have powers, make the new list
		repl = []
		for i in range(0,len(terms)):
			if terms[i][2] != 0:
				if terms[i][2] != 1:
					e = ExprPower( [terms[i][1], ExprNumber(terms[i][2])] )
				else: e = terms[i][1]
				if terms[i][0] == 1:
					repl.append( e )
				elif terms[i][0]:
					repl.append( ExprTimes([ExprNumber(terms[i][0]),e]) )
		# put the global coefficient on the front
		if coeff != 1:
			repl = [ExprNumber(coeff)] + repl
		if len(repl) == 1:
			return repl[0]
		elif not repl: return ExprNumber(1)
		return ExprTimes(repl)

#----------------------------------------------------------------------
class ExprMinus(Expr):
	# NOTE: this differs from Mathematica's Minus[] function,
	# which takes only one argument and returns its negative.
	# This takes one or two arguments, which makes parsing
	# much easier.

	def Head(self): return 'Minus'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) < 2:
			if data[0].Head() != 'Real' and data[0].Head() != 'Complex':
				return ExprTimes( [ExprNumber(-1),self.data[0]] )
			return ExprNumber( -self.data[0].data )
		elif len(data) == 2:
			if data[1].Head() == 'Real' or data[1].Head() == 'Complex':
				e = ExprNumber( -self.data[1].data )
			else: e = ExprTimes( [ExprNumber(-1),self.data[1]] )
			e2 = ExprPlus( [self.data[0],e] )
			return e2.Eval()
		else:
			raise "Minus::argx", "Minus called with %i arguments; 1 or 2 arguments are expected." % len(data)
		
#----------------------------------------------------------------------
class ExprDivide(Expr):

	def Head(self): return 'Divide'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 2:
			raise "Divide::argx", "Divide called with %i arguments; 2 arguments are expected." % len(data)
		if isinstance(data[0], (ExprReal, ExprComplex)) and \
				isinstance(data[1], (ExprReal, ExprComplex)):
			if isinstance(data[0], ExprReal):
				data[0].setData(float(data[0]))
			elif isinstance(data[1], ExprReal):
				data[1].setData(float(data[1]))
			return ExprNumber(data[0].data / data[1].data)
		else: return ExprDivide(data)

	def Simplify(self):
		# replace Divide with Power, where possible
		if self.data[1].Head() == 'Real':
			return ExprTimes( [ExprNumber(1.0/self.data[1].data),self.data[0]])
		e = ExprPower( [self.data[1],ExprNumber(-1)] )
		if self.data[0].Head() == 'Real' and self.data[0].data == 1:
			return e
		return ExprTimes( [self.data[0],e] )
		
#----------------------------------------------------------------------
class ExprSet(Expr):

	def Head(self): return 'Set'

	def Eval(self):
		global gSymTable
		if len(self.data) < 2:
			raise "Set::argx", "Set called with %i arguments; at least 2 arguments are expected." % len(data)
		data = [self.data[0]] + DataEval(self.data[1:])
		for d in data[:-1]:
			if d.Head() != "Symbol":
				raise "Set::ParamError", "First parameters of Set must be a Symbol, not %s" % d.Head()
			gSymTable[d.data] = data[-1]
		return data[-1]

#----------------------------------------------------------------------
class ExprUnset(Expr):

	def Head(self): return 'Unset'

	def Eval(self):
		global gSymTable
		if len(self.data) < 1:
			raise "Unset::argx", "Unset called with 0 arguments; at least 1 argument is expected."
		for d in self.data:
			if d.Head() != "Symbol":
				raise "Set::ParamError", "Parameters of Unset must be Symbol, not %s" % d.Head()
			if d.data in gSymTable.keys():
				del gSymTable[d.data]
		return ExprSymbol("OK")

#----------------------------------------------------------------------
class ExprPower(Expr):

	def Head(self): return 'Power'

	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 2:
			raise "Power::argx", "Power called with %i arguments; 2 arguments are expected." % len(data)
		if not isinstance(data[0], (ExprReal, ExprComplex)) or \
				not isinstance(data[1], (ExprReal, ExprComplex)):
			return ExprPower(data)
		return ExprNumber( pow(data[0].data, data[1].data) )

#----------------------------------------------------------------------
class ExprEqual(Expr):

	def Head(self): return 'Equal'

	def Eval(self):
		if len (self.data) < 2: return true
		data = DataEval(self.data)
#		if not isinstance(data[0], (ExprReal, ExprComplex)): return self
#		val = data[0].data
#		for d in data[1:]:
#			if not isinstance(d, (ExprReal, ExprComplex)): return self
#			if d.data != val: return false
#		return true
		# Use the defined __cmp__ on Eval
		val = data[0]
		for d in data[1:]:
			if val != d: return false
		return true

#----------------------------------------------------------------------
class ExprIn(Expr):

	def Head(self): return 'In'

	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "In::argx", "In called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return self
		idx = int(data[0])
		# make positive numbers 1-indexed, to match Mathematica
		if idx > 0: idx -= 1
		try: return gInList[idx]
		except: return ExprIn(data)

#----------------------------------------------------------------------
class ExprOut(Expr):

	def Head(self): return 'Out'

	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Out::argx", "Out called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return self
		idx = int(data[0])
		# make positive numbers 1-indexed, to match Mathematica
		if idx > 0: idx -= 1
		try: return gOutList[idx].Eval()
		except: return self

#----------------------------------------------------------------------
class ExprSin(Expr):
	
	def Head(self): return 'Sin'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Sin::argx", "Sin called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprSin(data)
		return ExprNumber(math.sin(data[0].data))

#----------------------------------------------------------------------
class ExprCos(Expr):
	
	def Head(self): return 'Cos'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Cos::argx", "Cos called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprCos(data)
		return ExprNumber(math.cos(data[0].data))

#----------------------------------------------------------------------
class ExprTan(Expr):
	
	def Head(self): return 'Tan'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Tan::argx", "Tan called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprTan(data)
		return ExprNumber(math.tan(data[0].data))

#----------------------------------------------------------------------
class ExprASin(Expr):
	
	def Head(self): return 'ASin'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "ASin::argx", "ASin called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprASin(data)
		return ExprNumber(math.asin(data[0].data))

#----------------------------------------------------------------------
class ExprACos(Expr):
	
	def Head(self): return 'ACos'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "ACos::argx", "ACos called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprACos(data)
		return ExprNumber(math.acos(data[0].data))

#----------------------------------------------------------------------
class ExprATan(Expr):
	
	def Head(self): return 'ATan'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "ATan::argx", "ATan called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprATan(data)
		return ExprNumber(math.atan(data[0].data))

#----------------------------------------------------------------------
class ExprRad2Deg(Expr):
	
	def Head(self): return 'Rad2Deg'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Rad2Deg::argx", "Rad2Deg called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprRad2Deg(data)
		return ExprNumber(math.degrees(data[0].data))

#----------------------------------------------------------------------
class ExprDeg2Rad(Expr):
	
	def Head(self): return 'Deg2Rad'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Deg2Rad::argx", "Deg2Rad called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprDeg2Rad(data)
		return ExprNumber(math.radians(data[0].data))

#----------------------------------------------------------------------
class ExprSqrt(Expr):
	
	def Head(self): return 'Sqrt'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Sqrt::argx", "Sqrt called with %i arguments; 1 argument is expected." % len(data)
		if isinstance(data[0], ExprReal):
			return ExprNumber(math.sqrt(data[0].data))
		elif isinstance(data[0], ExprComplex):
			return ExprNumber(pow(data[0].data, 0.5))
		else:
			return ExprSqrt(data)

#----------------------------------------------------------------------
class ExprRoot(Expr):
	def Head(self): return 'Root'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 2:
			raise "Root::argx", "Root called with %i arguments; 2 arguments are expected." % len(data)
		if not isinstance(data[0], (ExprReal, ExprComplex)):
			return ExprRoot(data)
		return ExprNumber(pow(data[0].data, 1.0/data[1].data))

#----------------------------------------------------------------------
class ExprExp(Expr):
	def Head(self): return 'Exp'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Exp::argx", "Exp called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprExp(data)
		return ExprNumber(math.exp(data[0].data))

#----------------------------------------------------------------------
class ExprAbs(Expr):
	def Head(self): return 'Abs'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Abs::argx", "Abs called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], (ExprReal, ExprComplex)):
			return ExprExp(data)
		return ExprNumber(abs(data[0].data))

#----------------------------------------------------------------------
class ExprMod(Expr):
	def Head(self): return 'Mod'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 2:
			raise "Mod::argx", "Mod called with %i arguments; 2 arguments are expected." % len(data)
		if not isinstance(data[0], ExprReal) or not isinstance(data[1], ExprReal):
			return ExprMod(data)
		return ExprNumber(data[0].data % data[1].data)

#----------------------------------------------------------------------
class ExprRound(Expr):
	def Head(self): return 'Round'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1 and len(data) != 2:
			raise "Round::argx", "Round called with %i arguments; 1 or 2 arguments are expected." % len(data)
		if len(data) == 2:
			n = data[1]
		else:
			n = ExprNumber(0)
		if not isinstance(data[0], ExprReal) or not isinstance(n, ExprReal):
			return ExprRound(data)
		return ExprNumber(round(data[0].data, n.data))

#----------------------------------------------------------------------
class ExprRand(Expr):
	def Head(self): return 'Rand'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 0:
			raise "Rand::argx", "Rand called with %i arguments; 0 arguments are expected." % len(data)
		return ExprNumber(random.random())

#----------------------------------------------------------------------
class ExprRandInt(Expr):
	def Head(self): return 'RandInt'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1 and len(data) != 2:
			raise "RandInt::argx", "RandInt called with %i arguments; 1 or 2 arguments are expected." % len(data)
		if len(data) == 2:
			low = data[0]
			high = data[1]
		else:
			low = ExprNumber(0)
			high = data[0]
		if not isinstance(low, ExprReal) or not isinstance(high, ExprReal):
			return ExprRandInt(data)
		if low.data > high.data:
			raise "RandInt::range", "Invalid RandInt range"
		return ExprNumber(random.randint(low.data, high.data))

#----------------------------------------------------------------------
class ExprFloor(Expr):
	def Head(self): return 'Floor'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Floor::argx", "Floor called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprFloor(data)
		return ExprNumber(math.floor(data[0]))

#----------------------------------------------------------------------
class ExprCeil(Expr):
	def Head(self): return 'Ceil'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Ceil::argx", "Ceil called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprCeil(data)
		return ExprNumber(math.ceil(data[0]))

#----------------------------------------------------------------------
class ExprLog(Expr):
	def Head(self): return 'Log'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1 and len(data) != 2:
			raise "Log::argx", "Log called with %i arguments; 1 or 2 arguments are expected." % len(data)
		if not isinstance(data[0], ExprReal) or \
				(len(data) == 2 and not isinstance(data[1], ExprReal)):
			return ExprLog(data)
		if len(data) == 2:
			return ExprNumber(math.log(data[0], data[1]))
		else:
			return ExprNumber(math.log(data[0]))

#----------------------------------------------------------------------
class ExprLog10(Expr):
	def Head(self): return 'Log10'
	
	def Eval(self):
		data = DataEval(self.data)
		if len(data) != 1:
			raise "Log10::argx", "Log10 called with %i arguments; 1 argument is expected." % len(data)
		if not isinstance(data[0], ExprReal):
			return ExprLog10(data)
		return ExprNumber(math.log10(data[0]))

#----------------------------------------------------------------------
# define built-in constants
#----------------------------------------------------------------------
ExprSet([ExprSymbol('pi'),ExprNumber(math.pi)]).Eval()
ExprSet([ExprSymbol('e'),ExprNumber(math.e)]).Eval()

#----------------------------------------------------------------------
# end of PythonicaCore.py
#----------------------------------------------------------------------

