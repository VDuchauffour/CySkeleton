"""
Recovers output of the Extract mod and writes it into the file skeleton.json
"""

import os


# Input and output file, change this if necessary
LOG_FILE = "~/Documents/My Games/Beyond the Sword/Logs/PythonDbg.log"
OUT_FILE = "skeleton.json"


START_LINE = "Tree for CvPythonExtensions START"
END_LINE = "Tree for CvPythonExtensions END"


# Expand "~"
inPath = os.path.expanduser( LOG_FILE )
outPath = os.path.expanduser( OUT_FILE )

try :
	has_written = False
	with open( inPath, "r" ) as inFp :
		with open( outPath, "w" ) as outFp :
			writing = False
			for line in inFp :
				if line.strip() == START_LINE :
					writing = True
					has_written = True
				elif line.strip() == END_LINE :
					writing = False
				elif writing :
					outFp.write( line )
	if not has_written :
		print( "ERROR: Tree not found in log" )
except IOError as e :
	print( "Error opening file '" + e.filename + "'" )