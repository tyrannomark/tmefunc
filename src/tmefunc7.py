#cell 0
import collections.abc   ## Called by F.__call__
import operator          ## Probably this one :-)
import random
from inspect       import signature
from typing        import Optional, List, Tuple, Callable
from pprint        import pprint

#cell 1
## Answer from:
## https://stackoverflow.com/questions/45161393/jupyter-split-classes-in-multiple-cells
import functools
def update_class(
    main_class: type = None, exclude: Tuple[str] = ("__module__", "__name__", "__dict__", "__weakref__")
) -> Callable[[type], type]:
    """Class decorator. Adds all methods and members from the wrapped class to main_class
    Args:
    - main_class: class to which to append members. Defaults to the class with the same name as the wrapped class
    - exclude: black-list of members which should not be copied
    """
    def decorates(main_class: type, exclude: Tuple[str], appended_class: type) -> type:
        if main_class is None:
            main_class = globals()[appended_class.__name__]
        ## print( appended_class.__name__ )
        for k, v in appended_class.__dict__.items():
            if k not in exclude:
                setattr(main_class, k, v)
        return main_class
    return functools.partial(decorates, main_class, exclude)

#cell 2
RunTests = (
    "runTestx"
).split('|')

#cell 3
def runTest(key: str, fn: Callable[[None], None], force: bool = False) -> None:
    if force or (key in RunTests):
        print( fn.__name__, "BEGIN")
        fn()
        print( fn.__name__, "END")

def test_runTest():
    print("Hello")
    
runTest("runTest", test_runTest)

#cell 5
##########################################################################################
##########################################################################################
## Class F - a wrapper for functions to provide meta methods
##########################################################################################

Test = []
class F:
  ########################################################################################
  ## Constructor to make an object of class F from a function
  def __init__(self,f):
    self.F                      = f
    self.L                      = len( signature(f).parameters )
    ## print( "__init__ L:", self.L )

#cell 6
def test_F_init():
    f = lambda x: x*2
    print( F(f).F(7) )

runTest("Finit", test_F_init)

#cell 7
@update_class()
class F:
  ########################################################################################
  ## A function to ensure that an object is an object of class F, and make it so if not
  ##   so long as it is a function. Call this as: F.ensure(f)
  def ensure(g):
    if not isinstance(g,F) and isinstance(g, collections.abc.Callable): return( F(g) )
    return( g )

def test_F_ensure():
    f = lambda x: x*2
    ff = F.ensure(f)
    fff = F.ensure(ff)
    print( f.__class__.__name__ )
    print( ff.__class__.__name__ )
    print( fff.__class__.__name__ )
    fff = F.ensure(ff)
    print( ff.F.__class__.__name__ )
    print( fff.F.__class__.__name__ )

runTest("Fensure", test_F_ensure)

#cell 8
@update_class()
class F:
  ########################################################################################
  ## Apply the function in this object to one or more arguments. If the value returned
  ##   is callable, then wrap it in F. This means that functions returned by functions
  ##   using the @F decorator do not need to be declared as @F themselves.
  def __call__(self,*args):
    #3 print( "len(args):",len(args),"self.L:", self.L )
    if len(args) == self.L:
      result = self.F( *args )
    elif len(args) < self.L:
      result = F( lambda *remainder: self(*(args+remainder)) )
    else:
      result = F.ensure( self.F( *(args[:self.L]) ) )( *(args[self.L:]) )
    if isinstance(result, collections.abc.Callable): return F.ensure( result )
    return( result )

#cell 9
def test_F_call():
    f = F( lambda x, y, z: (x - y)*z )
    print( f(5,3,2)    )
    print( f(5,3)(2)   )
    print( f(5)(3,2)   )
    print( f(5)(3)(2)  )
    g = F( lambda x: F( lambda y: F( lambda z: (x - y)*z )))
    print( g(5)(3)(2)  )
    print( g(5)(3,2)   )
    print( g(5,3)(2)   )
    print( g(5,3,2)    )

runTest("Fcall", test_F_call)

#cell 10
@update_class()
class F:
  ########################################################################################
  ## Compose the current functor with another. The bracketed argument is applied second in
  ##   the composition. This can be called from an object, or from the class.
  def compose(fromAtoB :F, fromBtoC :F) -> F:
    fromAtoBF = F.ensure( fromAtoB ); fromBtoCF = F.ensure( fromBtoC )
    def fromAtoC(*args):
      return fromBtoCF( fromAtoBF( *args ) )
    fromAtoCF = F( fromAtoC ); fromAtoCF.L = fromAtoBF.L
    return( fromAtoCF )

#cell 11
def test_F_compose():
    f = F( lambda x: x*2 )
    g = F( lambda x: x+7 )
    print( "***" )
    print( (g.compose(f))( 0 ))
    print( (f.compose(g))( 0 ))

runTest("Fcompose", test_F_compose)

#cell 12
@update_class()
class F:
  ########################################################################################
  ## Compose two functions as a pipeline.
  def __or__(self: F, other: F) -> F: return F.compose(self,other)
  ########################################################################################
  ## Apply two functions to the same input, returning a list of outputs
  def __and__(self: F, other: F): ## Same as 'fan'
    @F
    def f( *args ):
      a = self.F( *args )
      b = other.F( *args )
      if not isinstance( a, list ): a = [ a ]
      if not isinstance( b, list ): b = [ b ]
      return( a + b )
    f.L = self.L
    return( f )

#cell 13
def test_F_orand():
    f = F( lambda x: x*2 )
    g = F( lambda x: x+7 )
    print( (g | f)( 0 ))
    f = F( lambda x: x+5 )
    print( (g & f)( 0 ))

runTest("Forand", test_F_orand)

#cell 14
@update_class()
class F:
  ########################################################################################
  ## Do a binary fold. This is much more stack memory-efficient than linear left- or
  ##   right- folds (implemented below).
  def fold(self,zero=None, direction="L"): ## direction = "L|B|R"
    @F
    def f(l):
      n = len(l)
      if n == 0: return( zero )
      n2 = int( n / 2 )
      if direction == "L":
        if n == 1: return( self.F( zero, l[0] ) )
        left = self.fold(zero,direction)(l[:n2]); right = self.fold(left,direction)(l[n2:])
        return( right )
      elif direction == "R":
        if n == 1: return( self.F( l[0], zero ) )
        right = self.fold(zero,direction)(l[n2:]); left = self.fold(right,direction)(l[:n2])
        return( left )
      if n == 1: return( l[0] )
      left = self.fold(zero,direction)(l[:n2]); right = self.fold(zero,direction)(l[n2:])
      return( self.F( left, right ) )
    return( f )

#cell 15
def test_F_fold():
    f = F( lambda x,y: "("+x+","+y+")" ); print( f("2","3") )
    g = F( lambda x, y: x+y ); print( g(2,3) )
    print( f.fold("","L")( [ str(i) for i in range(4) ] ) )
    print( g.fold(0,"L")(list(range(11))) )
    print( f.fold("","R")( [ str(i) for i in range(4) ] ) )
    print( g.fold(0,"R")(list(range(11))) )
    print( f.fold("","B")( [ str(i) for i in range(4) ] ) )
    print( g.fold(0,"B")(list(range(11))) )

runTest("Ffold", test_F_fold)

#cell 16
@update_class()
class F:
  ########################################################################################
  ## Cumulative binary fold. This function returns a function which gives all the
  ##   intermediary values of the fold, as well as the final one, in a list.
  def cumFold(self,zero=None,direction="L"):
    @F
    def f(l):
      n = len(l)
      if n == 0: return( zero )
      n2 = int( n / 2 )
      if direction == "L":
        if n == 1: return( [ self.F( zero, l[0] ) ] )
        left = self.cumFold(zero,direction)(l[:n2]); right = self.cumFold(left[-1],direction)(l[n2:])
        return( left+right )
      if n == 1: return( [ self.F( l[0], zero ) ] )
      right = self.cumFold(zero,direction)(l[n2:]); left = self.cumFold(right[0],direction)(l[:n2])
      return( left+right )
    return( f )

#cell 17
def test_F_cumFold():
    f = F( lambda x,y: "("+x+","+y+")" ); print( f("2","3") )
    g = F( lambda x, y: x+y ); print( g(2,3) )
    pprint( f.cumFold("")( [ str(i) for i in range(4) ] ) )
    print( g.cumFold(0)(list(range(11))) )
    pprint( f.cumFold("","R")( [ str(i) for i in range(4) ] ) )
    print( g.cumFold(0,"R")(list(range(11))) )

runTest("FcumFold", test_F_cumFold)

#cell 19
@update_class()
class F:
  ########################################################################################
  ## Map the values in a list, with or without indices
  def map(self):
    @F
    def ff( *ll ):
      return(
        [ self(*[ l[i] for l in ll ]) for i in range(len(ll[0])) ] if ll else []
      )
    ff.L = self.L
    return( ff )
  def mapi(self):
    @F
    def ff( *ll ): return(
      [ self( *([i]+[ l[i] for l in ll ]) ) for i in range(len(ll[0])) ] if ll else []
    )
    ff.L = self.L-1
    return( ff )

#cell 20
def test_F_map():
    f = F( lambda x,y,z: x * y + z )
    print( f.map()( [1,2,3,4,5], [5,4,3,2,1], [1,2,3,4,5] ) )
    f = F( lambda x,y: str(x) + "." + str(y) )
    print( f.mapi()( "hello" ) )

runTest("Fmap", test_F_map)

#cell 22
##########################################################################################
##########################################################################################
## Compose and Composition-Related Functions
##########################################################################################

##########################################################################################
## The basic identity function
Id = F(lambda x: x)
##########################################################################################
## The constant value function
@F
def Const(value):
  return F( lambda k: value )

#cell 23
def test_IdConst():
  print( Id( [1,2,3] ) )
  print( Const( 1 )( "dog" ) )

runTest("IdConst", test_IdConst)

#cell 24
##########################################################################################
## 
@F
def Pf(ff = Id):
  @F
  def f(x):
    print( ff(x) )
    return( x )
  f.L = 1
  return( f )

#cell 26
matrix = [ [1,2], [3,1] ] ## list of columns
matrix2 = [ [3,4], [5,6] ] ## list of columns
cvector = [ 3,4 ]

#cell 27
dotProduct = (
	F( lambda a, b: a * b ).map() |
	F( lambda a, b: a+b ).fold(0.0)
)

print( dotProduct( cvector, cvector ) ) ## Prints 25

#cell 28
transpose = F( lambda m:
  [
    [ m[i][j] for i in range(len(m)) ]
    for j in range(len(m[0]))
  ]
)

print( matrix ) ## Prints [ [1,2], [3,1] ]
print( transpose( matrix ) ) ## Prints [[1, 3], [2, 1]]

#cell 29
applyMat = F( lambda m, v: (
  transpose |
  dotProduct(v).map()
)(m) )

pprint( applyMat( matrix, cvector ) ) ## Prints [15.0, 10.0]

#cell 30
matMul = F( lambda m1, m2: applyMat(m1).map()( m2 ) )

print( matMul( matrix, matrix2 ) ) ## Prints [[15.0, 10.0], [23.0, 16.0]]

