#!/usr/bin/python3

import sys
import argparse
import vtoy

def main():
    default_group = 'vmnodes'

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inventory", help="print inventory", metavar="GROUP", nargs='?', const=default_group)
    parser.add_argument("-u", "--uri", help="print inventory in URI format (default METHOD=qemu+ssh", metavar="METHOD", nargs='?', const='qemu+ssh')
    parser.add_argument("-d", "--domains", help="print domains for each VM in inventory", action='store_true')
    args = parser.parse_args()

    if args.inventory:
        for host, user in list_inventory(ansible_groups=[args.inventory, ]):
            if args.uri:
                print(gen_phys_machine_uri(host, user, args.uri))
            else:
                print(host)
        return

    elif args.domains:
        group = (args.inventory if args.inventory else default_group)
        for host, user in vtoy.list_inventory(ansible_groups=[group, ]):
            if args.uri:
                huri = vtoy.gen_phys_machine_uri(host, user, args.uri)
            else:
                huri = vtoy.gen_phys_machine_uri(host, user)

            print("+ %s (%s)" % (host, huri))
            for d,s in vtoy.list_domains(huri):
                print("\\- %s (%s)" % (d, s))
            print()
        return

    parser.print_help()





if __name__ == '__main__':
    main()
