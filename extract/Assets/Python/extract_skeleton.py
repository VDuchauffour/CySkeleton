import inspect
import sys

import simplejson as json

# TODO: Handle properties

# TODO: Handle str vs. unicode (?)


class DocTreeMaker( object ) :
	def __init__( self, iMaxDepth = 3 ) :
		self._sIndentStr = "  "
		self._iMaxDepth = iMaxDepth
	
	def make_doc_tree( self, obj, sName, iDepth = 0, bEnumItem = False ) :
		result = { "name" : sName }
		tp = type(obj)
		if inspect.isclass(tp):
			result["type"] = tp.__name__

		if tp in (bool, int, float, str, unicode) :
			result["value"] = obj
		elif bEnumItem :
			result["value"] = int( obj ) # TODO?
		elif tp == dict : # TODO: Does that make sense?
			result["value"] = []
			for key, val in obj.iteritems() :
				result["value"].append( ( key, self.make_doc_tree( val, sName + "[" + repr(key) + "]", iDepth + 1 ) ) )
		elif tp == property :
			result["getter"] = obj.fget is not None
			result["setter"] = obj.fset is not None
			result["deleter"] = obj.fdel is not None
		
		sDoc = inspect.getdoc( obj )
		if sDoc is not None and sDoc != "" :
			result["doc"] = sDoc

		if inspect.ismodule( obj ) or inspect.isclass( obj ) :
			if iDepth >= self._iMaxDepth :
				sys.stdout.write( "WARNING: Maximum search depth reached at " + sName )
			else :
				bEnum = hasattr( obj, "name" ) and hasattr( obj, "values" )
				
				members = None
				try :
					members = inspect.getmembers( obj ) # Already sorted by name
				except Exception, e :
					print "Could not get members, error: " + str( e )

				if members :
					encodedMembers = []
					for sMemberName, memberObj in members :
						if sMemberName == "__init__" or not sMemberName.startswith( "_" ) :
							bEnumItem = bEnum and type( memberObj ) == obj
							encodedMembers.append( self.make_doc_tree( memberObj, sMemberName, iDepth + 1, bEnumItem ) )
					result["members"] = encodedMembers

		return result


def extract_skeleton( module, out = sys.stdout, iMaxDepth = 3 ) :
	sys.stdout.write( "------------------------------------------------------------------------\n" )
	sys.stdout.write( "Tree for %s START\n" % module.__name__ )
	
	json.dump( DocTreeMaker( iMaxDepth ).make_doc_tree( module, module.__name__ ), out )
	out.write( "\n" )
	
	sys.stdout.write( "Tree for %s END\n" % module.__name__ )
	sys.stdout.write( "------------------------------------------------------------------------\n" )
