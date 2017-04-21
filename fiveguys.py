#!/usr/bin/env python3

# Title: fiveguys.py
# Author: Troy W. Caro <twc17@pitt.edu>
# Date: April 21, 2017 <4/21/17>
#
# Purpose: To extract workstaton VLAN IDs from c3750 and c3850 PittNet switches 
#
# Dependencies: 
#          Ubuntu and Debian:
#               build-essential libssl-dev libffi-dev python3-dev python3
#          Fedora and RHEL-derivatives:
#               gcc libffi-devel python3-devel openssl-devel
#          Netmiko python3 module:
#               Install using the following: sudo -H pip3 install netmiko

# Import statements
import os
import sys
import socket
import netmiko
import getpass

# Get keyboard input for username and password
# Return:
#   username and password as strings
def user_input():
    try:
        user = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    except KeyboardInterrupt:
        print()
        print("!ERROR: Caught KeyboardInterrupt, exiting")
        sys.exit(1)

    return str(user), str(password)

# Checks to see if the hosts resolves in DNS
# Parameters:
#   host<String> = hostname to lookup
# 
# Return:
#   1 if lookup is good
#   0 does not resolve
def check_host(host):
    try:
        socket.gethostbyname(host)
        return 1
    except socket.error:
        return 0

# Connect to an edge switch and get VLAN IDs and access ports for workstation VLANs
# Parameters:
#   ssh<Netmiko> = Netmiko SSH object - this is the connection to the switch
#
# Return:
#   vlans<Array[String]> = VLAN IDs of workstation VLANs
def get_workstation_vlans(ssh):
    # COMMAND THAT WILL RUN ON SWITCH
    cmd = "sh vl br | i (W-I|WKSTN|WKST)"
    result = ssh.find_prompt() + "\n"
    # Send command to switch and get output
    result += ssh.send_command(cmd, delay_factor=2)

    # This is the entire output of the command split into an array by whitespace
    output = result.split()

    vlans = []

    for v in output:
        # VLAN IDs are the only entries with just digits
        if v.isdigit():
            vlans.append(v)

    return vlans

# Main program logic
#
def main():
    # Make sure user entered list of switches as command line arg
    # Pre-condition: File is formatted correctly with one switch hostname per line
    if len(sys.argv) == 1:
        print("!ERROR: You need to specify the file containing switches")
        sys.exit(1)

    # Custom welcome message
    print("Welcome! This script will log in to each switch and grab the workstation VLAN IDs")
    # Make sure we're ready to go
    go = input("Are you ready to get started? (y/N): ").lower()
    if go == 'y':
        # Empty array for switches
        switches = []
        # Open file with switch hostnames
        switch_file = sys.argv[1]
        f = open(switch_file, 'r')
        for s in f:
            switches.append(s.strip())
        # Get username and password for switches from keyboard
        user, password = user_input()
        print()

        f = open('workstation-vlans.txt', 'w')

        # Go over each switch that was listed in the file
        for s in switches:
            # Let us know which one we're working with
            print("*Current switch " + s)
            if (check_host(s)):
                # Build the ssh object
                # Here is where we can specify anything specific about the switch
                #   device type, secrete phrase, etc
                print("*Establishing connection ...")
                ssh = netmiko.ConnectHandler(
                        device_type = 'cisco_ios',
                        ip = s,
                        username = user,
                        password = password)

                # Open ssh connection
                ssh.enable()
                print("*Done")

                # Get the VLAN IDs and access ports for workstaion VLANs and store in arrays
                print("*Getting workstation VLANs ...")
                vlans = get_workstation_vlans(ssh)
                print("*Done")

                # Just in case there are no workstation vlans on the switch, skip it
                if len(vlans) == 0:
                    print("!No workstation VLANs, skipping switch " + s)
                    continue

                # Write switch name to file
                f.write(s + ",")
                # Write workstation VLAN IDs to file
                print("*Writing workstation VLAN IDs to file ...")
                f.write(','.join(vlans))
                print("*Done")

                # We're done with this switch
                print("*Done with switch " + s)

                # Close ssh connection to switch
                ssh.disconnect()

                f.write('\n')

            # Hostname didn't resolve
            else:
                print("!ERROR: Check hostname")
                sys.exit(1)
        print()
        f.close()
        # No switches are left in the list, we're done
        print("Done with all switches.")
        print("Exiting")

# Execute the program
if __name__ == "__main__":
    main()
