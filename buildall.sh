#!/bin/bash
#
# buildall.sh
#
#  Build pipaOS image from scratch.
#

# xsysroot profile and build log files
xsysroot_profile="pipaos-build"
logfile="buildall.log"

# switch to xsysroot profile
echo "Fetching xsysroot profile..."
xsysroot -p $xsysroot_profile -s
if [ "$?" != "0" ]; then
    exit 1
else
    echo "Unmounting xsysroot profile..."
    xsysroot -p $xsysroot_profile -u
    if [ "$?" != "0" ]; then
        exit 1
    fi
fi

echo "Building pipaOS..."
rm -fv $(xsysroot -q backing_image)
python -u pipaos.py $xsysroot_profile >$logfile 2>&1
echo "done!"
exit $?
