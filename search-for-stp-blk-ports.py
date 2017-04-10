#!/usr/bin/python

#################################################################################################
# Use: Search all switches import via CSV format file for any spanning-tree blocked ports		#
# Input: CSV file with two fields per device, separated by a comma.								#
#			Column 1: Switch hostname															#
#			Column 2: Switch IP address															#
#			Each device on a new line separated by a carriage return							#
# Output: All info is outputted to screen.  No files are saved									#
#################################################################################################

import inspect
import subprocess
import re
import socket
import sys
import time
import os
import paramiko as pm
import lib.functions as fn
import lib.user_functions as ufn
import lib.ssh_functions as sfn


### Variables ###
# User credentials
user = ''												# Add your username here if desired
pw = ''													# Add your password here if desired
# Script variables
switchSkipped = False
noBlockHost = []										# Variable for storing hosts with no blocked ports detected
noSSHHost = []											# Variable for storing hosts that were unable to connect via SSH
resultDict = dict()										# Variable created as a dictionary type
switchFileName = 'switches.txt'							# File with a list of all corporate host device IP addresses
inputDirectory = 'textfiles/'							# File directory for any data files used by this script
### /Variables ###


# Get credentials from user if not already set
user, pw = ufn.getUserCredentials(user, pw)
# Store user credentials in creds class
creds = fn.setUserCredentials(user, pw)

# If switchFileName not predefined, ask user for filename.  Prepend with input directory
switchFileName = inputDirectory + ufn.userGetCorpSWFileName(switchFileName)

print "\n"
# Import file contents
fileLines = fn.readFromFile(switchFileName)

# Count how many switches are in the import file
switchCount = fn.file_len(switchFileName)

# Counter for progress bar
i = 0

# Progress bar for each switch listed in file
fn.printProgress(i, switchCount, prefix = 'Progress:', suffix = 'Complete')

# For each line extracted from the file, loop
for line in fileLines:
	# Split each line on whitespace
	line = line.split(',')
	# Set switch name and IP variables
	switchName = fn.stripNewline(line[0])
	switchIP = fn.stripNewline(line[1])
	# Dictionary to store results in; instantiate as empty
	resultList = {}
	# If 'line' is empty/all whitespace, this will fail
	try:
		# Connect to device; return unique list of STP blocked ports on host
		# Index 0 is device hostname, index 1 is device IP address

		# Initiate an SSH session
		ssh = sfn.connectToSSH(switchIP, creds)
		# Verify ssh connection established and didn't return an error
		if sfn.sshSkipCheck(ssh):
			# Set variable to True if switch was skipped
			switchSkipped = True
		# Establish SSH interactive session
		sshConn = ssh.invoke_shell()
		### Send switch commands ###
		# Set terminal output settings to infinite scroll
		sshConn.send("terminal length 0\n")
		# Pause to allow command to complete
		time.sleep(.5)
		# Show all ports currently blocked by STP
		sshConn.send("show spanning-tree blockedports\n")
		# Pause to allow command to complete
		time.sleep(1)
		# Set terminal output settings back to default settings
		sshConn.send("terminal length 24\n")
		# Save any command output as 'output'
		output = sshConn.recv(5000)
		# Disconnect from the SSH session
		sfn.disconnectFromSSH(ssh)

		# Replace everywhere with multiple spaces with only a single space
		output = fn.replaceDoubleSpaces(output)
		# Replace all newlines (\r\n) in output with a single space
		output = re.sub(r"\r\n", " ", output)
		# Split result by individual spaces
		output = output.split(" ")
		# Tracking variable for excluding duplicate interface entries in list
		# Intialize/reset as an empty list
		trackList = []
		# For each interface in output, identified by '/', print with no duplicates
		for line in output:
			# '//' detection needed as NX-OS outputs URL's in login banner
			# 'and/or' detection needed in case it is in a login banner (custom fix)
			if ("/" in line or "Po" in line) and not ("//" in line or "and/or" in line):
				# If interface isn't currently in the list (unique interface), add it to list
				if (line not in trackList) and line:
					trackList.append(line)
				# Otherwise, it's a duplicate interface and already in the list.  Skip adding it
				else:
					pass
			# If output doesn't contain a '/', or isn't a Port-Channel, it's not considered an interface.  Skip checking it
			else:
				pass

	except:
		pass

	finally:
		# If host is skipped, store into variable for later
		if switchSkipped:
			noSSHHost.append(switchName)
			# Reset variable back to False
			switchSkipped = False
		# If host connects successfully, store ports in dictionary variable 'resultDict'
		# Use hostname as key for storing this data
		elif switchName not in resultDict:
			resultDict[switchName] = trackList
		else:
			pass
			#print "%s is most likely a duplicate switch in the file %s.  Skipping." % (line[0], switchFileName)

	# Increment progress bar counter
	i += 1
	# Progress bar for each switch listed in file
	fn.printProgress(i, switchCount, prefix = 'Progress:', suffix = 'Complete')

# Remove extra variables returned from checkSTPBlockedPorts as variable returned is the full list
chars_to_remove = ['[', ']', '\'', ',']
# Spacer between checking output above and result output below
print "\n\n"
# Counter in case no switches detected with any blocked ports
i = 0

for x in resultDict:
	# 'y' is variable to append to 'x' key
	y = resultDict[x]
	# Remove the single apostrophe, comma, [ and ] characters returned from list in previous function
	y = str(y).translate(None, ''.join(chars_to_remove))
	# Add a comma before each space between ports if there are multiple ports
	y = str(y).replace(" ", ", ")
	if y:
		# This is the first host listed, so only print the 'print' statement once at the beginning
		if i == 0:
			print "List of all switches with STP blocked ports found:\n"
			# Change value of 'i' so above 'print' statement isn't repeated on every loop iteration
			i = 1
		print "%s:" % (x)
		print "Ports: %s\n" % (y)
	else:
		noBlockHost.append(x)
# If 'i' is still 0, no switches were found with blocked ports.  Specify this to user
if i == 0:
	print "No blocked ports were found on any checked switch."

print "\nList of all switches checked with NO blocked ports found:\n"
# For each host in noBlockHost list, print out the hostname.  Sort alphabetically
for x in sorted(noBlockHost):
	print "%s" % (x)

# If any hosts were skipped, list them here
if noSSHHost:
	print "\nList of all switches skipped:\n"
	for x in noSSHHost:
		print "%s" % (x)
