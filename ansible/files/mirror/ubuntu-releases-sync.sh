#/bin/dash

fatal() {
  echo "$1"
  exit 1
}

warn() {
  echo "$1"
}

# Find a source mirror near you which supports rsync on
# https://launchpad.net/ubuntu/+cdmirrors
# rsync://<iso-country-code>.rsync.releases.ubuntu.com/releases should always work
RSYNCSOURCE=rsync://cz.rsync.releases.ubuntu.com/releases
#RSYNCSOURCE=rsync://mirror.vutbr.cz/ubuntu/releases

# Define where you want the mirror-data to be on your mirror
BASEDIR=/srv/mirror/ubuntu-releases

if [ ! -d ${BASEDIR} ]; then
  warn "${BASEDIR} does not exist yet, trying to create it..."
  mkdir -p ${BASEDIR} || fatal "Creation of ${BASEDIR} failed."
fi

rsync --verbose --recursive --times --links --hard-links \
  --stats --delete-after \
  ${RSYNCSOURCE} ${BASEDIR} || fatal "Failed to rsync from ${RSYNCSOURCE}."

date -u > ${BASEDIR}/.trace/$(hostname -f)
