#!/bin/bash

MODULE_FOLDER='/home/led/gh/python/record'

function start_db() {
    if [[ `pg_ctl status | grep -v grep | grep "server is running" | wc -l` = 1 ]]; then
        echo "PostgreSQL is already started."
    else
        echo "PostgreSQL will be started."
        pg_ctl start    
    fi
}

function create_db() {
    dbc=`psql -c "select datname from pg_database where datname='$1';" | grep "1 row" | wc -l`
    if [[ $dbc = 0 ]]; then
        echo "The database '$1' is not created yet. Will create it now."
        createdb $1
    fi
}

function drop_db() {
    dbc=`psql -c "select datname from pg_database where datname='$1';" | grep "1 row" | wc -l`
    if [[ $dbc = 1 ]]; then
        echo "The database '$1' is already created. Will drop it now"
        dropdb $1
    fi
}

function create_tables() {
    fl=`ls -l $MODULE_FOLDER/data/ | awk '{print $9}' | sed '/^$/d' | awk -F "." '{print $1}'`

    #echo $fl $count
    for f in $fl
    do 
      echo $f
      psql $1 -c "CREATE TABLE $f(NAME TEXT PRIMARY KEY NOT NULL,
                             VERSION TEXT NOT NULL,
                             TYPE TEXT,
                             DESCRIPTION TEXT,
                             CONTENT TEXT
                             );" 2>&1>/dev/null
    done
}

function drop_tables() {
    fl=`ls -l $MODULE_FOLDER/data/ | awk '{print $9}' | sed '/^$/d' | awk -F "." '{print $1}'`

    #echo $fl $count
    for f in $fl
    do 
      #echo $f
      psql $1 -c "DROP TABLE $f;" 2>&1>/dev/null
    done
}

function list_db() {
    dbc=`psql $1 -c "select datname from pg_database;"`
    let lc=`echo $dbc | head -n1 | awk -F ' ' '{print NF}'`-2
    dbs=`echo $dbc | sed 's/[ ][ ]*/ /g' | cut -d ' ' -f 3-$lc`
    printf "\033[36m%s\033[0m\n" "`echo $dbc | sed 's/[ ][ ]*/ /g' | cut -d ' ' -f 3-$lc | sed 's/ /\n/g'`"
}

function print_usage() {
    printf "\033[1m\033[31m%s\033[0m\n" "Usage:"
    printf "\033[34m%s\n" " --start postgresql:    # odb"
    printf " --create db:           # odb c <db_name>\n"
    printf " --drop db:             # odb d <db_name>\n"
    printf " --list db:             # odb l\n"
    printf " --create tables:       # odb ct <db_name>\n"
    printf "%s\033[0m\n" " --drop tables:         # odb dt <db_name>"
}

if [[ $# = 1 ]]; then
    case "$1" in
        "l")  list_db;;
        *)    print_usage;;
    esac
elif [[ $# = 2 ]]; then
        case "$1" in
            "c" ) create_db $2;;
            "d" ) drop_db $2;;
            "ct" ) create_tables $2;;
            "dt" ) drop_tables $2;;
            * )   print_usage;;
        esac
else
    print_usage
fi

