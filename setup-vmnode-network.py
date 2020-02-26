#!/usr/bin/python3

import argparse
import yaml
import sys

def read_yaml(fn):
    with open(fn, 'r') as fh:
        npd = yaml.load(fh, Loader=yaml.FullLoader)
    return npd


def transform(npd):
    brs = ['br22',]

    npo = {'network':{'ethernets':{}, 'bridges':{}}}
    brif = []
    for e in npd['network']['ethernets']:
        npo['network']['ethernets'][e] = {}
        if 'match' in npd['network']['ethernets'][e]:
            npo['network']['ethernets'][e]['match'] = npd['network']['ethernets'][e]['match']
        if 'mtu' in npd['network']['ethernets'][e]:
            npo['network']['ethernets'][e]['mtu'] = npd['network']['ethernets'][e]['mtu']
        if 'set-name' in npd['network']['ethernets'][e]:
            npo['network']['ethernets'][e]['set-name'] = npd['network']['ethernets'][e]['set-name']
        if 'addresses' in npd['network']['ethernets'][e]:
            if 'gateway4' in npd['network']['ethernets'][e] or 'gateway6' in npd['network']['ethernets'][e]:
                brif.append(e)
            else:
                npo['network']['ethernets'][e]['addresses'] = npd['network']['ethernets'][e]['addresses']

    for br in brs:
        npo['network']['bridges'][br] = {}
        npo['network']['bridges'][br]['interfaces'] = []
        for e in brif:
             npo['network']['bridges'][br]['interfaces'].append(e)
             if 'addresses' in npd['network']['ethernets'][e]:
                npo['network']['bridges'][br]['addresses'] = npd['network']['ethernets'][e]['addresses']
             if 'gateway4' in npd['network']['ethernets'][e]:
                npo['network']['bridges'][br]['gateway4'] = npd['network']['ethernets'][e]['gateway4']
             if 'gateway6' in npd['network']['ethernets'][e]:
                npo['network']['bridges'][br]['gateway6'] = npd['network']['ethernets'][e]['gateway6']
             if 'nameservers' in npd['network']['ethernets'][e]:
                npo['network']['bridges'][br]['nameservers'] = npd['network']['ethernets'][e]['nameservers']
    return npo


def print_yaml(npo, fn=None):
    t = yaml.dump(npo)
    if fn:
        with open(fn, 'w') as fnh:
            print(t, file=fnh)
    else:
        print(t)



def main():
    dfn = '/etc/netplan/50-cloud-init.yaml'

    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--write", help="write the result", action="store_true")
    parser.add_argument("-f", "--file", help="write the result", default=dfn)
    args = parser.parse_args()

    i = read_yaml(args.file)
    o = transform(i)
    if args.write:
        print_yaml(o, args.file)
    else:
        print_yaml(o)
    return 0


if __name__ == '__main__':
    sys.exit(main())
