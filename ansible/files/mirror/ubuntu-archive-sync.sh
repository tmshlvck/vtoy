#/bin/dash

fatal() {
  echo "$1"
  exit 1
}

warn() {
  echo "$1"
}

# Find a source mirror near you which supports rsync on
# https://launchpad.net/ubuntu/+archivemirrors
# rsync://<iso-country-code>.rsync.archive.ubuntu.com/ubuntu should always work
RSYNCSOURCE=rsync://cz.archive.ubuntu.com/ubuntu
#RSYNCSOURCE=rsync://mirror.vutbr.cz/ubuntu/archive

# Define where you want the mirror-data to be on your mirror
BASEDIR=/srv/mirror/ubuntu

if [ ! -d ${BASEDIR} ]; then
  warn "${BASEDIR} does not exist yet, trying to create it..."
  mkdir -p ${BASEDIR} || fatal "Creation of ${BASEDIR} failed."
fi

rsync -a --recursive --times --links --hard-links \
  --progress --stats \
  --exclude "Packages*" --exclude "Sources*" \
  --exclude "Release*" \
  ${RSYNCSOURCE} ${BASEDIR} || fatal "First stage of sync failed."

rsync -a --recursive --times --links --hard-links \
  --progress --stats --delete --delete-after \
  ${RSYNCSOURCE} ${BASEDIR} || fatal "Second stage of sync failed."

date -u > ${BASEDIR}/project/trace/$(hostname -f)
