#!/bin/sh

USER=$1
DB=$2
#BACKUP_DIR=/root/mysql-backup/$DB
BACKUP_DIR=/server/backup/mysql/$DB

BACKUP_FILE=$DB\_`date "+%Y-%m-%d"`.sql
TEMP_FILE=tmp.bak

# check args
if [ -z $1 ] || [ -z $2 ]; then
    echo "Usage: backup-mysql.sh USERNAME DBNAME"
    exit 0
fi

# check directory
if [ ! -d $BACKUP_DIR ]; then
    mkdir -p $BACKUP_DIR
fi
LAST_FILE=`ls -1tr $BACKUP_DIR | grep -e $DB -e .sql | tail -1`

# backup from database
mysqldump -u $USER -r $BACKUP_DIR/$TEMP_FILE --opt $DB

# check database update
if [ -z $LAST_FILE ]; then
    DIFF_NUM=1
else
    DIFF_NUM=`diff $BACKUP_DIR/$TEMP_FILE $BACKUP_DIR/$LAST_FILE \
        | grep -v "^< -- Dump completed on" \
        | grep -c "<"`
fi

if [ $DIFF_NUM -ne 0 ]; then
    echo "new"
    mv $BACKUP_DIR/$TEMP_FILE $BACKUP_DIR/$BACKUP_FILE
else
    echo "stable"
    rm $BACKUP_DIR/$TEMP_FILE
fi
