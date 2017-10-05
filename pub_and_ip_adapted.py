#!/usr/bin/python3

# Title: pub_and_ip_adapted.py
# Author: Troy W. Caro <twc17@pitt.edu>
# Version: 1.0.0
# Last Modified: <10/05/17>
#
# Purpose: To extract public dot1x VLAN names from c3750 and c3850 PittNet switches 
#
# Dependencies: 
#          Ubuntu and Debian:
#               build-essential libssl-dev libffi-dev python3-dev python3
#          Fedora and RHEL-derivatives:
#               gcc libffi-devel python3-devel openssl-devel
#          Netmiko python3 module:
#               Install using the following: sudo -H pip3 install netmiko
#
# TODO: Maybe figure out a better way to catch exceptions. Test it!

# Import statements
import os
import sys
import socket
import netmiko
import getpass

# We will write all output to this file
LOG_FILE = "pub_vlan_names.log"

# Write an entry to our log file
# Arguments:
#   entry -- string entry we will write to file
# Return:
#   None
def write_log(entry):
    f = open(LOG_FILE, 'a')
    f.write(entry + '\n')
    f.close()

# Get keyboard input for username and password
# Return:
#   username and password as strings
def user_input():
    try:
        user = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    except KeyboardInterrupt:
        print()
        print("ERROR: Caught KeyboardInterrupt, exiting")
        write_log("ERROR: Caught KeyboardInterrupt, exiting")
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

# Connect to an edge switch and get VLAN IDs for public dot1x VLANs
# Parameters:
#   ssh<Netmiko> = Netmiko SSH object - this is the connection to the switch
#
# Return:
#   pub_vlans<Array[String]> = VLAN IDs of dot1x VLANs
def get_vlans(ssh, vlan_id):
    # COMMAND THAT WILL RUN ON SWITCH
    cmd = "sh vl id " + vlan_id

    result = ssh.find_prompt() + "\n"
    # Send command to switch and get output
    result += ssh.send_command(cmd, delay_factor=1)
    # This is the entire output of the command split into an array by whitespace
    output = result.split()

    return output[10]


# Main program logic
#
def main():
    # Make sure user entered list of switches as command line arg
    # Pre-condition: File is formatted correctly with one switch hostname per line
    if len(sys.argv) == 1:
        print("ERROR: You need to specify the file containing switches")
        write_log("ERROR: You need to specify the file containing switches")
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
        f.close()
        # Get username and password for switches from keyboard
        user, password = user_input()
        print()

        # File format:
        # <switch>, <dot1x_vlan_id>, <voip_vlan_id>
        f = open('pub_vlan_names.txt', 'w')

        # Go over each switch that was listed in the file
        for s in switches:
            s_name = s.split(',')[0]
            vlan_id = s.split(',')[1]
            # Let us know which one we're working with
            print("Current switch " + s_name)
            write_log("Current switch " + s_name)
            if (check_host(s_name)):
                try:
                    # Build the ssh object
                    # Here is where we can specify anything specific about the switch
                    #   device type, secrete phrase, etc
                    ssh = netmiko.ConnectHandler(
                            device_type = 'cisco_ios',
                            ip = s_name,
                            username = user,
                            password = password)

                    # Open ssh connection
                    ssh.enable()

                    # Get the VLAN IDs for dot1x and VoIP VLANs and store in arrays
                    pub_vlan_name = get_vlans(ssh, vlan_id)

                    # Write switch name to file
                    f.write(s_name + "," + vlan_id + "," + pub_vlan_name + '\n')

                    # We're done with this switch

                    # Close ssh connection to switch
                    ssh.disconnect()

                except:
                    print("ERROR: Unexpected exception with " + s_name)
                    write_log("ERROR: Unexpected exception with " + s_name)
                    f.write("ERROR: Unexpected exception with " + s_name + '\n')

            # Hostname didn't resolve
            else:
                print("ERROR: Check hostname for " + s_name)
                write_log("ERROR: Check hostname for " + s_name)
                f.write("ERROR: Check hostname for " + s_name + '\n')
        print()
        f.close()
        # No switches are left in the list, we're done
        print("Done with all switches.")
        write_log("Done with all switches.")
        print("Exiting")
        write_log("Exiting")

# Execute the program
if __name__ == "__main__":
    main()
