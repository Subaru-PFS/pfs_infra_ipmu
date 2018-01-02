#!/bin/sh

LIST=`psql -l -t | awk -F '|' '{print $1}' | egrep -iv 'template|postgres'`
DB_BACKUP=/server/admin/bin/psql-backup.sh

for i in $LIST
do
   echo [[ DB: $i ]]
   $DB_BACKUP $i
done

