#!/bin/bash

if [[ `pg_ctl status | grep -v grep | grep "server is running" | wc -l` = 1 ]]; then
    echo "PostgreSQL is already started."
else
    echo "PostgreSQL will be started."
    pg_ctl start    
fi

if [[ `psql -c '\l' | grep $1 | wc -l` = 0 ]]; then
    echo "The database '$1' is not created yet."
    createdb $1
else
    echo "The database '$1' is already created."
fi

