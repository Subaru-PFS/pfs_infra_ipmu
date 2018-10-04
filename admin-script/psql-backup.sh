#!/bin/sh

backup_single() {

    DB=$1
    BACKUP_DIR=/server/backup/pgsql/$DB

    BACKUP_FILE=$DB\_`date "+%Y-%m-%d"`.custom
    TEMP_FILE=tmp.bak

    # check args
    if [ -z $1 ] ; then
        return 0
    fi

    # check directory
    if [ ! -d $BACKUP_DIR ]; then
        mkdir -p $BACKUP_DIR
    fi
    LAST_FILE=`ls -1tr $BACKUP_DIR | grep -e $DB -e .custom | tail -1`

    # backup from database
    pg_dump --format=custom $DB > $BACKUP_DIR/$TEMP_FILE

    # check database update
    if [ -z $LAST_FILE ]; then
        DIFF_NUM=1
    else
        OLD_FSIZE=`wc -c $BACKUP_DIR/$LAST_FILE | cut -d' ' -f1`
        NEW_FSIZE=`wc -c $BACKUP_DIR/$TEMP_FILE | cut -d' ' -f1`
        if [ $OLD_FSIZE -ne $NEW_FSIZE ]; then
            DIFF_NUM=1
        else
            DIFF_NUM=`diff $BACKUP_DIR/$TEMP_FILE $BACKUP_DIR/$LAST_FILE \
                | grep -v "^< -- Dump completed on" \
                | grep -c "<"`
        fi
    fi

    if [ $DIFF_NUM -ne 0 ]; then
        echo "new"
        mv $BACKUP_DIR/$TEMP_FILE $BACKUP_DIR/$BACKUP_FILE
    else
        echo "stable"
        rm $BACKUP_DIR/$TEMP_FILE
    fi

}

LIST=`psql -l -t | awk -F '|' '{print $1}' | egrep -iv 'template|postgres'`

for i in $LIST
do
   echo [[ DB: $i ]]
   backup_single $i
done

