#!/usr/bin/python3

# Import statements
import sys
import socket
import paramiko
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

def execute(hst, usr, passwd, cmd):
    ssh = paramiko.SSHClient()
    # Set AutoAddPolicy so that we are not prompted to add new hosts to know_hosts file
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # All PittNET switches run SSH on default port 22
        # look_for_keys=False keeps script from trying to use keypair, we want plaintext passwd
        ssh.connect(hst, 22, usr, passwd, look_for_keys=False)
        # stdin, stdout, sterr are all set here, could write if needed
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().strip()

    except paramiko.ssh_exception.AuthenticationException as e:
        print("Authentication failure!")
        sys.exit(1)

    # stdout is written in 'bytes'. Needs to be decoded before priting
    ssh.close()
    return output.decode(encoding='UTF-8')

def check_host(host):
    try:
        socket.gethostbyname(host)
        return 1
    except socket.error:
        return 0

def get_workstation_vlans(switch, user, password):
    output = execute(switch, user, password, "sh vl br | i (W-I|WKSTN)")
    output = output.split()

    print(output)

    vlans = []
    ports = []

    for v in output:
        if v.isdigit():
            vlans.append(v)
        if v.find("Gi") is not -1:
            ports.append(v.replace(',', ''))

    return vlans, ports

def main():
    switch, user, password = user_input()

    if (check_host(switch)):
        vlans, ports = get_workstation_vlans(switch, user, password)
        for v in vlans:
            print(v)

        print()

        for p in ports:
            print(p)
    else:
        print("Check hostname")
        sys.exit(1)

# RUN
if __name__ == "__main__":
    main()
