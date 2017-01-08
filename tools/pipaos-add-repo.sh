#!/bin/bash
#
# pipaos-add-repo.sh
#
# Add pipaOS repository to APT, then list available packages.
# Visit http://pipaos.mitako.eu for details
#
# Repository with this script can be found at http://archive.mitako.eu/
#

apt_file="/etc/apt/sources.list.d/mitako.list"
apt_entry="deb http://archive.mitako.eu/ jessie main"
apt_key="http://archive.mitako.eu/archive-mitako.gpg.key"
apt_cache="/var/lib/apt/lists/archive.mitako.eu_dists_jessie_main_binary-armhf_Packages"

echo "Registering pipaOS repository: $apt_entry"
echo "$apt_entry" | sudo tee $apt_file > /dev/null

echo "Adding repository key $apt_key"
curl -L "$apt_key" | sudo apt-key add -

echo "Refreshing available packages"
sudo apt-get update

echo "List of available packages:"
cat $apt_cache | grep "Package" | sort | uniq
echo "Enjoy!"
