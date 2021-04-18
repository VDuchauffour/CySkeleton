#!/usr/bin/env python3

"""
Module to preprocess the skeleton JSON.
* Parses docstrings for types
"""

from dataclasses import dataclass
import json
import re

from cyskeleton.common import *
from cyskeleton import sig_util
from cyskeleton import type_util


@dataclass( frozen = True )
class SigOverride :
	"""
	A single configuration item for a function/method signature override.
	"""
	path : Union[str, re.Pattern]
	newSig : str

	def try_make_new_sig( self, path : str ) -> Optional[str] :
		if isinstance( self.path, str ) :
			if path != self.path :
				return None
			return self.newSig
		else :
			assert isinstance( self.path, re.Pattern )
			match = self.path.fullmatch( path )
			if not match :
				return None
			return self.newSig.format( *match.groups() )


	@staticmethod
	def parse( data : JsonObj ) -> "SigOverride" :
		path : Union[str, re.Pattern]
		if "path" in data :
			assert "pathPattern" not in data
			path = data["path"]
		elif "pathPattern" in data :
			path = re.compile( data["pathPattern"] )
		else :
			raise Exception( "Each type override must have either a path or a path pattern" )

		newSig = data["signature"]

		return SigOverride( path, newSig )


class Preprocess :
	"""
	Preprocesses a module
	"""
	def __init__( self, data : JsonObj, conf : Optional[JsonObj], verbosity : int = 0 ) -> None :
		assert data["type"] == "module"
		self._module_name = data["name"]
		self._verbosity = verbosity
		
		# Parse configuration
		if conf is None :
			conf = {}
		self._sigOverrides = [SigOverride.parse( sigOvConf ) for sigOvConf in conf.get( "sig-overrides", () )]
		self._usedSigOverrides = set()
		
		# Prepare type context
		self._tc = type_util.TypeContext()
		self._tc.read_type_overrides( conf )
		
		# Collect types
		for member in data.get( "members", () ) :
			if member["type"] in {"class", "type"} :
				self._tc.add_custom_type( member["name"] )
		if self._verbosity >= 2 :
			print( "Known types: " + ", ".join( sorted( self._tc.custom_types() ) ) )

		for member in data["members"] :
			if member["type"] == "class" :
				self._preprocess_class( member, data["name"] )
			elif member["type"] == "type" :
				self._preprocess_type( member, data["name"] )
			elif member["type"] == "function" :
				self._preprocess_function( member, data["name"] )
			elif member["type"] in ("bool", "int", "float", "str", "unicode" ) :
				pass # Nothing to do
			else :
				if self._verbosity >= 1 :
					print( f"Ignoring member {data['name']}.{member['name']} of unknown type '{member['type']}'" )
		
		for sigOv in self._sigOverrides :
			if sigOv not in self._usedSigOverrides :
				print( f"WARNING: signature override {sigOv} unused!" )
	
	def _preprocess_class( self, data : JsonObj, parentPath : str ) -> None :
		assert data["type"] == "class"
		path = parentPath + "." + data["name"]

		for member in data["members"] :
			if member["type"] == "instancemethod" :
				self._preprocess_function( member, path )
			elif member["type"] == "property" :
				pass # Nothing to do
			else :
				if self._verbosity >= 1 :
					print( f"Ignoring member {path}.{member['name']} of unknown type '{member['type']}'" )

	def _preprocess_type( self, data : JsonObj, parentPath : str ) -> None :
		assert data["type"] == "type"
		for member in data["members"] :
			# Types of enum members
			# TODO: This might also be useful elsewhere
			if member["type"].startswith( self._module_name + "." ) :
				member["type"] = member["type"][len(self._module_name + "."):]

	def _preprocess_function( self, data : JsonObj, parentPath : str ) -> None :
		assert data["type"] in ("function", "instancemethod")
		path = parentPath + "." + data["name"]

		if "doc" in data and "-" in data["doc"] :
			# Try to split docstring into signature part and documentation part
			doc : str = data["doc"]
			idx = doc.index( "-" )
			posSig = doc[:idx].strip() # This might be a signature

			sig = sig_util.try_parse_signature( path, posSig, self._tc, self._verbosity )
			if sig is not None :
				data["signature"] = sig
				data["doc"] = doc[idx+1:].strip()
			# Otherwise, we leave the doc as is.
		elif "doc" in data :
			# Try to parse whole docstring as signature
			sig = sig_util.try_parse_signature( path, data["doc"], self._tc, self._verbosity )
			if sig is not None :
				data["signature"] = sig
				data["doc"] = ""
		
		# Try sig overrides
		for sigOverride in self._sigOverrides :
			newSig = sigOverride.try_make_new_sig( path )
			if newSig is not None :
				self._usedSigOverrides.add( sigOverride )
				newSigParsed = sig_util.try_parse_signature( path, newSig, self._tc, self._verbosity )
				if newSigParsed is not None :
					data["signature"] = newSigParsed
				else :
					print( f"ERROR: sig override {sigOverride} produced invalid signature '{newSig}'" )



def main() -> None :
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument( "--config", help = "The configuration file to use." )
	parser.add_argument( "input_json", help = "The input skeleton, generated by the CySkeleton-extract mod." )
	parser.add_argument( "output_json", help = "The output file." )
	parser.add_argument( "-v", "--verbosity", type = int, default = 0, choices = (0,1,2,3),
			help = "How much information to print (0: nothing, 3: everything; default:0)." )
	args = parser.parse_args()

	if args.config :
		with open( args.config, "r" ) as fp :
			confData = json.load( fp )
	else :
		confData = None
	with open( args.input_json, "r" ) as fp :
		data = json.load( fp )
	Preprocess( data, confData, verbosity = args.verbosity )
	with open( args.output_json, "w" ) as fp :
		json.dump( data, fp, indent = "\t" )

if __name__ == "__main__" :
	main()