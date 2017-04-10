#!/usr/bin/python

#################################################################################################
# Use: Search for host endpoint on network by MAC or IP address									#
# Input: All input is done via CLI on the screen												#
# Output: All info is outputted to screen.  No files are saved									#
#																								#
# Untested for fiber-channel, Cisco blades for HP chassis, and non-Cisco switches				#
#																								#
# Error for MAC/IP lookup if device is a server connected to 2 separate Nexus 5k's				#
#	via VPC/Port-channel.  Then the client lookup detects it on a port channel, when it's		#
#	really directly connected to the 5k's														#
#																								#
# Also fails if searching for an IP with multiple returned results								#
# 	Example: 10.0.0.24 returns 10.0.0.24 and 10.0.0.241, 242, 243, etc							#
#																								#
# Bug1: add check at line if host == hostCoreSW: to instead detect if switch is NX-OS or IOS	#
# Bug2: Authentication information shows the next line "data domain" when it shouldn't,			#
#	even if there isn't any auth info on the port.  this is due to an MOTD banner being			#
#	configured.  login banner alone works OK													#
#################################################################################################

import inspect
import subprocess
import re
import socket
import sys
import os
import paramiko as pm
import lib.functions as fn
import lib.user_functions as ufn
import lib.ssh_functions as sfn
from collections import defaultdict
from time import sleep

### Variables ###
# User credentials
user = ''												# Add your username here if desired
pw = ''													# Add your password here if desired
# Script variables
host = ''												# Host variable used for storing which host/switch to search for a user on currently
hostCoreSW = '10.x.x.x'									# Add the starting core switch here
#hostCoreASA = '10.x.x.x'								# Add a firewall here if one may host any potential vlans; still a WIP
hostHops = []											# Variable for storing each hop in path from core to end host (when searching for a client)
hostHopsPorts = []										# Variable for storing the interface on each hop in path from core to end host (when searching for a client)
wifiClient = False										# Variable to determine if client looked up is on wifi; initialize as False
d = defaultdict(list)									# Create new empty dictonary for storing the auth class
authClassVar = IntAuthResult('', '', '', '')			# Create new auth class instance
# ISE authentication variables
authVoiceDomain = False
authVoiceUser = ''
authVoiceStatus = ''
authVoiceType = ''
### /Variables ###

# Class for storing interface authentication session results when searching for a client on the network
class IntAuthResult(object):
	# Results for an interface's authentication status
	def __init__(self, user, domain, status, authtype):
		self.user = user
		self.domain = domain
		self.status = status
		self.authtype = authtype

# Returns IP address assigned to provided MAC address
def findIpByMac(addr, host):
	# Find what the IP address is associated with the provided MAC address
	showArp = "show ip arp | include "
	command = showArp + addr
	# Run command, save output to 'result'
	result = sfn.runSSHCommand(command, host, creds)

	# If MAC address isn't in ARP table, or listed as Incomplete, check a firewall to see if its hosted there
	if fn.errorCheckEmptyIncResult(result):
		# Currently not fully implemented yet
		'''showArp = "show arp | include "
		command = showArp + addr
		host = hostCoreASA
		asaClient = True'''

		if asaClient:
			result = sfn.runSSHCommandASA(command, host, creds)
		# If MAC address isn't in ARP table, or listed as Incomplete, exit script
		if fn.errorCheckEmptyIncResult(result):
			print "Client MAC address is not found on the core switch or internal ASA.  Error #201.  Please try again"
			fn.debugErrorOut('201')

		# Split result into list split by newlines
		result = result.splitlines()
		# Replace everywhere with multiple spaces with only a single space
		result = fn.replaceDoubleSpaces(result[-3])

		# Split result by individual spaces
		result = result.split(" ")
		# If MAC address isn't in ARP table, or listed as Incomplete, exit script
		if fn.errorCheckEmptyIncResult(result[2]):
			print "Client MAC address is not found.  Error #202.  Please try again"
			fn.debugScript('202')
		# Otherwise, return MAC address found from ARP table
		else:
			if result[2] == "arp":
				print "Client IP address is identified as as on the firewall but cannot be found on it.  Error #203.  Please try again"
				fn.debugScript('203')
			else:
				return result[1]
	else:
		# Replace everywhere with multiple spaces with only a single space
		result = fn.replaceDoubleSpaces(result)
		# Split result by individual spaces
		clientIPAddr = result.split(" ")
		# If MAC address isn't in ARP table, or listed as Incomplete, exit script
		if fn.errorCheckEmptyIncResult(clientIPAddr[0]):
			print "Client IP address is not found.  Please try again"
			fn.debugScript('204')
		# Otherwise, return IP address found from ARP table
		else:
			return clientIPAddr[0]

# Returns MAC address assigned to provided IP address
def findMacbyIp(addr, host):
	# Find what the MAC address is associated with the provided IP address
	# If client IP address is on a vlan hosted on a firewall, pull MAC from firewall
	# Currently not fully implemented yet
	'''if (
			"10.x.x." in ipAddr or
			"10.x.x." in ipAddr or
			"10.x.x." in ipAddr
		):
		# Below 2 lines not used; left for future ASA support
		showArp = "show arp | include "
		host = hostCoreASA
		asaClient = True
	# If client IP address is not on a firewall-hosted vlan, pull MAC from Core
	else:
		showArp = "show ip arp | include "
		asaClient = False'''

	showArp = "show ip arp | include "
	asaClient = False
	# Set command to run for ARP table lookup
	command = showArp + addr + "\n"
	# Run command, save output to 'result'
	if asaClient:
		result = sfn.runSSHCommandASA(command, host, creds)
		# If MAC address isn't in ARP table, or listed as Incomplete, exit script
		if fn.errorCheckEmptyIncResult(result):
			print "Client IP address is not found on the core switch or the ASA.  Error #301.  Please try again"
			fn.debugScript('301')
		# Split result into list split by newlines
		result = result.splitlines()
		# Replace everywhere with multiple spaces with only a single space
		result = fn.replaceDoubleSpaces(result[-3])
	else:
		result = sfn.runSSHCommand(command, host, creds)
		# If MAC address isn't in ARP table, or listed as Incomplete, exit script
		if fn.errorCheckEmptyIncResult(result):
			print "Client IP address is not found in the core network.  Error #302.  Please try again"
			fn.debugScript('302')
		# Replace everywhere with multiple spaces with only a single space
		result = fn.replaceDoubleSpaces(result)
	# Split result by individual spaces
	result = result.split(" ")
	# If MAC address isn't in ARP table, or listed as Incomplete, exit script
	if fn.errorCheckEmptyIncResult(result[2]):
		print "Client MAC address is not found.  Please try again"
		sys.exit()
	# Otherwise, return MAC address found from ARP table
	else:
		if result[2] == "arp":
			print "Client IP address is identified as on the firewall but cannot be found on it.  Error #303.  Please try again"
			fn.debugScript('303')
		else:
			return result[2]


# Get credentials from user if not already set
user, pw = ufn.getUserCredentials(user, pw)
# Store user credentials in creds class
creds = fn.setUserCredentials(user, pw)

# Get host core switch/starting gateway from user if not already set
host = ufn.userGetCoreSW(hostCoreSW)

while True:
	q = raw_input("Lookup by MAC or IP address? (mac/ip) ")
	# Check to see if entered value is 'mac' or 'ip' only
	if q != 'mac' and q != 'ip':
		print "Please enter \"mac\" or \"ip\" only\n"
		continue
	else:
		break

# If user is searching by MAC address, get it from user, then lookup its assigned IP address
if q == 'mac':
	while True:
		# Get MAC address to search for from user
		macAddr = raw_input("What is the MAC address you are looking for? ")
		# Check to see if entered value is empty or not
		if fn.isEmpty(macAddr):
			print "Please enter in a non-empty value for the MAC address\n"
			continue
		# If MAC address is in decimal format, return 'd'
		elif fn.macFormatType(macAddr) == "d":
			# This is what we want.  Break loop and continue
			break
		# If MAC address is in colon or hyphen format, return 'c' or 'h' (respectively)
		elif fn.macFormatType(macAddr) == "c" or fn.macFormatType(macAddr) == "h":
			macAddr = fn.convertMacFormatCol2Dec(macAddr)
			break
		# If MAC address is in text format, return 't'
		elif fn.macFormatType(macAddr) == "t":
			macAddr = fn.convertMacFormatText2Dec(macAddr)
			break
		# If MAC address is in none of the required formats loop and ask again
		else:
			print "Invalid MAC address format\n"
			continue
	# Find IP address assigned to provided MAC address
	ipAddr = findIpByMac(macAddr, host)

# If user is searching by IP address, get it from user, then lookup the MAC address assigned to it
elif q == 'ip':
	while True:
		# Get IP address to search for from user
		ipAddr = raw_input("What is the IP address you are looking for? (x.x.x.x) ")
		# Check to see if entered value is empty or not
		if fn.isEmpty(ipAddr):
			print "Please enter in a non-empty value for the IP address\n"
			continue
		else:
			break
	# Find MAC address assigned to provided IP address
	macAddr = findMacbyIp(ipAddr, host)

else:
	# This should never trigger
	fn.debugErrorOut('101')

# Find what switch the given MAC address is on
while True:
	# Set to run twice.  If first MAC address lookup fails, script will ping the IP to force the MAC address to
	#  populate in the MAC table, then rechecks MAC table
	for a in range(0,2):
		showMac = "show mac address-table | include %s" % (macAddr)

		# Run 1st command, save output to 'result'
		result = sfn.runSSHCommand(showMac, host, creds)
		# If outputList is empty, ping IP address from switch and recheck MAC address table (to force it to populate)
		if not result:
			commandPing = "ping " + ipAddr
			sfn.runSSHCommand(commandPing, host, creds)
			time.sleep(1)
			a += 1
		else:
			# Break from 'for' loop
			break
	# Replace everywhere with multiple spaces with only a single space
	result1 = fn.replaceDoubleSpaces(result)
	# Split result by individual spaces
	outputList = result1.split(" ")

	# Set last index for outputList to 2nd from last if last index is empty
	# Needed for variations in the MAC Address Table output between IOS and IOS-XE/NX-OS
	try:
		i = fn.indexLookup(outputList[-1])
	except ValueError:
		fn.debugErrorOut('102')

	iface = outputList[i]

	# if MAC not found on core host/switch, error is thrown here:
	# Traceback (most recent call last):
	#  File "device-lookup.py", line 262, in <module>
	#    iface = outputList[i]
	#IndexError: list index out of range

	print "Searching..."
	hostHops.append(host)
	hostHopsPorts.append(iface)

	# If device shows up as on a Port-channel interface, assume it's on another switch
	if ("Po" in iface):
		# Device is on another switch by MAC address table

		# poAbbrev is "Po12" for the port-channel
		poAbbrev = iface.replace("rt-channel", "")
		# poNumber is just the number of the port channel
		poNumber = poAbbrev.replace("Po", "")
		# Command to find neighboring switch's interface it's connected on
		# Different commands if NX-OS vs IOS/IOS-XE
		if host == hostCoreSW:
			command2 = "show port-channel summary interface port-channel %s | i %s" % (poNumber, poAbbrev)
		else:
			command2 = "show etherchannel %s summary | include %s" % (poNumber, poAbbrev)
		# Run 2nd command, save output to 'result'
		result = sfn.runSSHCommand(command2, host, creds)

		# Reduce all spacing to just a single space per section
		result2 = fn.replaceDoubleSpaces(result)

		# Split string by spaces.  We are looking for the 4th field
		portChannelList = result2.split(" ")
		# Set last index for iface to 2nd from last if last index is empty
		# Needed for variations in the MAC Address Table output between IOS and IOS-XE/NX-OS
		i = fn.indexLookup(portChannelList[-1])
		iface = portChannelList[i]
		# Remove parentheses and everything in them using a regex
		# portChannelInt is the interface where the neighboring switch can be found for the MAC address
		portChannelInt = re.sub(r'\([^)]*\)', '', portChannelList[i])

		# Find IP address for switch where MAC address can be found off of
		# Different commands if NX-OS vs IOS/IOS-XE
		if host == hostCoreSW:
			command3 = "show cdp neighbors interface %s detail | inc \"IPv4 Address\"" % (portChannelInt)
		else:
			command3 = "show cdp neighbors %s detail | inc IP address" % (portChannelInt)

		# Run 3rd command, save output to 'result'
		result = sfn.runSSHCommand(command3, host, creds)

		# Reduce all spacing to just a single space per section
		result3 = fn.replaceDoubleSpaces(result)
		# Split string by spaces.  We are looking for the 4th field
		ipAddressList = result3.split(" ")
		# Strip any newlines from the string, store as new host
		host = fn.stripNewline(ipAddressList[3])
		continue

	# If device shows up as on a TenGigabitEthernet interface, assume it's on another switch
	elif ("Te" in iface):
		# Device is on another switch by MAC address table

		# teAbbrev is "Te5/1" for the TenGigabitEthernet interface
		teAbbrev = iface.replace("nGigabitEthernet", "")

		# Find IP address for switch where MAC address can be found off of
		# Different commands if NX-OS vs IOS/IOS-XE
		if host == hostCoreSW:
			command2 = "show cdp neighbors interface %s detail | inc \"IPv4 Address\"" % (teAbbrev)
		else:
			command2 = "show cdp neighbors %s detail | inc IP address" % (teAbbrev)

		# Run 2nd command, save output to 'result'
		result = sfn.runSSHCommand(command2, host, creds)

		# Reduce all spacing to just a single space per section
		result2 = fn.replaceDoubleSpaces(result)
		# Split string by spaces.  We are looking for the 4th field
		ipAddressList = result2.split(" ")
		# Strip any newlines from the string, store as new host
		host = fn.stripNewline(ipAddressList[3])

		# Check to see if client is wireless (on wireless controller)
		wifiClient, wifiNum = fn.wifiCheck(host)
		if wifiClient:
			break

		continue

	# If device shows up as on an Ethernet interface, but the switch is the starting core switch
	# that means the host is on another switch, as there shouldn't be any hosts directly plugged into the core switch
	elif ("Eth" in iface) and (host == hostCoreSW):
		# No clients should ever be plugged directly into the Core,
		# so it is assumed it's a neighbor switch not in a port-channel

		# Set CDP lookup command for NX-OS
		command2 = "show cdp neighbors interface %s detail | inc \"IPv4 Address\"" % (iface)

		# Run 2nd command, save output to 'result'
		result = sfn.runSSHCommand(command2, host, creds)

		# Reduce all spacing to just a single space per section
		result2 = fn.replaceDoubleSpaces(result)
		# Split string by spaces.  We are looking for the 4th field
		ipAddressList = result2.split(" ")
		# Strip any newlines from the string, store as new host
		host = fn.stripNewline(ipAddressList[3])

		# Check to see if client is wireless (on wireless controller)
		wifiClient, wifiNum = fn.wifiCheck(host)
		if wifiClient:
			break

		continue

	# Device is on this switch by MAC address table
	elif ("Eth" in iface) or ("Gi" in iface) or ("Fa" in iface):
		print "Found!  Compiling info, standby..."
		# Device is on this switch by MAC address table
		# Begin: Find ISE authentication status on the interface
		i = 0
		# Auth counter
		l = 0
		commandAuth = "show authentication sessions interface %s details | i Domain|User-Name|Status|Success" % (iface)
		pipeCount = commandAuth.count('|')

		resultAuth = sfn.runSSHCommand(commandAuth, host, creds)

		if resultAuth:
			resultCount = fn.textBlock_len(resultAuth.split("\n"))
			resultAuth2 = fn.replaceDoubleSpaces(resultAuth)

			for result in resultAuth2.split("\n"):
				i += 1
				k = 1
				# Increments once for each line in resultAuth2
				l += 1

				result2 = fn.replaceDoubleSpaces(result)
				resultList = result2.split(" ")
				for item in resultList:
					k += 1
					if k == pipeCount:
						if i == 1:
							authClassVar.user = item
						elif i == 2:
							authClassVar.status = item
						elif i == 3:
							authClassVar.domain = item

					elif k == pipeCount - 1 and i == 4:
						authClassVar.authtype = item

				if i == pipeCount:
					i = 0
					m = l / pipeCount
					d[m].append(authClassVar.user)
					d[m].append(authClassVar.status)
					d[m].append(authClassVar.domain)
					d[m].append(authClassVar.authtype)

			dLength = len(d)

		# End: Find ISE authentication status on the interface

		# Do a reverse DNS lookup on the host IP address
		hostName = fn.reverseDNSNetwork(host, creds)
		print "\n"
		print "Client information:"
		print "\tMAC address ...................... %s" % (fn.convertMacFormatDec2Col(macAddr))
		print "\tIP address ....................... %s\n" % (ipAddr)
		print "Host switch information:"
		print "\tSwitch name ...................... %s" % (hostName)
		print "\tSwitch IP address ................ %s" % (host)
		print "\tInterface client is found on ..... %s\n" % (iface)
		print "Authentication information:"
		if d:
			print "   Data Domain:"
			t = 1
			while t <= dLength:
				value = d[t]
				if value[2] == "VOICE":
					authVoiceDomain = True
					authVoiceUser = value[0]
					authVoiceStatus = value[1]
					authVoiceType = value[3]
				elif value[2] == "DATA":
					print "\tUser-Name ........................ %s" % (value[0])
					print "\tStatus ........................... %s" % (value[1])
					print "\tAuth Type ........................ %s\n" % (value[3])
				t += 1
			if authVoiceDomain:
				print "   Voice Domain:"
				print "\tUser-Name ........................ %s" % (authVoiceUser)
				print "\tStatus ........................... %s" % (authVoiceStatus)
				print "\tAuth Type ........................ %s" % (authVoiceType)
		else:
			print "\tNo currently active authentication sessions on this interface"

		# Show path from core to client through network as found by script
		print "\n\nNetwork path to host:"
		hostHopsCounter = 0
		while hostHopsCounter < len(hostHops):
			# Do a reverse DNS lookup on each network device in path to endpiont IP address. Display IP address of switch if reverse DNS fails
			print "%s <-- %s -----> " % (fn.reverseDNSEndpoint(hostHops[hostHopsCounter]), hostHopsPorts[hostHopsCounter].replace("Port-channel","Po")),
			hostHopsCounter += 1
		# Find hostname for IP if reverse DNS is successful and list it
		print fn.reverseDNSEndpoint(ipAddr)

		raw_input("\n\nPress Enter to continue...")

		print "\n\nConfig settings for interface %s on %s:" % (iface, hostName)
		print sfn.showIntRunConfig(host, iface, creds) + "\n"
		break
	else:
		# Mainly used for debugging.  This should never trigger
		fn.debugScript('103')
# If wireless client, skip menu and exit script
if wifiClient:
	print "\nClient is wireless %s.  Exiting script.\n" % wifiNum
	sys.exit()

# Start menu section, pause for user input
raw_input("\nPress Enter to continue...")

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
				fn.debugErrorOut('104')
		# Menu option is 9, so break initial menu selection loop
		else:
			break

	# Execute commands based off menu choice
	if menuChoice == '9':
		print "\nExiting script\n"
		sys.exit()

	elif menuChoice == '1':
		output = sfn.bounceSSHInterface(host, iface, creds)
		if output:
			print "\nInterface %s on host %s has been bounced\n" % (iface, host)
		break

	elif menuChoice == '2':
		command = "shutdown"
		output = sfn.runSSHInterfaceCommand(command, host, iface, creds)
		if output:
			print "\nInterface %s on host %s has been disabled\n" % (iface, host)
		break

	elif menuChoice == '3':
		command = "no shutdown"
		output = sfn.runSSHInterfaceCommand(command, host, iface, creds)
		if output:
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
			fn.debugErrorOut('105')

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
				fn.debugErrorOut('106')

		output = sfn.runSSHInterfaceCommand(command, host, iface, creds)
		if output:
			print "\nInterface %s on host %s has been configured for %s vlan %s\n" % (iface, host, choiceTypeCmd, vlan)

		output = sfn.askUserBounceInt(host, iface, vlan, creds)
		if output:
			print "\nInterface %s on host %s has been bounced\n" % (iface, host)
		break

	elif menuChoice == '6':
		command = "clear authentication sessions interface %s" % (iface)
		output = sfn.runSSHCommand(command, host, creds)
		if output:
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
				if output:
					print "\nConfiguration settings have been wiped for interface %s on switch %s.\n" % (iface, host)
				break
			# Mainly used for debugging.  This should never trigger
			else:
				fn.debugErrorOut('107')
		break

	else:
		print "\nInvalid menu option selected\n"
		continue
