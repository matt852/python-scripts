#!/usr/bin/python

#################################################################################################
# Use: Backup running-config files on all imported Cisco devices								#
# Input: TXT file with a single device hostname and IP address per line							#
#			-Hostname and IP address separated by a single space								#
#			-Each device separated by carriage return											#
# Output: TXT files for each device with the running-config saved from it						#
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
inputFileName = 'devices_full.txt'						# File with a list of all IP addresses to run commands on
inputDirectory = 'textfiles/'							# File directory for any data files used by this script
outputDirectory = 'configbackups/'						# File directory with files for logging output
### /Variables ###


# Get credentials from user if not already set
user, pw = ufn.getUserCredentials(user, pw)
# Store user credentials in creds class
creds = fn.setUserCredentials(user, pw)

# If inputFileName not predefined, ask user for filename.  Prepend with input directory
inputFileName = inputDirectory + ufn.userGetFileName(inputFileName, '')


# Import file contents
fileLines = fn.readFromFile(inputFileName)
# Count how many devices are in the import file
deviceCount = fn.file_len(inputFileName)
# Tell user we are working on each device as we go
print "\nRunning script on the %s imported devices:\n" % deviceCount
# Counter for progress bar
i = 0
# Progress bar for user on device count
fn.printProgress(i, deviceCount, prefix = 'Progress:', suffix = 'Complete')
# Get current time for later calculations on how long script took to run
startTime = fn.getCurrentTime()

# Get current time in format that can be appended to file name
currentDate = time.strftime("%m-%d-%Y")
currentTime = time.strftime("%H%M")
outputDirectory = "%s/%s" % (outputDirectory, currentDate)

# Get current time for later calculations on how long script took to run
startTime = fn.getCurrentTime()

# Make new directory for the current date
fn.makeDirectory(outputDirectory)

# Loop for each listed item imported into fileLines array
for line in fileLines:
	# Strip newlines from imported devices
	line = fn.stripNewline(line)
	# Split each line on whitespace
	line = line.split(',')

	# Get running config from network device - line[1] is IP address
	commandRunConfig = sfn.runSSHCommand("show run", line[1], creds)

	# Save pulled running-config to file as a backup - line[0] is hostname
	backupFileName = "%s/%s_%s.txt" % (outputDirectory, line[0], currentTime)
	fn.writeCommandToFile(commandRunConfig, backupFileName)

	# Increment progress bar counter
	i += 1
	# Progress bar for user on device count
	fn.printProgress(i, deviceCount, prefix = 'Progress:', suffix = 'Complete')

# Print elapsed time for running script
print "\nTotal elapsed time to complete script:"
print fn.getScriptRunTime(startTime)
print "\n"
