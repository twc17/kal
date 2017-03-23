#!/usr/bin/python3

# Import statements
import sys
import socket
import netmiko
import getpass

def user_input():
    try:
        user = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    except KeyboardInterrupt:
        print()
        print("!ERROR: Caught KeyboardInterrupt, exiting")
        sys.exit(1)

    return str(user), str(password)

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
    if len(sys.argv) == 1:
        print("ERROR: You need to specify the file containing switches")
        sys.exit(1)

    print("Welcome! This script will log in to each switch and grab the current configuration for all access ports in workstaion VLANs, make changes, then grab the new config.")
    go = input("Are you ready to get started? (y/N): ").lower()
    if go == 'y':
        switches = []
        switch_file = sys.argv[1]
        f = open(switch_file, 'r')
        for s in f:
            switches.append(s.strip())
        user, password = user_input()
        print()

        for s in switches:
            print("!Current Switch: " + s)
            if (check_host(s)):
                ip = socket.gethostbyname(s)

                print("*Getting workstation VLANs and access ports...")
                vlans, ports = get_workstation_vlans(ip, user, password)
                print("*Done") 

                print("*Building config...")
                config = get_running_config(ip, user, password, ports)
                print("*Done")

                print("*Writing workstation VLAN IDs to file " + s + "-vlans.txt ...")
                f = open(s + '-vlans.txt', 'w')
                f.write('\n'.join(vlans))
                f.close()
                print("*Done")

                print("*Writing workstation access ports to file " + s + "-ports.txt ...")
                f = open(s + '-ports.txt', 'w')
                f.write('\n'.join(ports))
                f.close()
                print("*Done")

                print("*Writing config before changes to file " + s + "-before.txt ...")
                f = open(s + '-before.txt', 'w')
                f.write(config)
                f.close()
                print("*Done")

                print("!Done with switch " + s)

                print()
                go = input("Ready for the next switch? (y/N): ")
                if go != 'y':
                    print("!ERROR: User canceled")
                    sys.exit(1)
            else:
                print("!ERROR: Check hostname")
                sys.exit(1)
        print()
        print("Done with all switches.")
        print("Exiting")

# RUN
if __name__ == "__main__":
    main()
