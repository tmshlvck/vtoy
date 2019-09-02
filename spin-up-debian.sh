#!/bin/bash

CLOUDIMAGE="/var/lib/libvirt/images/debian-10.0.3-20190815-openstack-amd64.qcow2"
DEF_DISKSIZE="10G"
IMAGEDIR="/var/lib/libvirt/images/"
NET="br22"
#STOR="qcow2"
STORAGE="lvm"
VG="vg0"

if [ "$#" -lt 2 ]; then
    echo "Usage: $1 <virthostname> [disksize]"
    exit
fi

CIDIR=`mktemp -d`

cat >$CIDIR/meta-data <<EOF
instance-id: $1
local-hostname: $1
EOF

cat >$CIDIR/user-data <<EOF
#cloud-config
password: chobotak1234
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCeQg5TjzWeCC3v1meyx8sCcHi9G8mPD1J7o5R4WQYQrplfuALwAJ5v9Ne2lqZDzvQui7QvjfzkRTe/jGR35VKbOGYeaMkQ0tUEM8HimCIcjxdvdZEwGaAbMA2u3L0OXqozSmfZIURGzjf53qIkpAXkUSRrGFl0CEkWZpgDTgVTktJ7SqMnl981jAWDTHLCW7Vf+Fx+GnU1tvafWVw3qk/fTna7fobvg39fG6Ja7JqVF/qw4v74OtRfQjj6TLF03vAhdMmDPr2BVUvizVAhtqqUaJEMwF0yUIrohaDpIwiIx14op+6s9ecoj6wFrrPwknPt1xkPrd5N2VJGls+dkvEQK/GC7d8NNaXKQwQ1i9loMUhbGyalqSYCFVnYriAQMANTdqLBoLo/wqGagillgGtgZhIKIcpA+RgJ8I0FfpdDqAsrT9S9BUKMMpd9Eai9SiWmHq38XqjQwpfBEqg9hTcAwq80k9yv/Af5yJD7416N7xwRn5l4kBXbYdP5Ezwlm6yGY25OQEuz2n6izY2lZ3nHDuADsvRddpt4RdBSVDePAXeDl4nH42YxGAbgWb/vCx7RFQNdcl7F1iz3N98gaTKCOIwmqyJ3TmBp47A8Trwtol7FEpzUDI/2elOgOo2FvwlO7mp4ZAjkcFW15ca0UMCEjxx49PQ5V62Q+3DcOgGLRw== tmshlvck@gmail.com
packages:
  - qemu-guest-agent
EOF
genisoimage -o $CIDIR/config.iso -V cidata -r -J $CIDIR/user-data $CIDIR/meta-data
CIMG="$IMAGEDIR/${1}-config.iso"
mv $CIDIR/config.iso $IMAGEDIR/${1}-config.iso
rm -rf $CIDIR

if [[ $STORAGE == "qcow2" ]]
  IMG="${IMAGEDIR}/${1}.qcow2"
  cp $CLOUDIMAGE $IMG
  qemu-img resize $IMG ${2:-$DEF_DISKSIZE}
  DISK="path=$IMG"
fi

if [[ $STORAGE == "lvm" ]]
  DEV="/dev/${VG}/${1}"
  lvcreate -L${2:-$DEF_DISKSIZE} -n ${1} ${VG}
  dd if=$CLOUDIMAGE of=$DEV bs=1M
  DISK="path=$DEV"
fi


if [ -z "${DISK}" ]; then
  echo "Missing storage definition. Exit."
  exit -1
fi



virt-install --connect qemu:///system \
         -n $1 \
         -r 1024 \
         --import \
         --disk $DISK \
         --disk path=${CIMG} \
	 --network bridge=${NET},model=virtio \
	 --os-type=linux \
	 --os-variant=debiantesting \
	 --graphics spice
	 --cpu Nehalem-IBRS

