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
        switch = socket.gethostbyname(switch)
        vlans, ports = get_workstation_vlans(switch, user, password)
        print("Workstation VLANs")
        for v in vlans:
            print(v)

        print()
        print("Access ports in workstation VLANs")
        for p in ports:
            print(p)

        print()
        
        config = get_running_config(switch, user, password, ports)
        if config is not '':
            print(config)
    else:
        print("Check hostname")
        sys.exit(1)

# RUN
if __name__ == "__main__":
    main()
