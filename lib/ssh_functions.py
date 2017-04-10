#!/usr/bin/python

#####################################################################################################
# Written by v1tal3																					#
# Creation date			2-22-2016																	#
# Last modifed date		4-9-2017																	#
#####################################################################################################

import inspect
import subprocess
import re
import socket
import sys
import os
import pexpect
import errno
import hashlib
import paramiko as pm
from time import sleep

# Returns True if SSH session contains "skipped" (was unsuccessful)
# Returns False otherwise
def sshSkipCheck(x):
	try:
		if "skipped" in str(x):
			return True
		return False
	except:
			return False

# Connects to host via SSH with provided username and password
def connectToSSH(host, creds):
	# Try to connect to the host
	try:
		ssh = pm.SSHClient()
		#ssh.set_missing_host_key_policy(AllowAllKeys())
		ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
		ssh.connect(host, username=creds.un, password=creds.pw, timeout=10, allow_agent=False, look_for_keys=False)
		#return ssh
	except pm.AuthenticationException:
		return "%s skipped - authentication error\n" % (host)
	except:
		return "%s skipped - connection timeout\n" % (host)
	# Returns active SSH session to host
	return ssh

# Disconnects from active SSH session
def disconnectFromSSH(ssh):
	# Disconnect from the host
	ssh.close()

# Run single command on device over SSH
def runSSHCommand(command, host, creds):
	# Initiate an SSH session
	ssh = connectToSSH(host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return ssh
	# Send the command (non-blocking)
	stdin, stdout, stderr = ssh.exec_command(command)
	# Save command output to 'output'
	output = '\n'.join(item for item in stdout.read().splitlines() if '>' not in item)
	# Disconnect from the SSH session
	disconnectFromSSH(ssh)
	# Return output
	return output

# Run single command on device over SSH
def runSSHCommandASA(command, host, creds):
	child = pexpect.spawn('ssh %s@%s' % (creds.un, host))
	child.expect('%s@%s\'s password:' % (creds.un, host))
	child.sendline(creds.pw)
	child.expect('#')
	child.sendline(command)
	child.expect('#')
	output = child.before
	child.kill(1)
	return output

# Bounces provided interface on host
def bounceSSHInterface(host, iface, creds):
	# Initiate an SSH session
	ssh = connectToSSH(host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return ssh
	# Establish SSH interactive session
	sshConn = ssh.invoke_shell()
	### Send router commands ###
	# Enter config mode
	sshConn.send("config t\n")
	# Pause to allow command to complete
	sleep(1)
	# Enter the interface
	sshConn.send("interface " + iface + "\n")
	# Pause to allow command to complete
	sleep(1)
	# Shutdown interface
	sshConn.send("shutdown\n")
	# Pause for 3 seconds before re-enabling
	sleep(3)
	# Bring interface back online
	sshConn.send("no shutdown\n")
	# Save any command output as 'output'
	output = sshConn.recv(100000)
	# Disconnect from the SSH session
	disconnectFromSSH(ssh)
	# Return output
	return output

# Run command on an interface on a host
def runSSHInterfaceCommand(command, host, iface, creds):
	# Initiate an SSH session
	ssh = connectToSSH(host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return ssh
	# Establish SSH interactive session
	sshConn = ssh.invoke_shell()
	### Send router commands ###
	# Enter config mode
	sshConn.send("config t\n")
	# Pause to allow command to complete
	sleep(1)
	# Enter the interface
	sshConn.send("interface " + iface + "\n")
	# Pause to allow command to complete
	sleep(1)
	# Execute the specific action command on the interface
	sshConn.send(command + "\n")
	# Pause to allow command to complete
	sleep(1)
	# Save any command output as 'output'
	output = sshConn.recv(100000)
	# Disconnect from the SSH session
	disconnectFromSSH(ssh)
	# Return output
	return output

def runSSHConfigCommand(command, host, creds):
	# Initiate an SSH session
	ssh = connectToSSH(host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return ssh
	# Establish SSH interactive session
	sshConn = ssh.invoke_shell()
	### Send router commands ###
	# Enter config mode
	sshConn.send("config t\n")
	# Pause to allow command to complete
	sleep(1)
	# Execute the specific action command on the interface
	sshConn.send(command + "\n")
	# Pause to allow command to complete
	sleep(1)
	# Back out to privileged mode
	sshConn.send("end\n")
	# Pause to allow command to complete
	sleep(.5)
	# Save changes
	sshConn.send("wr\n")
	# Save any command output as 'output'
	output = sshConn.recv(100000)
	# Disconnect from the SSH session
	disconnectFromSSH(ssh)
	# Return output
	return output

# Run command on an interface on a host
def runCustomConfigCommands(commands, host, creds):
	# Initiate an SSH session
	ssh = connectToSSH(host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return ssh
	# Establish SSH interactive session
	sshConn = ssh.invoke_shell()
	### Send router commands ###
	for line in commands:
		# Execute each command one line at a time
		sshConn.send(line + "\n")
		# Pause to allow command to complete
		sleep(.25)
	# Save any command output as 'output'
	output = sshConn.recv(100000)
	# Disconnect from the SSH session
	disconnectFromSSH(ssh)
	# Return output
	return output

# Ask user if they want to bounce the interface.  Bounce if 'y' only
def askUserBounceInt(host, iface, vlan, creds):
	while True:
		choice = raw_input("\nDo you want to bounce this port now? (y/n): ")
		# Check to see if entered value is 'y' or 'n' only
		if choice != 'y' and choice != 'n':
			print "\nPlease enter \"y\" or \"n\" only."
			continue
		elif choice == 'n':
			output = "";
			break
		elif choice == 'y':
			output = bounceSSHInterface(host, iface, creds)
			break
		# Mainly used for debugging.  This should never trigger
		else:
			fn.debugErrorOut('301')
	return output

# Returns interface running config
def showIntRunConfig(host, interface, creds):
	command = "show run int %s | ex configuration|!" % (interface)
	result = runSSHCommand(command, host, creds)
	return result
