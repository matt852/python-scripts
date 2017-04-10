#!/usr/bin/python

#####################################################################################################
# Use: Converts decimal notation MAC addresses into all uppercase colon delimited format			#
# Input: TXT file with a single decimal notation MAC address per line, separated by carriage return	#
# Output: TXT file with the converted MAC address in uppercase colon delimited format				#
#####################################################################################################

import pdb 			# Set breakpoints in script for debugging with this line: pdb.set_trace()
import inspect
import subprocess
import re
import socket
import sys
import os
import lib.functions as fn
import lib.user_functions as ufn
import lib.ssh_functions as sfn

### Variables ###
# Script variables
inputFileName = ''										# File with a list of data to import
outputFileName = 'output.csv'							# File to output any results to
inputDirectory = 'textfiles/'							# File directory for any data files used by this script
outputDirectory = 'logs/'								# File directory with files for logging output
### /Variables ###


# If inputFileName not predefined, ask user for filename.  Prepend with input directory
inputFileName = inputDirectory + ufn.userGetFileName(inputFileName)

# If outputFileName not predefined, ask user for filename
outputFileName = outputDirectory + ufn.userGetOutputFileName(outputFileName)

# Import file contents
fileLines = fn.readFromFile(inputFileName)

# Converts decimal notation MAC addresses in provided file into all uppercase colon delimited format
# Example: inputting 1234.56ab.cdef returns 12:34:56:AB:CD:EF
for mac in fileLines:
	# Convert imported MAC address to the colon-delimited MAC address format
	newMac = fn.convertMacFormatDec2Col(mac)
	# Format output
	output = "%s\n" % (newMac)
	# Save results to file
	fn.appendCommandToFile(output, outputFileName)
