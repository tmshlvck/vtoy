#! /bin/bash

rsync -av --delete rsync://cdimage.debian.org/debian-cd/ /srv/mirror/debian-cd/
