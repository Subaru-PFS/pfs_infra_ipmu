#!/bin/sh

MYSQL_CONNOPT="--defaults-file=/etc/mysql/debian.cnf"
BACKUP_ROOT='/server/backup/mysql/'

backup_single() {

    DB=$1
    BACKUP_DIR=$BACKUP_ROOT$DB

    BACKUP_FILE=$DB\_`date "+%Y-%m-%d"`.sql
    TEMP_FILE=tmp.bak

    # check args
    if [ -z $1 ] ; then
        return 1
    fi

    # check directory
    if [ ! -d $BACKUP_DIR ]; then
        mkdir -p $BACKUP_DIR
    fi
    LAST_FILE=`ls -1tr $BACKUP_DIR | grep -e $DB -e .sql | tail -1`

    # backup from database
    mysqldump $MYSQL_CONNOPT -r $BACKUP_DIR/$TEMP_FILE --opt $DB

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
}

LIST=`mysqlshow $MYSQL_CONNOPT | cut -d' ' -f 2 | egrep -iv 'information_schema|performance_schema|mysql|test|-'`

for i in $LIST
do
   echo [[ DB: $i ]]
   backup_single $i
done


