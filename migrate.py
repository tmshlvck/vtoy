#!/usr/bin/python3

import sys

def migrate(suri, duri, dom_name):
    import libvirt

    srcconn = libvirt.open(suri)
    if srcconn == None:
        raise Exception('Failed to open connection to %s' % suri)

    dstconn = libvirt.open(duri)
    if dstconn == None:
        raise Exception('Failed to open connection to %s' % duri)
        
    dom = srcconn.lookupByName(dom_name)
    if dom == None:
        print('Failed to find the domain '+domName, file=sys.stderr)
        exit(1)

    flags = 0
    flags |= (libvirt.VIR_MIGRATE_LIVE|libvirt.VIR_MIGRATE_PERSIST_DEST|libvirt.VIR_MIGRATE_UNDEFINE_SOURCE|libvirt.VIR_MIGRATE_NON_SHARED_DISK)
#    flags |= libvirt.VIR_MIGRATE_PEER2PEER
    new_dom = dom.migrate(dstconn, flags, None, None, 0)
    if new_dom == None:
        print('Could not migrate to the new domain', file=sys.stderr)
        exit(1)

    print('Domain was migrated successfully.', file=sys.stderr)

    srcconn.close()
    dstconn.close()


def main():
    migrate(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == '__main__':
    main()
