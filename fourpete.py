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
    cmd = "sh vl br | i (W-I|WKSTN|WKST)"
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
#   result<Array[String]> = Running config for list of access ports
def get_running_config(ssh, ports):
    result = []
    result.append(ssh.find_prompt() + "\n")

    for p in ports:
        # COMMAND THAT WILL RUN ON SWITCH
        result.append(ssh.send_command("sh run int " + p + " | inc (max|desc|access|max|speed|duplex)|interface", delay_factor=2))

    # Returns the entire running config of access ports as one string
    return result

# Connect to an edge switch and make config changes to access ports per new template
# Paramerters:
#   ssh<Netmiko> = ssh<Netmiko> = Netmiko SSH object - this is the connection to the switch
#   config<Array[String]> = List of access ports to config (This is actually the running config of the access ports)
#   switch<String> = switch hostname so we can tell if it's 3750 or 3850
#
# Return:
#   result<Array[String]> = config commands that were applied to the switch
def config_access_ports(ssh, config, switch):
    result = []

    # For each access port:
    for p in config:
        # COMMANDS THAT WILL RUN ON SWITCH
        commands = [
                'no logging event link-status',
                'power inline auto',
                'source template BX_VOIP_VLAN_361_TEMPLATE']

        # If we're working with a c3750 switch, we need to add two additional commands
        if switch.find("3750") is not -1:
            # COMMANDS THAT WILL RUN ON SWITCH
            commands.append("srr-queue bandwidth share 1 30 35 5")
            commands.append("priority-queue out")
    
        # Sometimes the switch name prompt gets caught in the runnig config
        # We want to make sure we're working with only interfaces
        if p.find("interface") is not -1:
            iface = p.split()
            # COMMANDS THAT WILL RUN ON SWITCH
            # should be 'interface GigabitEthernetX/X/XX'
            commands.insert(0,iface[0] + " " + iface[1])
            # If the port already has a port-security maximum set
            if p.find("maximum") is not -1:
                # Send config commands to switch
                # result.append(ssh.send_config_set(commands))
                print("-Command would be sent here")
            # If the port has no port-sexurity maximum set, set it to 2
            else:
                # COMMANDS THAT WILL RUN ON SWITCH
                commands.append("switchport port-security maximum 2")
                # Send config commands to switch
                # result.append(ssh.send_config_set(commands))
                print("-Command would be sent here")
        # DEBUG
        print(commands)

    # Return full list of commands that were run on the switch
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

                # Get the VLAN IDs and access ports for workstaion VLANs and store in arrays
                print("*Getting workstation VLANs and access ports...")
                vlans, ports = get_workstation_vlans(ssh)
                print("*Done")

                # Just in case there are no workstation vlans on the switch, skip it
                if len(vlans) == 0:
                    print("!No work station VLANs, skipping")
                    continue

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
                f.write('\n\n'.join(config))
                f.close()
                print("*Done")

                # Done with the 'before' information

                # Apply changes to switch
                print("*Sending new config to switch...")
                new = config_access_ports(ssh, config, s)
                print("*Done")

                # Write the changes that we made to a file
                print("*Writing config output to file " + s + "-config.txt ...")
                f = open(s + "/" + s + '-config.txt', 'w')
                f.write('\n'.join(new))
                f.close()
                print("*Done")

                # Get the new running config
                print("*Building new config...")
                config_new = get_running_config(ssh, ports)
                print("*Done")

                # Write new config to file
                print("*Writing new config changes to file " + s + "-after.txt ...")
                f = open(s + "/" + s + '-after.txt', 'w')
                f.write('\n\n'.join(config_new))
                f.close()
                print("*Done")

                # Done with the 'after' stuff

                # We're done with this switch
                print("!Done with switch " + s)

                # Close ssh connection to switch
                ssh.disconnect()

                # Gives the user a moment to review the output files that were generated, and that everything went okay
                # Make sure we're ready for the next switch
                print("!Please review output files before moving on")
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
