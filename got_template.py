#!/usr/bin/env python3

# Title: got_template.py
# Author: Troy W. Caro <twc17@pitt.edu>
# Date: April 27, 2017 <4/27/17>
#
# Purpose: To determinte if PittNet switches have a VOIP template and it's configured correctly
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

# Connect to an edge switch and get VOIP template information
# Parameters:
#   ssh<Netmiko> = Netmiko SSH object - this is the connection to the switch
#
# Return:
#   result<String> = VOIP template name and if it's configured correctly as one line
def get_template(ssh):
    # COMMAND THAT WILL RUN ON SWITCH
    cmd = "sh run | sec template"
    search_1 = "switchport block unicast"
    search_2 = "service-policy input custom_voip_policy"
    # Send command to switch and get output
    output = ssh.send_command_expect(cmd)
    output = output.splitlines()
    num_lines = len(output)
    result = ''

    for x in range(num_lines):
        if "template" and "VOIP" and "source" in output[x]:
            continue
        if "template" and "VOIP" in output[x]:
            if (x+1) < num_lines:
                good_line_1 = False
                good_line_2 = False
                
                for y in range(x+1, num_lines):
                    if good_line_1 and good_line_2:
                        result += output[x].split()[1] + ": yes "
                        break
                    if search_1 in output[y]:
                        good_line_1 = True
                    if search_2 in output[y]:
                        good_line_2 = True
                    if 'template' in output[y]:
                        result += output[x].split()[1] + ": no "
                        break
                #if good_line_1 or good_line_2 == False:
                    #result += output[x].split()[1] + ": no "
            else:
                result += output[x].split()[1] + ": no "

    return result

# Main program logic
#
def main():
    # Make sure user entered list of switches as command line arg
    # Pre-condition: File is formatted correctly with one switch hostname per line
    if len(sys.argv) == 1:
        print("!ERROR: You need to specify the file containing switches")
        sys.exit(1)

    # Custom welcome message
    print("Welcome! This script will log in to each switch and determine if it has a VOIP template or not")
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

        sw_tmp = open('switch_template_check.txt', 'w')

        # Go over each switch that was listed in the file
        for s in switches:
            print("Current switch: " + s)
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
                # Write switch name to file
                sw_tmp.write(s + ": ")

                # Get template information from switch and write to file
                sw_tmp.write(get_template(ssh))
                sw_tmp.write('\n')

                # Close ssh connection to switch
                ssh.disconnect()

            # Hostname didn't resolve
            else:
                print("!ERROR: Check hostname")
                sys.exit(1)
        print()
        sw_tmp.close()
        # No switches are left in the list, we're done
        print("Done with all switches.")
        print("Exiting")

# Execute the program
if __name__ == "__main__":
    main()
