#!/usr/bin/env python3

# Title: fourpete.py (access_port_voip_config.py)
# Author: Troy W. Caro <twc17@pitt.edu>
# Date: March 23, 2017 <3/23/17>
#
# Purpose: This program was designed to prepare PittNET users for new VoIP phones.
#          The program will access each edge switch and configure the access ports that
#          are currently in workstation VLANs with the new template. 
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
#   ports<Array[String]> = Access ports in workstation VLANs
def get_workstation_vlans(ssh):
    # COMMAND THAT WILL RUN ON SWITCH
    cmd = "sh vl br | i (W-I|WKSTN)"
    result = ssh.find_prompt() + "\n"
    # Send command to switch and get output
    result += ssh.send_command(cmd, delay_factor=2)

    # This is the entire output of the command split into an array by whitespace
    output = result.split()

    vlans = []
    ports = []

    for v in output:
        # VLAN IDs are the only entries with just digits
        if v.isdigit():
            vlans.append(v)
        # Best way I've found to identify access ports is to look for the 'Gi'
        if v.find("Gi") is not -1:
            # Remove comma from access port
            ports.append(v.replace(',', ''))

    return vlans, ports

# Connect to an edge switch and get the running config for a list of access ports
# Parameters:
#   ssh<Netmiko> = Netmiko SSH object - this is the connection to the switch
#   ports<Array[String]> = List of access ports
#
# Return:
#   result<String> = Running config for list of access ports
def get_running_config(ssh, ports):
    result = ssh.find_prompt() + "\n"

    for p in ports:
        # COMMAND THAT WILL RUN ON SWITCH
        result += ssh.send_command("sh run int " + p + " | inc (max|desc|access|max|speed|duplex)|interface", delay_factor=2)
        result += '\n\n'

    # Returns the entire running config of access ports as one string
    return result

# Main program logic
#
def main():
    # Make sure user entered list of switches as command line arg
    # Pre-condition: File is formatted correctly with one switch hostname per line
    if len(sys.argv) == 1:
        print("ERROR: You need to specify the file containing switches")
        sys.exit(1)

    # Custom welcome message
    print("Welcome! This script will log in to each switch and grab the current configuration for all access ports in workstaion VLANs, make changes, then grab the new config.")
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

        # Go over each switch that was listed in the file
        for s in switches:
            # Let us know which one we're working with
            print("!Current Switch: " + s)
            if (check_host(s)):
                # Build the ssh object
                # Here is where we can specify anything specific about the switch
                #   device type, secrete phrase, etc
                ssh = netmiko.ConnectHandler(
                        device_type = 'cisco_ios',
                        ip = s,
                        username = user,
                        password = password)

                # Open ssh connection
                ssh.enable()

                # Make a dir for each switch as each switch will generate a few output files
                os.mkdir(s)
                # Switch hostname to IP address
                ip = socket.gethostbyname(s)

                # Get the VLAN IDs and access ports for workstaion VLANs and store in arrays
                print("*Getting workstation VLANs and access ports...")
                vlans, ports = get_workstation_vlans(ssh)
                print("*Done") 

                # Get the running config for access ports in workstation VLANs and store in array
                # This is before any changes have been made to the switch
                print("*Building config...")
                config = get_running_config(ssh, ports)
                print("*Done")

                # Create new file and write workstation VLAN IDs to it
                print("*Writing workstation VLAN IDs to file " + s + "-vlans.txt ...")
                f = open(s + "/" + s + '-vlans.txt', 'w')
                f.write('\n'.join(vlans))
                f.close()
                print("*Done")

                # Create new file and write workstation access ports to it
                print("*Writing workstation access ports to file " + s + "-ports.txt ...")
                f = open(s + "/" + s + '-ports.txt', 'w')
                f.write('\n'.join(ports))
                f.close()
                print("*Done")

                # Create a new file and write the running config of access ports to it
                # No changes have been made to the switch yet
                print("*Writing config before changes to file " + s + "-before.txt ...")
                f = open(s + "/" + s + '-before.txt', 'w')
                f.write(config)
                f.close()
                print("*Done")

                # Done with the 'before' information

                # TROY
                # This is where I need to add the rest of the program
                # At this point, the program will make and commit the changes to the access ports

                # We're done with this switch
                print("!Done with switch " + s)

                # Close ssh connection to switch
                ssh.disconnect()

                print()
                # Gives the user a moment to review the output files that were generated, and that everything went okay
                # Make sure we're ready for the next switch
                print("*Review the output files if needed. No changes have been made yet")
                go = input(">Ready for the next switch? (y/N): ").lower()
                if go != 'y':
                    print("!ERROR: User canceled")
                    sys.exit(1)
            # Hostname didn't resolve
            else:
                print("!ERROR: Check hostname")
                sys.exit(1)
        print()
        # No switches are left in the list, we're done
        print("Done with all switches.")
        print("Exiting")

# Execute the program
if __name__ == "__main__":
    main()
