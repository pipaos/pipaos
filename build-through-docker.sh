#!/bin/bash
#
#  build-through-docker.sh
#
#  Build pipaOS through a Docker container.
#

set -e

osimages="$HOME/osimages"
systmp="$HOME/systmp"

if [ "$1" == "build" ]; then
    cmd="./buildall.sh"
else
    cmd="bash"
fi

mkdir -p $osimages $systmp
chmod 777 $osimages $systmp

docker run -it --privileged -v=/dev:/dev -v /proc:/proc \
       -v $HOME/osimages:/var/cache/xsysroot \
       -v $HOME/systmp:/var/cache/systmp \
       -v $(pwd):/home \
       -w /home \
       pipaos $cmd
