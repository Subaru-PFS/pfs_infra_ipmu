#! /bin/sh

SOURCE=$1
OUTDIR=$2
URI=$3
OUTNAME=`date '+%Y%m%d-%H%M'`

echo "Start $SOURCE for $URI"
echo "Output $OUTDIR/$OUTNAME"

visitors -GKZWMRDXYS -m 30 $SOURCE --trails --prefix $URI -o html > $OUTDIR/$OUTNAME.html
visitors $SOURCE --prefix http://pfs.ipmu.jp -V > $OUTDIR/$OUTNAME.dot
dot -Tpng $OUTDIR/$OUTNAME.dot > $OUTDIR/$OUTNAME.png

