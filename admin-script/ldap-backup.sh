#!/bin/sh

SYSTEMD='/bin/systemctl'
SLAPD='slapd.service'

init_slapd() {
    $SYSTEMD $1 $SLAPD
}

PRG=/usr/sbin/slapcat
LDIF=pfs
DB_DIR=/var/lib/ldap
BACK_DIR=/server/backup/ldap

BACK_FILE=$LDIF_`date "+%Y-%m-%d"`.ldif
cd $BACK_DIR
LAST_FILE=`ls -1tr | tail -1`
TEMP_FILE=tmp.ldif

# stop ldap server
init_slapd stop

# Backup from ldap server
$PRG -l $BACK_DIR/$TEMP_FILE
if [ -f $BACK_DIR/$LAST_FILE ]; then
  DIFF_NUM=`diff $BACK_DIR/$TEMP_FILE $BACK_DIR/$LAST_FILE | grep -c "^[<>]"`
else
  DIFF_NUM=1
fi

# Check diff
if [ $DIFF_NUM -ne 0 ]; then
        mv $BACK_DIR/$TEMP_FILE $BACK_DIR/$BACK_FILE
        rm -rf $BACK_DIR/ldap
        cp -Rp $DB_DIR $BACK_DIR/ldap
else
        rm $BACK_DIR/$TEMP_FILE
fi

# start ldap server
init_slapd start

