#!/usr/bin/python3

# Import statements
import sys
import socket
import netmiko
import getpass

def user_input():
    try:
        switch = input("Enter switch: ")
        user = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    except KeyboardInterrupt:
        print()
        print("Caught KeyboardInterrupt, exiting")
        sys.exit(1)

    return str(switch), str(user), str(password)

def check_host(host):
    try:
        socket.gethostbyname(host)
        return 1
    except socket.error:
        return 0

def get_workstation_vlans(switch, user, password):
    cmd = "sh vl br | i (W-I|WKSTN)"
    ssh = netmiko.ConnectHandler(
            device_type = 'cisco_ios',
            ip = switch,
            username = user,
            password = password)

    ssh.enable()
    result = ssh.find_prompt() + "\n"
    result += ssh.send_command(cmd, delay_factor=2)
    ssh.disconnect()

    output = result.split()

    #print(output)

    vlans = []
    ports = []

    for v in output:
        if v.isdigit():
            vlans.append(v)
        if v.find("Gi") is not -1:
            ports.append(v.replace(',', ''))

    return vlans, ports

def get_running_config(switch, user, password, ports):
    ssh = netmiko.ConnectHandler(
            device_type = 'cisco_ios',
            ip = switch,
            username = user,
            password = password)

    ssh.enable()
    result = ssh.find_prompt() + "\n"

    for p in ports:
        result += ssh.send_command("sh run int " + p + " | inc (max|desc|access|max|speed|duplex)|interface", delay_factor=2)
        result += '\n\n'

    ssh.disconnect()

    return result

def main():
    switch, user, password = user_input()

    if (check_host(switch)):
        ip = socket.gethostbyname(switch)

        print("*Getting workstation VLANs and access ports...")
        vlans, ports = get_workstation_vlans(ip, user, password)
        print("*Done!") 

        print("*Building config...")
        config = get_running_config(ip, user, password, ports)
        print("*Done!")

        print("*Writing workstation VLAN IDs to file " + switch + "-vlans.txt")
        f = open(switch + '-vlans.txt', 'w')
        f.write('\n'.join(vlans))
        f.close()
        print("*Done!")

        print("*Writing workstation access ports to file " + switch + "-ports.txt")
        f = open(switch + '-ports.txt', 'w')
        f.write('\n'.join(ports))
        f.close()
        print("*Done!")

        print("*Writing config to file...")
        f = open(switch + '-before.txt', 'w')
        f.write(config)
        f.close()
        print("*Done!")

        print()
        print("Current config for " + switch + " written to " + switch + "-before.txt")
    else:
        print("Check hostname!")
        sys.exit(1)

# RUN
if __name__ == "__main__":
    main()
