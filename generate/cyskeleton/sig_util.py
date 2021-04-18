"""
Utilities to compute signatures from function docstrings.
"""

import re

from cyskeleton.common import *
from cyskeleton import type_util


# Type and "real type" in parenthesis or C-style comments
_RE_RET_TYPE_AUGMENTED = re.compile( r"([^ ]+)\s*\(\s*([^ ()]+)\s*\)" ) # e.g. "int (UnitTypes)"
_RE_RET_TYPE_AUGMENTED_ALT = re.compile( r"([^ ]+)\s*/\*\s*([^ ]+)\s*\*/" ) # e.g. "int /*UnitTypes*/"


def _parse_type_0( tp : str, tc : type_util.TypeContext ) -> Tuple[Optional[str], Optional[str]] :
	""" _parse_type, but the alternate type might be the same as the main type """
	match = _RE_RET_TYPE_AUGMENTED.fullmatch( tp )
	if match :
		return tc.cpp_to_python_type( match.group( 1 ) ), tc.cpp_to_python_type( match.group( 2 ), altType = True )

	match = _RE_RET_TYPE_AUGMENTED_ALT.fullmatch( tp )
	if match :
		return tc.cpp_to_python_type( match.group( 1 ) ), tc.cpp_to_python_type( match.group( 2 ), altType = True )

	return tc.cpp_to_python_type( tp ), tc.cpp_to_python_type( tp, altType = True )

def _parse_type( tp : str, tc : type_util.TypeContext ) -> Tuple[Optional[str], Optional[str]] :
	"""
	Parses a type one of the following forms:
		"[main] ([alt])"
		"[main] /*[alt]*/"
		"[main]"
	Returns main, alt. Both values might be None if the given TypeContext rejects the types.
	"""
	main, alt = _parse_type_0( tp, tc )
	if alt == main :
		alt = None
	return main, alt


def _parse_rough_func_signature( sig : str ) -> Optional[Tuple[str, str]] :
	"""
	Separates the first (return type/name) part from the argument part (in parenthesis).
	Returns None if typeStr contains non-matching parenthesis. Otherwise, returns (first, second), where
		second is the part inside the rightmost pair of top-level parenthesis, and
		first is the part before this pair of parenthesis.
	The rightmost pair of top-level parenthesis are not present in the result.
	"""
	first = ""
	second = None
	numOpenParens = 0
	for c in sig :
		if c == "(" :
			if numOpenParens == 0 :
				# Start with second part!
				# If we already started, then that was a fake second part.
				if second is not None :
					first += second
				second = ""
			numOpenParens += 1
		elif c == ")" :
			if numOpenParens == 0 :
				return None # Missing opening parenthesis
			numOpenParens -= 1

		# Always do this
		if second is None :
			first += c
		else :
			second += c

	if numOpenParens != 0 or second is None :
		return None
	else :
		return first.strip(), second[1:-1].strip() # Remove parentheses around second part


class _SigParser :
	def __init__( self, tc : type_util.TypeContext, verbosity : int ) -> None :
		self._tc = tc
		self._verbosity = verbosity

	def _parse_argument( self, path : str, argDoc : str, argIdx : int ) -> Optional[JsonObj] :
		"""
		Tries to parse an argument of one of the following forms:
			"[type]"
			"[type] [name]"
			"[name]"
		where [type] is something accepted by _parse_type
		"""
		argDoc = argDoc.strip()

		if " " not in argDoc :
			# Special case: we try to guess whether it's a type of a param name

			# Try parsing type, but also check whether we can be sure it's really a type
			tp, altTp = _parse_type( argDoc, self._tc )
			if tp is not None and self._tc.is_known_obj_type( tp ) and altTp is None or self._tc.is_known_obj_type( altTp ) :
				return {
					"name" : f"arg{argIdx}",
					"type" : tp,
					"alt-type" : altTp
				}
			elif type_util.is_python_identifier( argDoc ) :
				return { "name" : argDoc } # The whole thing is probably a name
			else :
				if self._verbosity >= 2 :
					print( f"{path} - Cannot parse argument '{argDoc}': Neither valid type nor valid identifier" )
				return None

		# Otherwise, we have a space.

		# Still might be just a type (e.g. "int /*YieldTypes*/")
		tp, altTp = _parse_type( argDoc, self._tc )
		if tp is not None and altTp is not None :
			# parse_type is rigorous if there is a space; this must be a type
			return {
				"name" : f"arg{argIdx}",
				"type" : tp,
				"alt-type" : altTp
			}

		# Only remaining case: should be of the form "[type] [name]".
		idx = argDoc.rfind( " " ) # rfind, as [type] might still a space
		typePart = argDoc[:idx].strip()
		argNamePart = argDoc[idx+1:].strip()
		tp, altTp = _parse_type( typePart, self._tc )

		if tp is not None :
			# Special case like "CvPlot *plot"
			if argNamePart.startswith( "*" ) :
				argNamePart = argNamePart[1:].strip()
			if argNamePart.startswith( "&" ) :
				argNamePart = argNamePart[1:].strip()

			# Check if everything came out right
			if type_util.is_python_identifier( argNamePart ) :
				return {
					"name" : f"arg{argIdx}",
					"type" : tp,
					"alt-type" : altTp
				}
			else :
				if self._verbosity >= 2 :
					print( f"{path} - Cannot parse argument '{argDoc}': assumed name '{argNamePart}' not valid" )
				return None
		else :
			if self._verbosity >= 2 :
				print( f"{path} - Cannot parse argument '{argDoc}': assumed type '{typePart}' not valid" )
			return None

	def parse( self, path : str, sig: str ) -> Optional[JsonObj] :
		result = {}

		rfs = _parse_rough_func_signature( sig )
		if rfs is None :
			if self._verbosity >= 3 :
				print( f"{path} - Cannot parse signature '{sig}': missing or non-matching parentheses" )
			return None
		retTypeDoc, argsDoc = rfs

		# First, see if the function name is contained in the signature and we accidentally parsed it
		funcName = path.split( "." )[-1] # TODO?
		if retTypeDoc.endswith( funcName ) :
			retTypeDoc = retTypeDoc[:-len(funcName)].strip()

		# Parse return type
		if retTypeDoc != "" :
			retType, retTypeAlt = _parse_type( retTypeDoc, self._tc )
			if retType is None :
				if self._verbosity >= 3 :
					print( f"{path} - Cannot parse signature '{sig}': invalid return type '{retTypeDoc}'" )
				return None
			result["return-type"] = retType
			if retTypeAlt is not None :
				result["return-type-alt"] = retTypeAlt

		result["args"] = []

		if argsDoc != "" :
			argNames = set() # To catch duplicate argument names
			for idx, arg in enumerate( argsDoc.split( "," ) ) :
				parsed = self._parse_argument( f"{path}/arg{idx}", arg, idx )
				if parsed is None :
					return None # Failed parsing that argument; error message already printed
				assert parsed["name"] is not None
				if parsed["name"] in argNames :
					if self._verbosity >= 1 :
						print( f"{path} - Cannot parse signature '{sig}': duplicate arg name '{parsed['name']}" )
				argNames.add( parsed["name"] )
				result["args"].append( parsed )

		return result



def try_parse_signature( path : str, sig: str, tc : type_util.TypeContext, verbosity : int ) -> Optional[JsonObj] :
	return _SigParser( tc, verbosity ).parse( path, sig )