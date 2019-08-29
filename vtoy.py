#!/usr/bin/python3

import libvirt
from flask import Flask, render_template

app = Flask(__name__)


@app.context_processor
def utility_processor():
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

    return dict(formatDomState=formatDomState)

@app.route('/')
def index():
    groups = []

    # TODO DYNAMIC GROUP
    for gid in [0,]:
        phns = ['lab08.maas.ignum.cz', 'lab10.maas.ignum.cz']
        g = {'name': 'Main', 'phys':[]}
        for phn in phns:
            conn = libvirt.open("qemu://%s/system" % phn)
            g['phys'].append({'name':phn, 'conn':conn, 'doms':conn.listAllDomains()})
        groups.append(g)

    result = render_template('vtoy-main.html',groups=groups)
    for g in groups:
        for p in g['phys']:
            p['conn'].close()

    return result
    

if __name__ == '__main__':
    app.run(debug = True)

