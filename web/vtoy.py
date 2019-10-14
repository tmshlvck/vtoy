#!/usr/bin/python3

import vtoy
from flask import Flask, render_template

app = Flask(__name__)


@app.context_processor
def utility_processor():
    return dict(formatDomState=vtoy.formatDomState)

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

