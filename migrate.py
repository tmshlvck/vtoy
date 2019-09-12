#!/usr/bin/python3

import sys
import libvirt
from xml.dom import minidom
import argparse
import threading
import time

def humanbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '%d %s' % (B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '%.2f KB' % (B/KB)
   elif MB <= B < GB:
      return '%.2f MB' % (B/MB)
   elif GB <= B < TB:
      return '%.2f GB' % (B/GB)
   elif TB <= B:
      return '%.2f TB' % (B/TB)

def do_migrate(srcconn, dstconn, dom_name):
    def job_progress_thread(conn):
        current_thread = threading.currentThread()

        def jobinfo_cb():
            olen = 0
            while True:
                time.sleep(1)

                if not current_thread.isAlive():
                    return False

                try:
                    jobinfo = conn.jobInfo()
                    data_total      = float(jobinfo[3])
                    data_processed  = float(jobinfo[4])
                    data_remaining  = float(jobinfo[5])

                    print(' '*olen, end="\r")
                    o = "Migration progress : %.2f%% (%s / %s)" % ((data_processed/data_total)*100, humanbytes(data_processed), humanbytes(data_total))
                    olen = len(o)
                    print(o, end="\r")
                except:
                    print("\n")
                    return False

            print("\n")
            return True

        t = threading.Thread(target=jobinfo_cb,
                         name="job progress reporting",
                         args=())
#        t.daemon = True
        t.start()
        return t
    # end job_progress_thread

    dom = srcconn.lookupByName(dom_name)
    if not dom:
        raise Exception('Failed to find the domain %s' % domName)

    flags = 0
    flags |= (libvirt.VIR_MIGRATE_LIVE|libvirt.VIR_MIGRATE_PERSIST_DEST|libvirt.VIR_MIGRATE_UNDEFINE_SOURCE|libvirt.VIR_MIGRATE_NON_SHARED_DISK)
#    flags |= libvirt.VIR_MIGRATE_PEER2PEER
    t = job_progress_thread(dom)
    new_dom = dom.migrate(dstconn, flags, None, None, 0)
    t.join()
    if new_dom == None:
        raise Exception('Migration to the new domain failed')


def list_blkdevs(srcconn, dom_name):

    def parse_blkdev(devpath):
        """
        devpath: str '/dev/vg0/lv0'
        returns: ('vg0', 'lv0') or raises exception when format is not recognized
        """

        fs = devpath.split('/')
        if len(fs) != 4:
            raise ValueError("Not valid simple path to LV with 3 parts: %s" % lvpath)
        if fs[0] != '' or fs[1] != 'dev':
            raise ValueError("Not valid path to LV in /dev: %s" % lvpath)
        return (fs[2], fs[3])

    dom = srcconn.lookupByName(dom_name)
    if not dom:
        raise Exception('Failed to find the domain %s' % dom_name)

    raw_xml = dom.XMLDesc(0)
    x = minidom.parseString(raw_xml)
    dts = x.getElementsByTagName('disk')
    for dt in dts:
        if dt.getAttribute('type') == 'block' and dt.getAttribute('device') == 'disk':
            for dn in dt.childNodes:
                if dn.nodeName == 'source':
                    for a in dn.attributes.keys():
                        if dn.attributes[a].name == 'dev':
                            yield parse_blkdev(dn.attributes[a].value)



def list_lvs(conn, poolname):
    sp = conn.storagePoolLookupByName(poolname)
    if not sp:
        raise Exception('Failed to find storage pool %s' % poolname)

    for s in sp.listAllVolumes():
        (stype, cap, alloc) = s.info()
        yield (s.name(), stype, cap)


def get_lv(conn, poolname, lvname):
    sp = conn.storagePoolLookupByName(poolname)
    if not sp:
        raise Exception('Failed to find storage pool %s' % poolname)

    for s in sp.listAllVolumes():
        if s.name() == lvname:
            (stype, cap, alloc) = s.info()
            return (s.name(), stype, cap)

    return None


def destroy_lv(conn, poolname, lvname):
    sp = conn.storagePoolLookupByName(poolname)
    if not sp:
        raise Exception('Failed to find storage pool %s' % poolname)

    s = sp.storageVolLookupByName(lvname)
    if not s:
        raise Exception('Failed to find volume %s in storage pool %s' % (lvname, poolname))

#    s.wipe()
    s.delete()


def create_lv(conn, vgname, lvname, size):
    stgvol_xml = """
<volume>
  <name>%s</name>
  <capacity unit="B">%d</capacity>
</volume>""" % (lvname, size)

    pool = conn.storagePoolLookupByName(vgname)
    if pool == None:
        raise Exception('Failed to locate any StoragePool objects')

    stgvol = pool.createXML(stgvol_xml, 0)
    if stgvol == None:
        raise Exception('Failed to create a  StorageVol objects')


def migrate(suri, duri, dom_name, force=False):
    srcconn = libvirt.open(suri)
    if srcconn == None:
        raise Exception('Failed to open connection to %s' % suri)

    dstconn = libvirt.open(duri)
    if dstconn == None:
        raise Exception('Failed to open connection to %s' % duri)
 
    sdom = srcconn.lookupByName(dom_name)
    if not sdom:
        raise Exception("Domain %s not found on src host" % dom_name)

    if dom_name in [d.name() for d in dstconn.listAllDomains()]:
        raise Exception("Domain %s is already running on dst host" % dom_name)


    print("Found src domain %s in state %s" % (sdom.name(), str(sdom.state())))

    blkdevs = list(list_blkdevs(srcconn, dom_name))
    for bd_pool, bd_name in blkdevs:
        print("Found blockdev /dev/%s/%s" % (bd_pool, bd_name))
        vname, vtype, vsize = get_lv(srcconn, bd_pool, bd_name)
        if vtype != libvirt.VIR_STORAGE_VOL_BLOCK:
            raise Exception("Wrong type of source blockdev: %d" % vtype)
        print("Found matching storage: vg %s lv %s size %d" % (bd_pool, vname, vsize))

        if get_lv(dstconn, bd_pool, bd_name):
            print("Found matching storage on dst host: vg %s lv %s size %d" % (bd_pool, vname, vsize))
            if not force:
                raise Exception("Stop unless force is set...")
            destroy_lv(dstconn, bd_pool, bd_name)
            print("Removed storage on dst host.")

    create_lv(dstconn, bd_pool, vname, vsize)

    print("Migration started...")
    do_migrate(srcconn, dstconn, dom_name)
    print("Migration finished.")

    for bd_pool, bd_name in blkdevs:
        destroy_lv(srcconn, bd_pool, bd_name)
        print("Removed storage /dev/%s/%s on src host." % (bd_pool, bd_name))

    srcconn.close()
    dstconn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("suri", help="source host URI", metavar="SOURCE_URI")
    parser.add_argument("duri", help="destination host URI", metavar="DEST_URI")
    parser.add_argument("dom_name", help="domain name", metavar="NAME")
    parser.add_argument("-f", "--force", help="force LV operations", action='store_true', default=False)
    args = parser.parse_args()

    migrate(args.suri, args.duri, args.dom_name, args.force)


if __name__ == '__main__':
    main()

