#!/usr/bin/python3

import sys
import argparse

def list_domains(uri):
    import libvirt

    def formatDomState(status):
        state, reason = status
        if state == libvirt.VIR_DOMAIN_NOSTATE:
            return 'NOSTATE'
        elif state == libvirt.VIR_DOMAIN_RUNNING:
            return 'RUNNING'
        elif state == libvirt.VIR_DOMAIN_BLOCKED:
            return 'BLOCKED'
        elif state == libvirt.VIR_DOMAIN_PAUSED:
            return 'PAUSED'
        elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
            return 'SHUTDOWN'
        elif state == libvirt.VIR_DOMAIN_SHUTOFF:
            return 'SHUTOFF'
        elif state == libvirt.VIR_DOMAIN_CRASHED:
            return 'CRASHED'
        elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
            return 'PMSUSPENDED'
        else:
            return 'unknown'

    conn = libvirt.open(uri)
    if conn == None:
        raise Exception('Failed to open connection to %s' % uri)

    ds = conn.listAllDomains()
    for d in ds:
        yield (d.name(), formatDomState(d.state()))

    conn.close()


def list_inventory(ansible_inventory='/etc/ansible/hosts', ansible_groups=None):
    from ansible.parsing.dataloader import DataLoader
    from ansible.inventory.manager import InventoryManager
    from ansible.vars.manager import VariableManager

    data_loader = DataLoader()
    inventory = InventoryManager(loader=data_loader, sources=ansible_inventory)
    variable_manager = VariableManager(loader=data_loader, inventory=inventory)

    for ag in ansible_groups:
        for h in inventory.groups[ag].get_hosts():
            rhost = (h.get_vars()['ansible_host'] if 'ansible_host' in h.get_vars() else h.get_vars()['inventory_hostname'])
            ruser = (variable_manager.get_vars(host=h)['ansible_user'] if 'ansible_user' in variable_manager.get_vars(host=h) else 'root')
            yield (rhost, ruser)

def gen_phys_machine_uri(host, user='root', prefix='qemu+ssh'):
    return '%s://%s@%s/system' % (prefix, user, host)

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
        for host, user in list_inventory(ansible_groups=[group, ]):
            if args.uri:
                huri = gen_phys_machine_uri(host, user, args.uri)
            else:
                huri = gen_phys_machine_uri(host, user)

            print("+ %s" % host)
            for d,s in list_domains(huri):
                print("\\- %s (%s)" % (d, s))
            print()
        return

    parser.print_help()





if __name__ == '__main__':
    main()
