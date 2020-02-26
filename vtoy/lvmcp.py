#!/usr/bin/env python3

listen_addr = '::'
listen_port = 16510
server_cert = '/etc/pki/libvirt/servercert.pem'
server_key = '/etc/pki/libvirt/private/serverkey.pem'
ca_cert = '/etc/pki/CA/cacert.pem'

#client_cert = '/etc/pki/libvirt/clientcert.pem'
#client_key = '/etc/pki/libvirt/private/clientkey.pem'
client_cert = server_cert
client_key = server_key
debug = True



import socket
import ssl
import sys
import os
import argparse
import time

BLOCKSZ = 4096
PROGRESS_PERIOD = 10000

def d(msg):
    if debug:
        print(msg, file=sys.stderr)



class ServerSocket(object):
    def __init__(self, ca_cert, server_key, server_cert, listen_address='::', listen_port=16510):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.ca_cert = ca_cert
        self.server_key = server_key
        self.server_cert = server_cert

    def __enter__(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=self.ca_cert)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile=server_cert, keyfile=self.server_key)
        context.load_verify_locations(cafile=self.ca_cert)

        bindsocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        bindsocket.bind((self.listen_address, self.listen_port))
        bindsocket.listen(5)

        d("listening on %s port %d" % (self.listen_address, self.listen_port))
        while True:
            try:
                newsocket, fromaddr = bindsocket.accept()
                d("connected: %s:%s" % (fromaddr[0], fromaddr[1]))
                self.conn = context.wrap_socket(newsocket, server_side=True)
                d("ssl estab: %s" % (self.conn.getpeercert()))

                bindsocket.close()
                d("listenining socket closed")
            finally:
                pass

            return self.conn

    def __exit__(self, extype, exval, extb):
        if self.conn:
            self.conn.close()
            d("active connection closed")


class ClientSocket(object):
    def __init__(self, ca_cert, client_key, client_cert, host, port=16510):
        self.ca_cert = ca_cert
        self.client_key = client_key
        self.client_cert = client_cert
        self.host = host
        self.port = port


    def __enter__(self):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.ca_cert)
        context.load_cert_chain(certfile=self.client_cert, keyfile=self.client_key)
        context.verify_mode = ssl.CERT_REQUIRED

        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.conn = context.wrap_socket(s, server_side=False, server_hostname=self.host)
        self.conn.connect((self.host, self.port))
        d("ssl estab: %s" % (self.conn.getpeercert()))
        return self.conn

    def __exit__(self, extype, exval, extb):
        if self.conn:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
            d("active connection closed")


def get_size(filename):
    fd = os.open(filename, os.O_RDONLY)
    try:
        return os.lseek(fd, 0, os.SEEK_END)
    finally:
        os.close(fd)


def runserver(dstfile, ca_cert, server_key, server_cert, timeout=30, listen_address='::', listen_port=16510, progress_callback=None):
    total = get_size(dstfile)
    with ServerSocket(ca_cert, server_key, server_cert, listen_address, listen_port) as s, open(dstfile, 'wb') as dsf:
        done = 0
        blocks = 0
        while True:
            b = s.recv(BLOCKSZ)
            if b:
                dsf.write(b)
                done += len(b)
                blocks += 1
                if progress_callback and (blocks % PROGRESS_PERIOD) == 0:
                    progress_callback(done, total)
            else:
                break
    return 0


def runclient(srcfile, ca_cert, client_key, client_cert, address, port=16510, progress_callback=None):
    total = get_size(srcfile)
    with ClientSocket(ca_cert, client_key, client_cert, address, port=16510) as s, open(srcfile, 'rb') as scf:
        done = 0
        blocks = 0
        while True:
            b = scf.read(BLOCKSZ)
            if b:
                s.send(b)
                done += len(b)
                blocks += 1
                if progress_callback and (blocks % PROGRESS_PERIOD) == 0:
                    progress_callback(done, total)
            else:
                break
    return 0


def progress_display(done, total):
    print("%d/%d" % (done, total), end='\r')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--src", help="SRC file/blockdev", default=None)
    parser.add_argument("-d", "--dst", help="DST file/blockdev", default=None)
    parser.add_argument("-p", "--peer", help="peer hostname/address", default=None)
    parser.add_argument("-r", "--retry", help="retry N time", default=1, type=int)
    parser.add_argument("-t", "--timeout", help="wait N second for client to connect", default=30, type=int)
    args = parser.parse_args()

    if args.src and args.peer:
        for i in range(0,args.retry):
            try:
                return runclient(args.src, ca_cert, client_key, client_cert, args.peer, progress_callback=progress_display)
                break
            except Exception as e:
                d(str(e))
                if args.retry > i:
                    time.sleep(i)
                else:
                    raise

    if args.dst:
        return runserver(args.dst, ca_cert, client_key, client_cert, args.timeout, progress_callback=progress_display)

    return -1


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)

