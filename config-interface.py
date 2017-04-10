#!/usr/bin/python

#################################################################################################
# Use: Configure a provided interface on a provided switch with various config settings			#
# Input: All input is provided via CLI during script execution									#
# Output: All info is outputted to screen.  No files are saved									#
# To do: add status check (up or down) to interface when pulling config							#
#################################################################################################

import pdb 			# Set breakpoints in script for debugging with this line: pdb.set_trace()
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
user = ''										# Add your username here if desired
pw = ''											# Add your password here if desired
# Script variables
### /Variables ###


# Get credentials from user if not already set
user, pw = ufn.getUserCredentials(user, pw)
# Store user credentials in creds class
creds = fn.setUserCredentials(user, pw)


host = raw_input("What switch is the interface on? ")
iface = raw_input("What interface do you want to configure? ")

print "\n\nConfig settings for interface %s on %s:" % (iface, host)

command = "show run int %s | ex configuration|!" % (iface)
# Print existing configuration settings for interface
print sfn.runSSHCommand(command, host, creds)
print "\n"

# Loop menu in case invalid option is selected
while True:
	# Loop menu in case incorrect option is selected, and user declines confirming menu option
	while True:
		print "\n"
		print "Troubleshooting Menu for interface %s\n" % (iface)
		print "1) Bounce port"
		print "2) Shutdown port"
		print "3) Enable port"
		print "4) Change data vlan on port"
		print "5) Change voice vlan on port"
		print "6) Clear authentication sessions on port"
		print "7) Erase port config"
		print "9) Exit menu\n"
		menuChoice = raw_input("Choose a menu option: ")

		# If menu choice is anything but 9 (exit menu), confirm with user
		if fn.isEmpty(menuChoice):
			print "\nInvalid menu option selected\n"
			mainMenuChoice = ''
			continue

		elif menuChoice != '9':
			menuConfirm = raw_input("Confirm menu choice of %s (y/n): " % (menuChoice))

			# Check to see if entered value is 'y' or 'n' only
			if menuConfirm != 'y' and menuConfirm != 'n':
				print "\nPlease enter \"y\" or \"n\" only."
				continue
			elif menuConfirm == 'n':
				continue
			elif menuConfirm == 'y':
				break
			# Mainly used for debugging.  This should never trigger
			else:
				fn.debugErrorOut('101')
		# Menu option is 9, so break initial menu selection loop
		else:
			break

	# Execute commands based off menu choice
	if menuChoice == '9':
		print "\nExiting script\n"
		sys.exit()

	elif menuChoice == '1':
		output = sfn.bounceSSHInterface(host, iface, creds)
		print "\nInterface %s on host %s has been bounced\n" % (iface, host)
		break

	elif menuChoice == '2':
		command = "shutdown"
		output = sfn.runSSHInterfaceCommand(command, host, iface, creds)
		print "\nInterface %s on host %s has been disabled\n" % (iface, host)
		break

	elif menuChoice == '3':
		command = "no shutdown"
		output = sfn.runSSHInterfaceCommand(command, host, iface, creds)
		print "\nInterface %s on host %s has been enabled\n" % (iface, host)
		break

	elif menuChoice == '4' or menuChoice == '5':
		if menuChoice == '4':
			choiceType = 'data'
			choiceTypeCmd = 'access'
		elif menuChoice == '5':
			choiceType = 'voice'
			choiceTypeCmd = 'voice'
		# Mainly used for debugging.  This should never trigger
		else:
			fn.debugErrorOut('102')

		while True:
			vlan = raw_input("Enter new %s vlan: " % (choiceType))
			command = "switchport %s vlan %s" % (choiceTypeCmd, vlan)
			menuConfirm = raw_input("Confirm %s vlan is %s (y/n): " % (choiceType, vlan))

			# Check to see if entered value is 'y' or 'n' only
			if menuConfirm != 'y' and menuConfirm != 'n':
				print "\nPlease enter \"y\" or \"n\" only."
				continue
			elif menuConfirm == 'n':
				continue
			elif menuConfirm == 'y':
				break
			# Mainly used for debugging.  This should never trigger
			else:
				fn.debugErrorOut('103')

		output = sfn.runSSHInterfaceCommand(command, host, iface, creds)
		print "\nInterface %s on host %s has been configured for %s vlan %s\n" % (iface, host, choiceTypeCmd, vlan)

		output = sfn.askUserBounceInt(host, iface, vlan, creds)
		print "\nInterface %s on host %s has been bounced\n" % (iface, host)
		break

	elif menuChoice == '6':
		command = "clear authentication sessions interface %s" % (iface)
		output = sfn.runSSHCommand(command, host, creds)
		print "\nAuthentication sessions have been cleared for interface %s on host %s\n" % (iface, host)
		break

	elif menuChoice == '7':
		while True:
			wipeConfirm = raw_input("\nConfirm wiping config for interface %s on switch %s (y/n) " % (iface, host))
			# Check to see if entered value is 'y' or 'n' only
			if wipeConfirm != 'y' and wipeConfirm != 'n':
				print "\nPlease enter \"y\" or \"n\" only."
				continue
			elif wipeConfirm == 'n':
				print "Exiting script without making any changes.\n"
				sys.exit()
			elif wipeConfirm == 'y':
				command = "default interface %s" % (iface)
				output = sfn.runSSHConfigCommand(command, host, creds)
				break
			# Mainly used for debugging.  This should never trigger
			else:
				fn.debugErrorOut('119')

		print "\n"
		print "\nConfiguration settings have been wiped for interface %s on switch %s.\n" % (iface, host)
		break

	else:
		print "\nInvalid menu option selected\n"
		continue
