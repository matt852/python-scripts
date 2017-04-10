#!/usr/bin/python

#####################################################################################################
# Written by: 																						#
# Creation date			2-4-2017																	#
# Last modifed date		4-9-2017																	#
#																									#
# Use: Auto configure firewall ACL to allow specified access if necessary							#
# Input: All input is done via the CLI.  The parameters that are needed are:						#
#			Username/Password - for firewall SSH access												#
#			HostFW - firewall this change is made on; preconfigured in script variables				#
#			Change Ticket - change ticket number for this change									#
#			Ticket Description - 1 or 2 word description about this change, for object-group naming	#
#			Source IP's - All source IP addresses with subnet masks, one per line, in this format:	#
#							10.0.0.1 255.255.255.255												#
#							10.0.1.0 255.255.255.0													#
#							[etc]																	#
#			Desination IP's - All destination IP addresses the source IP's need access to			#
#							[same format as source IP's]											#
#			Ports/Protocols - All ports and protocols that need to be opened, in this format:		#
#							80 TCP																	#
#							161 UDP																	#
#							[etc]																	#
# Output: TXT file with all commands executed on the firewall										#
#			Additionally, all output and results are displayed on screen							#
# To Do: add support for source ports (low priority, rarely used)									#
#			add keyword when inputting IP's to reloop if mistake is entered							#
#			add support for all ports																#
#####################################################################################################

import inspect
import subprocess
import re
import socket
import sys
import os
import time
import datetime
import lib.functions as fn
import lib.user_functions as ufn
import lib.ssh_functions as sfn
import lib.netmiko_functions as nfn
import lib.ip_functions as ifn
import lib.fw_functions as fwn


### Variables ###
# User credentials
user = ''												# Add your username here if desired
pw = ''													# Add your password here if desired
# Script variables
userInitials = ''										# User initials. If not set, uses 'user' from credentials
hostFW = ''												# Firewall IP address
outputFileName = 'fw-open-port-output.txt'				# File to output any results to
outputDirectory = 'logs/'								# File directory with files for logging output
deviceType = 'cisco_asa'								# Type of device, specified for Netmiko. Reference Netmiko documentation if using anything else
sourceIPIntDict = dict()
sourceIPMaskDict = dict()
duplicateSourceIPIntDict = dict()
duplicateSourceIPMaskDict = dict()
destIPMaskDict = dict()
portDict = dict()
varDict = dict()
intToACLDict = dict()
srcOGNameDict = dict()
dstOGName = ''
portOGName = ''
configCommandsList = []
changeTicket = ''
ranOnce = False
newSrcOGCounter = 0
### /Variables ###


# Validates input is an IP address and subnet mask, one per line, separated by a space
# Returns True if valid, False if invalid
def validateIPMaskUserInput(input):
	# Loop for each inputted source IP address and subnet mask
	for x in input:
		# Reduce all spacing to just a single space per section
		x = fn.replaceDoubleSpaces(x)
		# Strip any new lines from the input
		x = fn.stripNewline(x)
		# Split string by spaces.  The 1st field is the IP address, the 2nd field is the subnet mask
		xList = x.split(" ")
		# IP address is xList[0], subnet mask is xList[1]
		if not ifn.validateIPAddress(xList[0]) or not ifn.validateSubnetMask(xList[1]):
			# IP address or subnet mask isn't valid, return False
			return False
	# All IP addresses and subnet masks are valid, return True
	return True

# Validates input is port number and protocol, one per line, separated by a space
# Returns True if valid, False if invalid
def validatePortProtocolUserInput(input):
	# Loop for each inputted port number and protocol
	for x in input:
		# Reduce all spacing to just a single space per section
		x = fn.replaceDoubleSpaces(x)
		# Strip any new lines from the input
		x = fn.stripNewline(x)
		# Split string by spaces.  The 1st field is the port, the 2nd field is the protocol
		xList = x.split(" ")
		# Port is xList[0], protocol is xList[1]
		if not ifn.validatePortNumber(xList[0]) or not ifn.validatePortProtocol(xList[1]):
			# Port number and protocol isn't valid, return False
			return False
	# All port number and protocol are valid, return True
	return True

# Tells user of invalid IP and subnet mask input, with explanation on its correct formatting
def notifyInvalidIPMaskUserInput():
	print "\n### ERROR ###\n"
	print "Invalid input detected.  Input must include one IP address and one subnet mask per line only, separated by a space."
	print "The stopword must be included by itself on the last line.\n"
	print "Example:"
	print "10.0.0.0 255.255.0.0"
	print "10.1.1.0 255.255.255.0"
	print "8.8.8.8 255.255.255.255"
	print "[stopword]\n"

def notifyInvalidPortProtocolUserInput():
	print "\n### ERROR ###\n"
	print "Invalid input detected.  Input must include one port number and its protocol type per line only, separated by a space."
	print "The stopword must be included by itself on the last line."
	print "Valid port range is between 1 and 65535."
	print "Valid protocols supported: TCP or UDP only.\n"
	print "Example:"
	print "80 TCP"
	print "161 UDP"
	print "[stopword]\n"


# Get credentials from user if not already set
user, pw = ufn.getUserCredentials(user, pw)
# Store user credentials in creds class
creds = fn.setUserCredentials(user, pw)

# Save SSH username as userInitials for now, until implemented later
#userInitials = creds.un

# Set up the SSH session now, prints an error and closes the script if the SSH connection fails
ssh = nfn.getSSHSession(deviceType, hostFW, creds)

# If outputFileName not predefined, ask user for filename
outputFileName = outputDirectory + ufn.userGetOutputFileName(outputFileName)

# Get change ticket number from user
changeTicket = raw_input("What is the change ticket associated with this firewall change? ")
# Strip new lines from user input
changeTicket = fn.stripNewline(changeTicket)

# Ask user for description on the above IP addresses
print "\nDescribe this ticket and the source/dest IP addresses in 1 or 2 words only."
srcDesc = raw_input("This will be used for naming the different ACL groupings for this change: ")
# Strip any new lines from the input
srcDesc = fn.stripNewline(srcDesc)
# Replace any white space the user entered with underscores
srcDesc = fn.replaceSpacesWithUnderscore(srcDesc)

# Loop to validate user input
while True:
	# Text to tell user what type of input we are looking for
	typeOfInput = "All source IP addresses and their subnet mask, separated by space (ex: 10.1.2.3 255.255.255.255)"
	# Get user input for all source IP addresses, store in string
	sourceInput = fn.getCustomInput(typeOfInput, False)
	# If validation checks pass, break out of loop
	if validateIPMaskUserInput(sourceInput):
		break
	# Otherwise notify user and try again
	else:
		notifyInvalidIPMaskUserInput()
		continue

# Loop to validate user input
while True:
	# Text to tell user what type of input we are looking for
	typeOfInput = "All destination IP addresses and their subnet mask, separated by space (ex: 10.1.2.3 255.255.255.255)"
	# Get user input for all source IP addresses, store in string
	destInput = fn.getCustomInput(typeOfInput, False)
	# If validation checks pass, break out of loop
	if validateIPMaskUserInput(destInput):
		break
	# Otherwise notify user and try again
	else:
		notifyInvalidIPMaskUserInput()
		continue

# Loop to validate user input
while True:
	# Text to tell user what type of input we are looking for
	typeOfInput = "All destination ports followed by if they're TCP or UDP, separated by space (ex: 80 TCP)"
	# Get user input for all source IP addresses, store in string
	portInput = fn.getCustomInput(typeOfInput, False)
	# If validation checks pass, break out of loop
	if validatePortProtocolUserInput(portInput):
		break
	# Otherwise notify user and try again
	else:
		notifyInvalidPortProtocolUserInput()
		continue

# Let user know the script is running and hasn't hung up
print "Working, please standby...\n"

###########
# Need to add validation checks to above input
###########

# Counter for number of source IP's
i = 0

################################################################################
### Section - Sort through all Source IP addresses and subnet masks provided ###
################################################################################

# Loop for each inputted source IP address and subnet mask
for source in sourceInput:
	# Increment counter for number of source IP's submitted
	i += 1

	# Reduce all spacing to just a single space per section
	source = fn.replaceDoubleSpaces(source)
	# Split string by spaces.  The 1st field is the IP address, the 2nd field is the subnet mask
	sourceList = source.split(" ")

	# Needed to preserve user provided source in below loop, and be able to change these Cmd varables without affecting original user input
	# IP address
	sourceIPCmd = sourceList[0]
	# Subnet mask
	sourceMaskCmd = sourceList[1]

	# Loop once only in case initial source isn't in ASA routing table, then search for default route
	for k in range(2):
		# Command to check for interface source would originate from
		command = "show route %s | inc via" % (sourceIPCmd)
		# Get result of above command when run on the firewall
		result = nfn.runSSHCommandInSession(command, ssh)

		# This is blank if it isn't in the routing table; AKA check for default route next
		if fn.isEmpty(result):
			sourceIPCmd = "0.0.0.0"
			continue
		else:
			break

	# Split returned results by line
	result = result.split("\n")
	# Store last line of list into a new string variable
	resultStr = result[-1]
	# Reduce all spacing to just a single space per section
	resultStr = fn.replaceDoubleSpaces(resultStr)
	# Split string by spaces.  We are looking for the last field
	resultList = resultStr.split(" ")
	# Save interface name (value) source IP address (key) is found on in dictionary for reference later
	sourceIPIntDict[sourceList[0]] = resultList[-1]
	# Save IP address (key) and matching subnet mask (value) to separate dictionary for later reference
	sourceIPMaskDict[sourceList[0]] = sourceList[1]

################
### /Section ###
################



#########################################################################################################################################
### Section - Add each IP address to the same object-group if they all use the same interface, othewise create separate OG's for each ###
#########################################################################################################################################

# Loop counter for number of source IP's in original input
m = 0
# Loop counter for number of source IP's that do NOT originate from the same interface
n = 0

# If there's more than one source IP address, check if any/all of the source IP's originate from the same interface, group them in an object group
if i > 0:
	# Loop for each IP listed, retrieved from previous loop
	while True:
		# Reset dict variable
		varDict = dict()
		# There are IP's with different source interfaces in provided input, and this is the first loop iteration
		if n == 0 and not ranOnce:
			varDict = sourceIPMaskDict

		elif n > 0:
			# Reset this counter
			m = 0
			# Reset duplicate IP to interface loop counter
			n = 0
			# Store duplicate variable in here to run again
			varDict = duplicateSourceIPMaskDict
			# Rest this variable
			duplicateSourceIPMaskDict = dict()

		else:
			# Reset variable for future use
			ranOnce = False
			# Break from While loop
			break

		# Config to create object-group for source IP addresses with description
		configCommandsList, newOGName = fwn.addConfigNewOG('network', 's', changeTicket, userInitials, srcDesc, newSrcOGCounter, configCommandsList)
		# Increment counter to keep track of number of source object-groups
		newSrcOGCounter += 1

		# varDict is always the IP address and subnet mask inputs
		for key, value in varDict.iteritems():
			# Do this on the first iteration only
			if m == 0:
				# Get object-group config line for this host
				configCommandsList = fwn.addConfigNetworkOGLine(key, value, configCommandsList)

				# Store first host added to OG in this variable, to compare to the rest
				sourceOriginal = key

				# Find ACL applied to relevant interface via access-group
				commandAG = "show run access-group | inc interface %s" % (sourceIPIntDict[key])
				# Run command on ASA, save output
				groupResult = nfn.runSSHCommandInSession(commandAG, ssh)
				# interface is last string, separated by spaces

				# Reduce all spacing to just a single space per section
				groupResult = fn.replaceDoubleSpaces(groupResult)
				# Split string by spaces.  We are looking for the 4th field
				groupResultList = groupResult.split(" ")

				# Store ACL Name in dictionary as a value, where the IP address is the key
				intToACLDict[key] = groupResultList[1]

				# Save object-group name to dictionary
				srcOGNameDict[key] = newOGName

			# If not first loop iteration, verify each added host originates from the same source interface on the firewall
			else:
				# If the current source IP address uses the same interface as the first one added, add to the same OG
				if sourceIPIntDict[key] == sourceIPIntDict[sourceOriginal]:
					# Get object-group config line for this host
					configCommandsList = fwn.addConfigNetworkOGLine(key, value, configCommandsList)

				# Otherwise, increment counter for every source IP that is NOT on the same interface as the first one listed
				else:
					# Increment counter for IP's without the same source interface
					n += 1
					# Store IP address and its corresponding interface in the duplicate-tracking variable
					duplicateSourceIPMaskDict[key] = value
			m += 1

		# Add 'exit' to end of configCommandsList once this object-group is done being configured
		configCommandsList.append(" exit")
		# Save variable to know we've successfully completed one loop iteration
		ranOnce = True

################
### /Section ###
################



#####################################################################################
### Section - Sort through all Destination IP addresses and subnet masks provided ###
#####################################################################################

# Counter for number of destination IP's
j = 0
# Loop for each inputted destination IP address and subnet mask
for dest in destInput:
	# Increment counter for number of destination IP's submitted
	j += 1

	# Reduce all spacing to just a single space per section
	dest = fn.replaceDoubleSpaces(dest)
	# Split string by spaces.  The 1st field is the IP address, the 2nd field is the subnet mask
	destList = dest.split(" ")

	# Save IP address and matching subnet mask to separate dictionary for later reference
	destIPMaskDict[destList[0]] = destList[1]


# If there's more than one destination IP address, add to an object-group
if j > 0:
	# Config to create object-group for destination IP addresses with description
	configCommandsList, dstOGName = fwn.addConfigNewOG('network', 'd', changeTicket, userInitials, srcDesc, 0, configCommandsList)

	# Add each destination IP and mask to the object-group
	for key, value in destIPMaskDict.iteritems():
		# Get object-group config line for this host
		configCommands = fwn.addConfigNetworkOGLine(key, value, configCommandsList)

	# Add 'exit' to end of configCommandsList once this object-group is done being configured
	configCommandsList.append(" exit")

################
### /Section ###
################


#####################################################################
### Section - Sort through all ports and their protocols provided ###
#####################################################################

# Counter for number of ports and their protocols's
k = 0
# Loop for each inputted port and protocol
for port in portInput:
	# Increment counter for number of destination IP's submitted
	k += 1

	# Reduce all spacing to just a single space per section
	port = fn.replaceDoubleSpaces(port)
	# Split string by spaces.  The 1st field is the port, the 2nd field is the protocol
	portList = port.split(" ")

	# Save port and matching protocol to separate dictionary for later reference
	portDict[portList[0]] = portList[1]

# If there's more than one port, add to an object-group
if k > 0:
	# Config to create object-group with description
	configCommandsList, portOGName = fwn.addConfigNewOG('service', 'd', changeTicket, userInitials, srcDesc, 0, configCommandsList)

	# Add each destination IP and mask to the object-group
	for key, value in portDict.iteritems():
		# Get object-group config line for this host
		configCommandsList = fwn.addConfigServiceOGLine(key, value, 'd', configCommandsList)

	# Add 'exit' to end of configCommands once this object-group is done being configured
	configCommandsList.append(" exit")

################
### /Section ###
################



######################################################
### Section - Check if access is currently allowed ###
######################################################

# For each source address provided, loop
for sIP, sM in sourceIPMaskDict.iteritems():
	# If subnet mask is anything except '255.255.255.255', it's a range, so add 1 and use that as the host (for testing only)
	if not ifn.isSubnetMaskAHost(sM):
		# Increment source IP by 1
		sIPNew = ifn.incrementIPByOne(sIP)
	# Otherwise save source IP in the variable, to prevent error later if variable is not defined
	else:
		sIPNew = sIP
	# Counter for destination IP loop tracking
	i = 0
	# For each destination address provided, loop
	for dIP, dM in destIPMaskDict.iteritems():
		# If subnet mask is anything except '255.255.255.255', it's a range, so add 1 and use that as the host (for testing only)
		if not ifn.isSubnetMaskAHost(dM):
			dIP = ifn.incrementIPByOne(dIP)
		# Counter for port/protocol loop tracking
		j = 0
		# For each port provided, loop
		for port, proto in portDict.iteritems():
			# Send source interface, source IP, destination IP, port, protocol, and ssh session to test if this access is already allowed
			accessCheckResult, accessCheckReason = fwn.checkAccessThroughACL(sourceIPIntDict[sIP], sIPNew, dIP, port, proto, ssh)
			# If access is currently allowed, skip it and notify user
			if accessCheckResult:
				print "Access is already allowed from %s to %s on port %s %s" % (sIP, dIP, proto.upper(), port)
				# Increment counter for ports
				j += 1
		# If all ports in portDict are found to be allowed to this destination IP address, increment counter 'i'
		if j == len(portDict):
			# Increment counter for destination IP's
			i += 1
	# If this specific source IP can already reach every destination provided on every port provided, remove it from the source IP object-group and notify user
	# If every port is already open for this specific source to this specific destination, remove it from the object-group
	if i == len(destIPMaskDict):
		print "%s can already access all provided destination IP addresses on all provided ports.  This source will be skipped from the config.\n" % (sIP)

		# Remove sIP object from its relative OG.  Enter 'if' statement if it's parent OG was also deleted
		if fwn.removeNetworkLineFromOG(sIP, sM, configCommandsList):
			# Interface name found from sourceIPIntDict, where the source IP address is the key
			# If multiple IP's from the same source interface both have full access already, only one of the IP's will be listed
			#	Therefore ignore and exceptions and continue here
			try:
				# Delete the interface/ACL from the intToACLDict variable
				del intToACLDict[sIP]
				# Delete the interface and associated OG name from the srcOGNameDict variable
				del srcOGNameDict[sIP]
			except:
				pass
			# Same as above 'try/except' statement
			try:
				# Delete the interface and associated OG name from the srcOGNameDict variable
				del srcOGNameDict[sIP]
			except:
				pass

################
### /Section ###
################

'''
At this point we should have, and will need, the following:
	srcOGNameDict (dict) - key is the source IP address, value is the name of the object-group with the source IP addresses for use on that interface's ACL
	dstOGName (string) - name of destination object-group
	portOGName (string) - name of ports object-group
	sourceIPMaskDict (dict) - key is the source IP address, value is the matching subnet mask
	destIPMaskDict (dict) - key is the destination IP address, value is the matching subnet mask
	portDict (dict) - key is the port, value is the matching protocol
	intToACLDict (dict) - key is the source IP address, value is the ACL name tied to its interface
	sourceIPIntDict (dict) - key is the source IP address, value is the interface used for that source IP address
	newSrcOGCounter (int) - counter with the total number of object-groups for the source IP's
	configCommandsList (list) - list containing all configs to execute on the ASA for this change so far
	userInitials (string) - user intials or username (if initials not provided) used to create configure this change
	changeTicket (string) - change ticket associated with this change
'''

# If intToACLDict is empty, then all access requested is already allowed through the firewall. Notify user and exit script
if fn.isEmpty(intToACLDict):
	print "\nAll requested access is currently permitted through the firewall.  No configuration changes are needed."
	fn.debugScript("Exiting script with no configuration changes made.\n")

# Key is interface, value is ACL name for that interface
for key, value in intToACLDict.iteritems():
	# Get name of source object-group tied to this interface we're using in this loop iteration
	srcOGName = srcOGNameDict[key]
	# Configure the ACL remark for this interface
	commandRemark = "access-list %s remark Allow access for %s on necessary ports - (%s %s)" % (value, srcDesc,  userInitials, changeTicket)
	# Configure the ACL for this interface
	commandAclLine = "access-list %s extended permit object-group %s object-group %s object-group %s log" % (value, portOGName, srcOGName, dstOGName)

	# Add the remark and permissions line to the end of configCommandsList
	configCommandsList.append(commandRemark)
	configCommandsList.append(commandAclLine)

# Add backing out and saving config
configCommandsList.append("end")
configCommandsList.append("wr mem")

# Display configuration commands to user
print "\n\n"
for x in configCommandsList:
	print x
print "\n\n"

while True:
	userConfirm = raw_input("Confirm these configs are correct before execution (y/n): ")
	# Check to see if entered value is 'y' or 'n' only
	if userConfirm != 'y' and userConfirm != 'n':
		print "\nPlease enter \"y\" or \"n\" only."
		# Loop again
		continue
	elif userConfirm == 'n':
		# Save notification to 'result' for the log later
		result = "\nExiting script without making any configuration changes.\n"
		# Display notification to user that the script exited and didn't make any changes
		print result
		# Break out of While loop
		break
	elif userConfirm == 'y':
		# Execute all commands set on firewall
		result = nfn.runMultipleSSHCommandsInSession(configCommandsList, ssh)
		# Notify user it was successful
		print "Commands executed on %s firewall.\n" % (hostFW)

		# Get timestamp for log file
		timeStamp = '{:%b-%d-%Y %H:%M:%S}'.format(datetime.datetime.now())
		# Create/overwrite file, and add header to top
		headerStr = "Firewall scripted change - Ticket %s - Run by user %s at %s\n" % (changeTicket, creds.un, timeStamp)
		fn.writeCommandToFile(headerStr, outputFileName)
		# Save configuration commands created by script to new file/overwrite existing file
		for x in configCommandsList:
			# Add carriage return to end of each string
			x = x + "\n"
			fn.appendCommandToFile(x, outputFileName)
		# Save results from command execution to end of log file
		fn.appendCommandToFile(result, outputFileName)

		# Break out of While loop
		break
	# Mainly used for debugging.  This should never trigger
	else:
		print "ERROR: Loop asking user to confirm command execution failed with unknown error."
		break

# Disconnect SSH session once script is completed
nfn.disconnectFromSSH(ssh)
