#!/bin/sh

LIST=`mysqlshow | cut -d' ' -f 2 | egrep -iv 'information_schema|performance_schema|mysql|test|-'`
DB_BACKUP=/server/admin/bin/mysql-backup.sh

for i in $LIST
do
   echo [[ DB: $i ]]
   $DB_BACKUP root $i
done

