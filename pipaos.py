#!/usr/bin/python
#
# pipaos.py - Build pipaOS distro image.
#
# Copyright (C) 2013-2016 Albert Casals <skarbat@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os
import sys
import time
import xsysroot

__version__='4.7'
pipaos_codename='tamarillo'


def create_core_image(xpipa):
    '''
    Create an empty image, format partitions, install the core OS into it
    '''
    repo_url='http://mirror.us.leaseweb.net/raspbian/raspbian/'
    arch='armhf'
    suite='jessie'
    boot_size=120 # in MiB

    # image size is specified in the xsysroot profile configuration
    try:
        image_size=int(xpipa.query('qcow_size').replace('M', '')) - boot_size
        geometry='{} fat32:{} ext4:{}'.format(xpipa.query('backing_image'), boot_size, image_size)
    except:
        print 'Error calculating geometry - please specify xsysroot "qcow_size" in MiB'
        return False

    cmd_debootstrap='sudo debootstrap --no-check-gpg --verbose --include {} ' \
        '--foreign --variant=minbase --arch={} {} {} {}'

    extra_pkgs='less,sudo,nano,binutils,apt-utils,psmisc,module-init-tools,debconf-utils,'\
        'ca-certificates,curl,file,time,iputils-ping,net-tools,'

    print '>>> Creating pipaOS image with geometry: {}... '.format(geometry)
    success=xsysroot.create_image(geometry)
    if success:
        # Put the fresh image ready to work
        if not xpipa.renew():
            return False

        expanded_debootstrap=cmd_debootstrap.format(extra_pkgs, arch, suite, xpipa.query('sysroot'), repo_url)
        print '>>> Installing core OS (First stage)... '
        print expanded_debootstrap
        rc=os.system(expanded_debootstrap)
        if rc:
            print '>>> Error running debootstrap first stage - aborting'
            return False
        else:
            # Make the image ready to emulate ARM
            qemu_path=os.popen('which qemu-arm-static').read().strip()
            rc=os.system('sudo cp {} {}{}'.format(qemu_path, xpipa.query('sysroot'), qemu_path))
            if rc:
                print 'Could not copy QEMU ARM emulator in the image - aborting'
                return False

            print '>>> Installing core OS (Second stage)... '
            rc=xpipa.execute('/debootstrap/debootstrap --second-stage')
            if rc:
                print '>>> Error running debootstrap - aborting'
                return False

            # unmount to prepare for next step
            xpipa.umount()

    return True


def setup_repositories(xpipa):
    '''
    Register APT repositories and bring the package database up to date
    '''
    apt_directory='/etc/apt'
    repos = [ 
        { 'name': 'raspbian', 
          'file': 'sources.list',
          'pointer': 'deb http://archive.raspbian.org/raspbian jessie main contrib non-free',
          'key': 'https://archive.raspbian.org/raspbian.public.key' },

        { 'name': 'raspberrypi', 
          'file': 'sources.list.d/raspberrypi.list', 
          'pointer': 'deb http://archive.raspberrypi.org/debian/ jessie main ui',
          'key': 'http://archive.raspberrypi.org/debian/raspberrypi.gpg.key' },

        { 'name': 'mitako', 
          'file': 'sources.list.d/mitako.list', 
          'pointer': 'deb http://archive.mitako.eu/ jessie main',
          'key': 'http://archive.mitako.eu/archive-mitako.gpg.key' }
        ]

    for repo in repos:
        xpipa.edfile(os.path.join(apt_directory, repo['file']), repo['pointer'])
        rc=xpipa.execute('curl -s -L {} | apt-key add -'.format(repo['key']), pipes=True)
        if rc:
            print 'Error registering repository: {}'.format(repo['pointer'])
            return False

    rc=xpipa.execute('apt-get update')
    return rc==0


def install_additional_software(xpipa, custom_kernel=None):
    '''
    Installs Linux Kernel, RaspberryPI firmware, GPIO libraries, and additional userspace software
    custom_kernel is available at: http://pipaos.mitako.eu/download/kernels/kernel-latest-pipaos.tgz
    '''
    user_packages='screen mc crda raspi-config'
    pipaos_packages='dispmanx-vncserver criu-rpi pifm pipaos-tools rpi-monitor raspi2png'
    core_packages='ssh htop iptraf ifplugd bash-completion ifupdown tcpdump parted fake-hwclock ' \
        'ntp isc-dhcp-client dhcpcd5 usbutils wpasupplicant wireless-tools ifplugd hostapd dnsmasq iw ' \
        'locales console-data kbd console-setup'
    additional_packages = core_packages + ' python python-rpi.gpio python3-rpi.gpio raspi-gpio wiringpi ' \
        'libraspberrypi0 raspberrypi-bootloader libraspberrypi-bin alsa-utils ' \
        'firmware-atheros firmware-brcm80211 firmware-libertas firmware-ralink firmware-realtek ' \
        'firmware-zd1211 raspbian-archive-keyring {} {}'.format(user_packages, pipaos_packages)

    rc=xpipa.execute('DEBIAN_FRONTEND=noninteractive apt-get install -y {}'.format(additional_packages), pipes=True)
    if rc:
        return False

    # Install pipaOS custom linux kernel (RPI3)
    if (custom_kernel):
        cmdline='curl -s -L {} | tar --no-same-owner -zxvf - -C /'.format(custom_kernel)
        xpipa.execute(cmdline, pipes=True)
        xpipa.execute('strings /boot/kernel7.img | grep Linux')

    # Stop automatically started services
    xpipa.execute('/etc/init.d/triggerhappy stop')
    xpipa.execute('/usr/bin/pkill thd')

    # Install copies and fills and stop qemu from loading it.
    ld_preload_file='/etc/ld.so.preload'
    ld_sysroot_preload_file=os.path.join(xpipa.query('sysroot'), ld_preload_file)
    xpipa.execute('apt-get install -y raspi-copies-and-fills')
    xpipa.execute('sudo mv -f {} {}-disabled'.format(
            ld_sysroot_preload_file, os.path.join(xpipa.query('sysroot'), ld_preload_file)))

    # Install rpi-update tool
    rpi_update_url='https://raw.githubusercontent.com/Hexxeh/rpi-update/master/rpi-update'
    xpipa.execute('curl -L --output /usr/bin/rpi-update {} && chmod +x /usr/bin/rpi-update'.format(
        rpi_update_url), pipes=True)

    return True


def root_customize(xpipa):
    '''
    Additional system customizations
    '''
    failures=0
    motd_message='Welcome to pipaOS version {}-{}'.format(pipaos_codename, __version__)
    root_custom_dir='root_customization'
    hostname='pipaos'

    # Override system customization files into /etc and /boot
    failures += os.system('sudo cp -rfv {}/etc {}'.format(root_custom_dir, xpipa.query('sysroot')))
    failures +=os.system('sudo cp -rfv {}/boot {}'.format(root_custom_dir, xpipa.query('sysroot')))

    # insert version in login message
    xpipa.edfile('/etc/motd', motd_message)

    # insert pipaOS version file
    xpipa.edfile('/etc/pipaos_version', 'pipaos-{}-{}'.format(pipaos_codename, __version__))
    xpipa.edfile('/etc/pipaos_version', 'Built: {}'.format(time.ctime()), append=True)

    # generate default input locales
    failures += xpipa.execute('locale-gen')

    # set the correct hostname DNS pointers
    xpipa.edfile('/etc/hostname', hostname)
    xpipa.edfile('/etc/hosts', '127.0.0.1   localhost', append=True)
    xpipa.edfile('/etc/hosts', '127.0.0.1   {}'.format(hostname), append=True)

    # save the host time into the system so we don't default to 1970
    failures += xpipa.execute('fake-hwclock save')

    # force ssh host key regeneration on first boot
    failures += xpipa.execute('insserv regenerate_ssh_host_keys')

    # copy network configuration for first boot
    failures += xpipa.execute('cp -fv /boot/interfaces.txt /etc/network/interfaces')

    return failures == 0


def user_accounts(xpipa):
    '''
    Force root password and create a regular user account
    '''
    root_password='thor'
    sysop_username='sysop'
    sysop_password='posys'
    sysop_groups='tty,adm,dialout,cdrom,sudo,audio,video,plugdev,games,users,input,netdev,gpio,i2c,spi'

    # Create hardware access groups (controlled via udev)
    xpipa.execute('addgroup --system gpio')
    xpipa.execute('addgroup --system i2c')
    xpipa.execute('addgroup --system spi')

    # Create new user accounts
    xpipa.execute('useradd -m -s /bin/bash {}'.format(sysop_username))
    xpipa.execute('echo "{}:{}" | chpasswd'.format(sysop_username, sysop_password), pipes=True)
    xpipa.execute('echo "root:{}" | chpasswd'.format(root_password), pipes=True)
    xpipa.execute('usermod -a -G {} {}'.format(sysop_groups, sysop_username))

    return True
                 

def system_cleanup(xpipa):
    '''
    Empty the APT cache to save disk space on image
    '''
    xpipa.execute('apt-get -y clean')
    xpipa.execute('apt-get -y autoclean')
    return True



if __name__=='__main__':

    start_time=time.time()
    print '>>> pipaOS build starting on {}'.format(time.ctime())
    if len(sys.argv) < 2:
        print 'Please specify the xsysroot profile for pipaos build'
        sys.exit(1)

    # Load the xsysroot profile
    xsysroot_profile=sys.argv[1]
    xpipa=xsysroot.XSysroot(profile=xsysroot_profile)

    if xpipa.is_mounted():
        print '>>> image is currently mounted - aborting'.format(xsysroot_profile)
        sys.exit(1)

    # The image is created only the first time
    backing_image=xpipa.query('backing_image')
    if not os.path.isfile(backing_image):
        if not create_core_image(xpipa):
            print 'Error creating core image - aborting'
            sys.exit(1)

    print '>>> Customizing system...'
    if not xpipa.is_mounted() and not xpipa.mount():
        print 'could not mount the image - aborting'
        sys.exit(1)

    print '>>> Setting up repositories...'
    if not setup_repositories(xpipa):
        print 'Error setting up repositories - aborting'
        exit(1)

    print '>>> Creating a compressed minimal sysroot image'
    pipaos_sysroot_file='pipaos-{}-{}-sysroot64.tar.gz'.format(pipaos_codename, __version__)
    sysroot_cmd='sudo tar -zc -C {} . --exclude="./proc" --exclude="./sys" --exclude="./dev" -f {}'.format(
        xpipa.query('sysroot'), pipaos_sysroot_file)
    rc=os.system(sysroot_cmd)
    if rc:
        print '>>> Warning: failure while compressing minimal sysroot image'

    print '>>> Installing additional software...'
    if not install_additional_software(xpipa):
        print 'warning: errors installing additional software'

    print '>>> System customization...'
    if not root_customize(xpipa):
        print 'warning: errors setting up system accounts'

    print '>>> Setting up system accounts...'
    if not user_accounts(xpipa):
        print 'warning: errors setting up system accounts'

    system_cleanup(xpipa)

    # Unmount image and convert for deployment
    if not xpipa.umount():
        print 'Could not unmount image for deployment - processes still running?'
        sys.exit(1)

    # The output image to burn to the SD card
    pipaos_image_file='pipaos-{}-{}.img'.format(pipaos_codename, __version__)

    # zero free disk space and convert image
    xpipa.zerofree(xpipa.query('nbdev_part'), verbose=False)
    rc=os.system('qemu-img convert {} {}'.format(xpipa.query('qcow_image'), pipaos_image_file))
    if rc:
        print 'Error converting image file {} => {}'.format(xpipa.query('qcow_image'), pipaos_image_file)
        sys.exit(1)

    elapsed_time=time.time() - start_time
    print '>>> pipaOS build completed on {}'.format(time.ctime())
    print '>>> Elapsed time: {} mins'.format(elapsed_time / 60)
    sys.exit(0)
