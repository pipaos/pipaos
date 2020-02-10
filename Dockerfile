#
#  Dockerfile for pipaOS
#
#  This Dockerfile pulls from the xsysroot image
#  and allows for building pipaOS from a Docker container.
#

from skarbat/xsysroot

COPY xsysroot.conf /etc
