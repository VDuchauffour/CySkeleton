from dataclasses import dataclass
import re

from cyskeleton.common import *

_RE_PYTHON_IDENTIFIER = re.compile( "[a-zA-Z_][a-zA-Z0-9_]*" )


def is_python_identifier( s : str ) -> bool :
	return _RE_PYTHON_IDENTIFIER.fullmatch( s ) is not None

def python_identifier_or_none( s : str ) -> Optional[str] :
	if is_python_identifier( s ) :
		return s
	else :
		return None


def _sanitize_type( typeStr : str ) -> Optional[str] :
	"""
	Removes C++isms like "*", "&" and const from the type string.
	Returns None if the result is not a valid python 2 identifier
	"""
	while typeStr.endswith( "*" ) or typeStr.endswith( "&" ) :
		typeStr = typeStr[:-1]

	if typeStr.startswith( "const " ) :
		typeStr = typeStr[len("cosnt "):]

	return typeStr.strip()


_BUILTIN_TYPES : Mapping[str, str] = {
	"void" : "None",
	"bool" : "bool",
	"int" : "int",
	"unsigned int" : "int",
	"float" : "float",
	"string" : "str",
	"std::string" : "str",
	"char*" : "str",
	"TCHAR*" : "str",
	"TCHAR *" : "str", # TODO?
	"wstring" : "unicode",
	"std::wstring" : "unicode",
	"boost::python::list" : "List",
	"std::vector<CvString>" : "List[str]",
	"python::tuple" : "Tuple"
}

@dataclass
class _TypeOverride :
	pattern : re.Pattern
	newType : str
	newTypeAlt : Optional[str]
	mustBeKnown : bool = False

	@staticmethod
	def parse( data : JsonObj ) -> "_TypeOverride" :
		return _TypeOverride(
			re.compile( data["pattern"] ),
			data["type"],
			data.get( "alt-type" ),
			data.get( "must-be-known", False )
		)


class TypeContext :
	def __init__( self ) -> None :
		self._knownCustomTypes : Set[str] = set()
		self._typeOverrides : List[_TypeOverride] = []

	def add_custom_type( self, name : str ) -> None :
		assert is_python_identifier( name )
		self._knownCustomTypes.add( name )

	def _add_type_override( self, to : _TypeOverride ) -> None :
		self._typeOverrides.append( to )

	def read_type_overrides( self, config : JsonObj ) -> None :
		for toData in config.get( "type-overrides", () ) :
			self._add_type_override( _TypeOverride.parse( toData ) )

	def custom_types( self ) -> Iterator[str] :
		yield from self._knownCustomTypes

	def cpp_to_python_type( self, cppType : str, altType : bool = False ) -> Optional[str] :
		"""
		Returns a valid python type (assuming correct config) or None
		"""
		if cppType in _BUILTIN_TYPES :
			return _BUILTIN_TYPES[cppType] # We trust these are valid

		# Try removing stuff like "*", "&" first
		cppType = _sanitize_type( cppType )
		if cppType in _BUILTIN_TYPES :
			return _BUILTIN_TYPES[cppType] # We trust these are valid

		for to in self._typeOverrides :
			if not to.mustBeKnown or self.is_known_obj_type( cppType ) :
				match = to.pattern.fullmatch( cppType )
				if match :
					if not altType :
						return to.newType.format( *match.groups() ) # We trust these are valid
					else :
						if to.newTypeAlt is None :
							return cppType
						else :
							return to.newTypeAlt.format( *match.groups() ) # We trust these are valid

		# We don't trust that this is a valid python identifier
		return python_identifier_or_none( cppType )

	def is_known_obj_type( self, pyType : str ) -> bool :
		"""
		Whether we can be sure that the specified type is a conventional type, e.g. int, str, List[str] or CyGame
		(as opposed to something like function or instancemethod).
		"""
		return pyType in _BUILTIN_TYPES.values() or pyType in self._knownCustomTypes


def test() -> None :
	tc = TypeContext()
	assert tc.cpp_to_python_type( "CvTutorialMessage*" ) == "CvTutorialMessage"
	print( "All tests passed." )

if __name__ == "__main__" :
	test()