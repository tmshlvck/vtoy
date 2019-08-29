#!/usr/bin/python3

import sys
import libvirt

conn = libvirt.open(sys.argv[1])
if conn == None:
    print('Failed to open connection to qemu+tcp://localhost/system', file=sys.stderr)
    exit(1)

caps = conn.getCapabilities() # caps will be a string of XML
print('Capabilities:\n'+caps)

print(conn.listDefinedDomains())

ds = conn.listAllDomains()
for d in ds:
    print(d.name())

help(d)

conn.close()
exit(0)
