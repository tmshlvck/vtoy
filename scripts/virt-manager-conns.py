#!/usr/bin/python3

from gi.repository import Gio,GLib
import argparse
import sys

def read():
    s = Gio.Settings(schema='org.virt-manager.virt-manager.connections')
    return s.get_value('uris').unpack()


def checkuri(uri):
    return True


def write(uris):
    s = Gio.Settings(schema='org.virt-manager.virt-manager.connections')
    s.set_value('uris', GLib.Variant('as', uris))


class IOFile(object):
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        if self.filename and type(self.filename) == str:
           self.fh = open(self.filename, self.mode)
           return self.fh
        else:
            if self.mode == 'r':
                self.fh = sys.stdin
                return self.fh
            elif self.mode == 'w':
                self.fh = sys.stdout
                return self.fh
            else:
                raise IOError('Mode %s not allowd' % str(self.mode))

    def __exit__(self, type, value, tb):
        if self.fh and self.fh != sys.stdin and self.fh != sys.stdout:
            self.fh.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--export", help="export to file or STDOUT", metavar="FILE", nargs='?', const=sys.stdout)
    parser.add_argument("-i", "--import", help="import from file or STDIN", metavar="FILE", nargs='?', const=sys.stdin)
    parser.add_argument("-a", "--add", help="add URI", metavar="URI")
    parser.add_argument("-r", "--remove", help="remove URI", metavar="URI")
    args = parser.parse_args()

    if args.export:
        with IOFile(args.export, 'w') as efh:
            for r in read():
                efh.write("%s\n" % str(r))
        return

    elif vars(args)['import']:
        with IOFile(vars(args)['import'], 'r') as ifh:
            inp = set()
            for l in ifh.readlines():
                uri = l.strip()
                if uri:
                    if not checkuri(uri):
                        raise TypeError("URI %s failed to parse" % uri)
                    inp.add(uri)
            write(list(inp))
        return

    elif args.add:
        if not checkuri(args.add):
            parser.print_help()
            sys.exit(2)

        uris = set(read())
        uris.add(args.add)
        write(list(uris))
        return

    elif args.remove:
        if not checkuri(args.remove):
            parser.print_help()
            sys.exit(2)

        uris = set(read())
        uris.remove(args.remove)
        write(list(uris))
        return

    parser.print_help()



if __name__ == '__main__':
    main()
