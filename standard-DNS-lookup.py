#!/usr/bin/python

#################################################################################################
# Use: Search all switches import via CSV format file to see if they resolve via DNS			#
# Input: CSV file with two fields per device, separated by a comma.								#
#			Column 1: Switch hostname															#
#			Column 2: Switch IP address															#
#			Each device on a new line separated by a carriage return							#
# Output: All info is outputted to screen.  No files are saved									#
#################################################################################################

import socket
import lib.functions as fn
from lib.user_functions import userGetSwitchFileName


### Variables ###
# Script variables
devicesFileName = 'devices_full.txt'					# File with a list of all corporate host device IP addresses
inputDirectory = 'textfiles/'							# File directory for any data files used by this script
### /Variables ###


# If devicesFileName not predefined, ask user for filename.  Prepend with input directory
devicesFileName = inputDirectory + userGetSwitchFileName(devicesFileName)

print "\n"
# Import file contents
fileLines = fn.readFromFile(devicesFileName)

# Count how many switches are in the import file
switchCount = fn.file_len(devicesFileName)

# For each line extracted from the file, loop
for line in fileLines:
	# Split each line on whitespace
	line = line.split(',')
	# Set switch name and IP variables
	switchName = line[0]
	switchIP = line[1]
	# If 'line' is empty/all whitespace, this will fail
	try:
		# Attempts to lookup imported network device by name
		socket.gethostbyname(switchName)

	except:
		print "%s,%s" % (switchName, switchIP)
