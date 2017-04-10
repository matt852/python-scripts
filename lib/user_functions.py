#!/usr/bin/python

#####################################################################################################
# Written by v1tal3																					#
# Creation date			2-22-2016																	#
# Last modifed date		4-9-2017																	#
#####################################################################################################

import subprocess
import re
import socket
import sys
import time
import os
import getpass

# If username not previously set, ask user for it
# Only used locally within this script. Shouldn't be called from externally
def getUsername(user):
	# Loop in case user doesn't enter in a username
	while True:
		user = raw_input("Username: ")
		# Check to see if entered username is blank
		if not user:
			print "Please enter in a username\n"
			continue
		else:
			return user

# If password not previously set, ask user for it
# Only used locally within this script. Shouldn't be called from externally
def getPassword(pw):
	# Loop in case user doesn't enter in a password
	while True:
		pw = getpass.getpass()
		# Check to see if entered password is blank
		if not pw:
			print "Please enter in a password\n"
			continue
		else:
			return pw

# If credentials not previously set, ask user for input to set them
def getUserCredentials(user, pw):
	# If credentials not previously set, ask user for input to set them
	if (not user) or (not pw):
		print "Your network credentials are required"
		if not user:
			# Ask user to provide username
			user = getUsername(user)
		else:
			print "Using username saved in script."
		if not pw:
			pw = getPassword(pw)
		else:
			print "Using password saved in script."
	else:
		print "Using saved network credentials in script.\n"

	# Returns username and password
	return user, pw

# Get output file name from user if not predefined
def userGetOutputFileName(outputFileName):
	# If outputFileName not predefined, ask user for filename
	if not outputFileName:
		print "\nWhat is the filename for the output of this script once completed?"
		while True:
			# Loop in case user doesn't enter in the filename
			outputFileName = raw_input("Output filename: ")
			# Check to see if entered filename is blank
			if not outputFileName:
				print "Please enter in a filename for the output\n"
				continue
			else:
				return outputFileName
	else:
		return outputFileName

# Get output directory for saving files
def userGetOutputDirectory(outputDirectory):
	# If outputDirectory not predefined, ask user for directory
	if not outputDirectory:
		print "\nWhat is the directory (omitting / at the end) for the output files to be saved once completed?"
		while True:
			# Loop in case user doesn't enter in the directory
			outputDirectory = raw_input("Output directory: ")
			# Check to see if entered filename is blank
			if not outputDirectory:
				print "Please enter in a directory for the output files to be saved\n"
				continue
			else:
				return outputDirectory
	else:
		return outputDirectory

# If fileName not predefined, ask user for filename
# num is a string for if 1st, 2nd, etc file.  If null, assume it's the only file
def userGetFileName(fileName, num):
	if not fileName:
		if not num:
			print "\nWhat is the input filename?"
			while True:
				# Loop in case user doesn't enter in the filename
				fileName = raw_input("Filename: ")
				# Check to see if entered filename is blank
				if not fileName:
					print "Please enter in an input filename.\n"
					continue
				else:
					return fileName
		else:
			print "\nWhat is the input filename #%s?" % (num)
			while True:
				# Loop in case user doesn't enter in the filename
				fileName = raw_input("Filename: ")
				# Check to see if entered filename is blank
				if not fileName:
					print "Please enter in the #%s input filename.\n" % (num)
					continue
				else:
					return fileName

	else:
		return fileName


# Get core switch/starting gateway device from user if not predefined
def userGetCoreSW(hostCoreSW):
	# If hostCoreSW not predefined, ask user for filename
	if not hostCoreSW:
		print "\nWhat is the default gateway/core switch this script should start searching at?"
		while True:
			# Loop in case user doesn't enter in the IP address
			hostCoreSW = raw_input("Core IP address (x.x.x.x): ")
			# Check to see if entered IP address is blank
			if not hostCoreSW:
				print "Please enter in an IP address for the starting gateway/core switch\n"
				continue
			else:
				return hostCoreSW
	else:
		return hostCoreSW

# If host not previously set, ask user for input to set it
def getHost(host):
	# Loop in case host is empty
	while True:
		host = raw_input("Device host IP address: ")
		# Check to see if entered username is blank
		if not host:
			print "Please enter in an IP address\n"
			continue
		else:
			return host

# Get input directory for loading files
def userGetInputDirectory(inputDirectory):
	# If outputDirectory not predefined, ask user for directory
	if not inputDirectory:
		print "\nWhat is the directory (omitting / at the end) where the files to upload are located?"
		while True:
			# Loop in case user doesn't enter in the directory
			inputDirectory = raw_input("Upload source directory: ")
			# Check to see if entered filename is blank
			if not inputDirectory:
				print "Please enter in a directory files to upload are located."
				print "If the files are located in the same directory as this script, only enter a '.'\n"
				continue
			else:
				return inputDirectory
	else:
		return inputDirectory

# If fileName not predefined, ask user for filename
def userGetIOSImageFileName(fileName):
	if not fileName:
		print "\nWhat is the IOS image filename you want to upload?"
		while True:
			# Loop in case user doesn't enter in the filename
			fileName = raw_input("Input filename: ")
			# Check to see if entered filename is blank
			if not fileName:
				print "Please enter in a filename for the IOS image\n"
				continue
			else:
				return fileName
	else:
		return fileName

# If switchFileName not predefined, ask user for filename
def userGetSwitchFileName(switchFileName):
	if not switchFileName:
		print "\nWhat is the filename with a list of switches to search for blocked ports on?"
		while True:
			# Loop in case user doesn't enter in the filename
			switchFileName = raw_input("Host list filename: ")
			# Check to see if entered filename is blank
			if not switchFileName:
				print "Please enter in a filename for the list of switches\n"
				continue
			else:
				return switchFileName
	else:
		return switchFileName
