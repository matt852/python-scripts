#!/usr/bin/python

#####################################################################################################
# Written by: 																						#
# Creation date			1-25-2017																	#
# Last modifed date		4-9-2017																	#
#####################################################################################################

import netmiko as nm
import functions as fn


# Returns True if SSH session contains "skipped" (was unsuccessful)
# Returns False otherwise
def sshSkipCheck(x):
	try:
		if "skipped" in str(x):
			return True
		return False
	except:
			return False

# Connects to host via SSH with provided username and password, and type of device specified
def connectToSSH(deviceType, host, creds):
	# Try to connect to the host
	try:
		ssh = nm.ConnectHandler(device_type=deviceType, ip=host, username=creds.un, password=creds.pw)
	#except nm.AuthenticationException:
	#	return "%s skipped - authentication error\n" % (host)
	except:
		return "%s skipped - connection timeout\n" % (host)
	# Returns active SSH session to host
	return ssh

# Disconnects from active SSH session
def disconnectFromSSH(ssh):
	# Disconnect from the host
	ssh.disconnect()

# Runs command on host via SSH and returns output
def runSSHCommandOnce(command, deviceType, host, creds):
	ssh = connectToSSH(deviceType, host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return ssh
	# Get command output from device
	result = ssh.send_command(command)
	# Disconnect from SSH session
	disconnectFromSSH(ssh)
	# Return output of command
	return result

# Run multiple commands in list on host via SSH and returns all output from applying the config
def runMultipleSSHCommandsInSession(cmdList, ssh):
	# Get command output from multiple commands configured on device
	result = ssh.send_config_set(cmdList)
	# Return output of command
	return result

# Creates an SSH session, verifies it worked, then returns the session itself
def getSSHSession(deviceType, host, creds):
	ssh = connectToSSH(deviceType, host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		fn.debugScript("ERROR: In function nfn.getSSHSession, sshSkipCheck failed using host %s and deviceType %s" % (host, deviceType))
	# Return output of command
	return ssh

# Runs command on provided existing SSH session and returns output
def runSSHCommandInSession(command, ssh):
	# Get command output from device
	result = ssh.send_command(command)
	# Return output of command
	return result
