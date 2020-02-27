#!/bin/bash
#
# by Tomas Hlavacek (brill@elfove.cz)
#

set -e

RSYNC_HOST="security.debian.org"
RSYNC_DIR="debian-security"
TO="/srv/mirror/debian-security"
LOGDIR=/var/log/mirror
LOGFILE=$LOGDIR/debian-security.log
ARCH_EXCLUDE=""
EXCLUDE=""
#MAILTO=sys.linux@ignum.cz
LOCK_TIMEOUT=360
RSYNC=${RSYNC:-/usr/bin/rsync}

if [ -z "$TO" ] || [ -z "$RSYNC_HOST" ] || [ -z "$RSYNC_DIR" ] || [ -z "$LOGDIR" ]; then
	echo "One of the following variables seems to be empty:"
	echo "TO, RSYNC_HOST, RSYNC_DIR or LOGDIR"
	exit 2
fi

HOSTNAME="debian.ignum.cz"

LOCK="${TO}/Archive-Update-in-Progress-${HOSTNAME}"
TMP_EXCLUDE="--exclude .~tmp~/"
echo "Starting sync at $(LANG=C date -u)..." >>$LOGFILE


for ARCH in $ARCH_EXCLUDE; do
	EXCLUDE=$EXCLUDE"\
	--exclude $ARCH/"
done

cd $HOME
umask 002

if [ -f "$LOCK" ]; then
  if [ "`find $LOCK -maxdepth 1 -cmin -$LOCK_TIMEOUT`" = "" ]; then
    if ps ax | grep '[r]'sync | grep -q $RSYNC_HOST; then
      echo "stale lock found, but a rsync is still running, aiee!"
      exit 1
    else
      echo "stale lock found (not accessed in the last $LOCK_TIMEOUT minutes), forcing update!"
      rm -f $LOCK
    fi
  else
    echo "current lock file exists, unable to start rsync!"
    exit 1
  fi
fi

touch $LOCK
trap "rm -f $LOCK" exit

set +e

if [ ! -d "${TO}/project/trace/" ]; then
  mkdir -p ${TO}/project/trace
fi

$RSYNC -4 -p --recursive --links --hard-links --times \
     --verbose \
     --delay-updates --delete-after \
     --timeout=3600 \
     --exclude "Archive-Update-in-Progress-${HOSTNAME}" \
     --exclude "project/trace/${HOSTNAME}" \
     $TMP_EXCLUDE $EXCLUDE $SOURCE_EXCLUDE \
     $RSYNC_HOST::$RSYNC_DIR/ $TO >> $LOGFILE 2>&1

LANG=C date -u > "${TO}/project/trace/${HOSTNAME}"


if [ -n "$MAILTO" ]; then
  mail -s "debian-security archive synced" $MAILTO < $LOGFILE
fi

#savelog $LOGFILE >/dev/null
rm $LOCK
