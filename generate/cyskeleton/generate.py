#!/usr/bin/env python3
"""
Generate python modules from (preprocessed) skeleton.
"""

from cyskeleton.common import *


_IGNORED_NAMES = ("__init__",)
_IGNORED_TYPES = ("member_descriptor",)


_TPL_MODULE_HEADER = '''\
"""
{name}

{doc}
"""
'''

_TPL_TYPE_HEADER = "{indent}class {name} :\n"
_TPL_CLASS_HEADER = "{indent}class {name}( object ) :\n"
_TPL_FUNCTION_HEADER = "{indent}def {name}( {args} ) :\n"
_TPL_FUNCTION_SIG = "{indent}\t# type: {sig}\n"

_TPL_DOC = '{indent}\t""" {doc} """\n'
_TPL_PASS = '{indent}\tpass\n'

_TPL_MEMBER = "{indent}{name} = {value} # type: {type}\n"

_TPL_PROPERTY = '''\
{indent}@property
{indent}def {name}( self ) :
{indent}\t# type: () -> Any
{indent}\tpass
{indent}@{name}.setter
{indent}def {name}( self, value ) :
{indent}\t# type: (Any) -> None
{indent}\tpass
'''

def _gen( skeleton : JsonObj, out : TextIO, path : str, indent : str = "" ) -> None :
	assert skeleton["type"] != "module"
	assert "name" in skeleton

	name = skeleton["name"]
	tp = skeleton["type"]
	
	if tp in ("type", "class") :
		if tp == "type" :
			out.write( _TPL_TYPE_HEADER.format( indent = indent, name = name ) )
		elif tp == "class" :
			out.write( _TPL_CLASS_HEADER.format( indent = indent, name = name ) )
		needPass = True # Whether we need to write 'pass' at the end to avoid an indention error
		if "doc" in skeleton :
			out.write( _TPL_DOC.format( indent = indent, doc = skeleton["doc"] ) )
			needPass = False
		for member in skeleton.get( "members", () ) :
			needPass = False
			_gen( member, out, path = f"{path}.{skeleton['name']}", indent = indent + "\t" )
		if needPass :
			out.write( _TPL_PASS.format( indent = indent ) )
	elif tp in ( "function", "instancemethod" ) :
		if "signature" not in skeleton :
			argNames = ["*args", "**kwargs"]
			sigStr = None
		else :
			sig = skeleton["signature"]
			argNames = [arg["name"] for arg in sig.get( "args" )]
			argTypes = [arg.get( "type", "Any" ) for arg in sig.get( "args" )] # TODO: alt-types?
			retType = sig.get( "return-type", "Any" )
			sigStr = f"({', '.join( argTypes )}) -> {retType}"

		if tp == "instancemethod" :
			argNames.insert( 0, "self" )

		argStr = ", ".join( argNames )

		out.write( _TPL_FUNCTION_HEADER.format( indent = indent, name = name, args = argStr ) )

		if sigStr :
			out.write( _TPL_FUNCTION_SIG.format( indent = indent, sig = sigStr ) )

		if "doc" in skeleton and skeleton["doc"] :
			out.write( _TPL_DOC.format( indent = indent, doc = skeleton["doc"] ) )
		else :
			out.write( _TPL_PASS.format( indent = indent ) )

	elif "value" in skeleton :
		out.write( _TPL_MEMBER.format( indent = indent, name = name, value = skeleton["value"], type = tp ) )
	elif tp == "property" :
		out.write( _TPL_PROPERTY.format( indent = indent, name = name ) )
		# TODO: Only add setter if fset method of property is present (has to be done in extract)
	elif name not in _IGNORED_NAMES and tp not in _IGNORED_TYPES :
		print( f"WARNING: Ignored {path}.{name} of type {tp}" )



def gen_module( skeleton : JsonObj, out : TextIO ) -> None :
	assert skeleton["type"] == "module"
	out.write( _TPL_MODULE_HEADER.format( name = skeleton["name"], doc = skeleton.get( "doc", "" ) ) )
	for member in skeleton.get( "members", () ) :
		out.write( "\n" )
		_gen( member, out, path = skeleton["name"] )


def _main() -> None :
	import argparse
	import json
	import os

	parser = argparse.ArgumentParser()
	parser.add_argument( "input_json", help = "The preprocessed skeleton." )
	parser.add_argument( "output_py", help = "The path to the output file, usually named 'CvPythonExtensions.py'." )

	args = parser.parse_args()
	with open( args.input_json, "r" ) as fp :
		skeleton = json.load( fp )
	os.makedirs( os.path.dirname( args.output_py ), exist_ok = True )
	with open( args.output_py, "w" ) as fp :
		gen_module( skeleton, fp )

if __name__ == "__main__" :
	_main()