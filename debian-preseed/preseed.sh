#! /bin/sh

export ISO_IMAGE=$1
export PRESEED_CFG=$2

# config
export ORIG_ISO='./iso_orig/'
export TEMP_ISO='./iso_temp/'
export IRMOD='./iso_irmod/'
export INST_TGT='install.amd'

echo "Using original iso: $ISO_IMAGE"
echo "Using preseed.cfg : $PRESEED_CFG"

if [ ! -e $ISO_IMAGE ]; then
    echo "Source iso image $ISO_IMAGE does not exist"
    exit
fi
if [ ! -e $PRESEED_CFG ]; then
    echo "Source preseed.cfg $PRESEED_CFG does not exist"
    exit
fi
if [ -e $ORIG_ISO ]; then
    echo "Directory $ORIG_ISO exists."
    exit
fi
if [ -e $TEMP_ISO ]; then
    echo "Directory $TEMP_ISO exists."
    exit
fi
if [ -e $IRMOD ]; then
    echo "Directory $IRMOD exists."
    exit
fi

mkdir $ORIG_ISO $TEMP_ISO
sudo mount -o loop $ISO_IMAGE $ORIG_ISO
rsync -a -H --exclude=TRANS.TBL $ORIG_ISO $TEMP_ISO
sudo umount $ORIG_ISO
rmdir $ORIG_ISO
chmod -R u+w $TEMP_ISO

mkdir $IRMOD
cd $IRMOD
cp ../$PRESEED_CFG ./preseed.cfg
gunzip ../$TEMP_ISO/install.amd/initrd.gz
echo 'preseed.cfg' | cpio -o -H newc -A -F ../$TEMP_ISO/install.amd/initrd
gzip -9 ../$TEMP_ISO/install.amd/initrd
cd ../

cd $TEMP_ISO
mv isolinux/isolinux.cfg isolinux/isolinux.cfg.oirg
cat << EOS > isolinux/isolinux.cfg
# D-I config version 2.0
# search path for the c32 support libraries (libcom32, libutil etc.)
path 
default vesamenu.c32
prompt 0
timeout 20
label install
	menu label ^Install
	kernel /install.amd/vmlinuz
	append vga=788 initrd=/install.amd/initrd.gz --- quiet 
EOS
md5sum `find -follow -type f` > md5sum.txt
cd ../

genisoimage -o $PRESEED_CFG.iso -r -J -no-emul-boot -boot-load-size 4 \
    -quiet \
    -boot-info-table -b isolinux/isolinux.bin -c isolinux/boot.cat $TEMP_ISO

