#!/bin/bash
#
# pipadev.sh
#
# Prepare a development sysroot after buildall.sh has completed
#

DEVPKGS="build-essential devscripts debhelper fakeroot git-core \
libqt5all-dev libqt5webengine-dev libx11-dev libpng12-dev libqt5wayland-dev"

# xsysroot profile and build log files
xsysroot_profile="$1"

if [ "$xsysroot_profile" == "" ]; then
    echo "please specify a xsysroot development profile name"
    exit 1
fi

# switch to xsysroot profile
echo "Fetching xsysroot profile..."
xsysroot -p $xsysroot_profile -s
if [ "$?" != "0" ]; then
    exit 1
else
    echo "Expanding xsysroot profile..."
    xsysroot -p $xsysroot_profile -u
    if [ "$?" != "0" ]; then
        exit 1
    fi

    xsysroot -p $xsysroot_profile -r
    xsysroot -p $xsysroot_profile -u
    xsysroot -p $xsysroot_profile -e
    xsysroot -p $xsysroot_profile -m
    echo "xsysroot expanded."

    xsysroot -p $xsysroot_profile -x "apt-get update"
    xsysroot -p $xsysroot_profile -x "apt-get -y install --no-install-recommends $DEVPKGS"
    echo "xsysroot development tools installed."
fi
