#!/usr/bin/python3

import argparse
import vtoy



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("suri", help="source host URI", metavar="SOURCE_URI")
    parser.add_argument("duri", help="destination host URI", metavar="DEST_URI")
    parser.add_argument("dom_name", help="domain name", metavar="NAME")
    parser.add_argument("-f", "--force", help="force LV operations", action='store_true', default=False)
    parser.add_argument("-c", "--cleanup", help="cleanup LV on source", action='store_true', default=False)
    args = parser.parse_args()

    vtoy.migrate(args.suri, args.duri, args.dom_name, args.force, args.cleanup)


if __name__ == '__main__':
    main()

