#!/bin/bash
#
# buildall.sh
#
# Build pipaOS console and xgui versions, from scratch.
#

mode=$1
if [ "$mode" != "all" ] && [ "$mode" != "console" ] && [ "$mode" != "xgui" ]; then
    echo "Syntax: buildall < all | console | xgui >"
    exit 1
fi

# xsysroot profile and build log files
xsysroot_profile="pipaos-build"
logfile_console="build-console.log"
logfile_xgui="build-xgui.log"

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

# build pipaos console
if [ "$mode" == "all" ] || [ "$mode" == "console" ]; then
    echo "Building pipaOS console..."
    rm -fv $(xsysroot -q backing_image)
    python -u pipaos.py $xsysroot_profile >$logfile_console 2>&1
fi

# build pipaos xgui
if [ "$mode" == "all" ] || [ "$mode" == "xgui" ]; then
    echo "Building pipaOS xgui..."
    rm -fv $(xsysroot -q backing_image)
    python -u pipaos.py $xsysroot_profile --with-xgui >$logfile_xgui 2>&1
fi

echo "done!"
exit $?
