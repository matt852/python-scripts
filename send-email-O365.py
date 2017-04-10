#!/usr/bin/python

#################################################################################################
# Use: Send a mass email to multiple users with the same email message							#
# Input: CSV file with two fields per device, separated by a comma.								#
#			Column 1: Email address																#
#			Column 2: Recipient's Name															#
# Output: All info is outputted to screen.  No files are saved									#
# Pip install: O365																				#
#################################################################################################

import O365 as o3
import lib.functions as fn
import lib.user_functions as ufn

### Variables ###
# User credentials
user = ''												# Add your username here if desired
pw = ''													# Add your password here if desired
emailList = 'emaillist.txt'								# List of user email address and names in CSV format
inputDirectory = 'textfiles/'							# File directory for any data files used by this script

# Get credentials from user if not already set
user, pw = ufn.getUserCredentials(user, pw)
# Store user credentials in creds class
creds = fn.setUserCredentials(user, pw)

# If emailList not predefined, ask user for filename.  Prepend with input directory
emailList = inputDirectory + ufn.userGetFileName(emailList, '')

# Store user credentials in 'authentication' variable
authenticiation = (creds.un, creds.pw)
# Start O365 session with credentials
m = o3.Message(auth=authenticiation)


# Import file contents
fileLines = fn.readFromFile(emailList)

# Count how many email addresses are in the import file
emailCount = fn.file_len(emailList)

# Get current time for later calculations on how long script took to run
startTime = fn.getCurrentTime()

# Counter for progress bar
i = 0
# Progress bar for each email address listed in file
fn.printProgress(i, emailCount, prefix = 'Progress:', suffix = 'Complete')

# For each line extracted from the file, loop
for line in fileLines:
	# Split each line on whitespace
	line = line.split(',')
	# Set email address and recipient name
	emailAddr = line[0]
	emailRecipient = line[1]
	# Strip new lines from email address and recipient name, if any
	emailAddr = fn.stripNewline(emailAddr)
	emailRecipient = fn.stripNewline(emailRecipient)

	# Set the email address as the recipient
	m.setRecipients(emailAddr)
	# Set the email subject
	m.setSubject('Email script test %s' % (i+1))

	# Set the body of text here
	m.setBody("""Dear %s,\n
This is an example of a generic email being sent out.\n
This is the whole email #%s.\n
Sincerely,\n
\n
%s""" % (emailRecipient, i+1, creds.un))
	# Send the message
	m.sendMessage()
	# Increment progress bar counter
	i += 1
	# Progress bar for each switch listed in file
	fn.printProgress(i, emailCount, prefix = 'Progress:', suffix = 'Complete')


# Print elapsed time for running script
print "\nTotal elapsed time to complete script:"
print fn.getScriptRunTime(startTime)
print "\n"
