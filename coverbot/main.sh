#!/bin/bash
if [[ -z $1 ]]
  then
    echo "No dump file provided"
    exit 1
fi
if [[ -z $2 ]]
  then
    echo "No filtered dump output path provided"
    exit 1
fi
if [[ -z $3 ]]
  then
    echo "No fixed dump output path provided"
    exit 1
fi

OL_DUMP=$1
FIXED_OL_DUMP=$2
FIXED_EDITIONS_DUMP=$3

bash find_coverless_editions_in_library.sh $OL_DUMP $FILTERED_OL_DUMP
python cover_updater.py $FILTERED_OL_DUMP $FIXED_EDITIONS_DUMP