# Files for PFS Server system operation

## tools on libvirt (libvirt)
Tools to monitor and operate VM instances via qemu+tls

## debian preseed configuration (debian-preseed)
Configuration files for setup Linux by Debian preseed.
Assumed to be used on bulding new instance on virt.

### usage

* sudo virsh start XXXX
* sudo virsh attach-device XXXX XXXX.xml
* 'Send Ctrl+Alt+Del' from spice
* 'Advanced Options' -> 'Automated install'
* At 'Download debconf preconfiguration file', put URL of configuration
* VM will shutdown after installation
* Start again, change password of 'pfs'

### list of configurations

* [Stretch](/debian-preseed/stretch.preseed.cfg)

## Chef configuration (chef)
Software configuration codes on Chef.

