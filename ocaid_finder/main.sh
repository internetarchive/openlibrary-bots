#!/bin/bash

if [[ -z $1 ]]
  then
    echo "No edition dump file provided"
    exit 1
fi
if [[ -z $2 ]]
  then
    echo "No output file name provided"
    exit 1
fi
if [[ -z $3 ]]
  then
    echo "No output file name provided"
    exit 1
fi

EDITION_DUMP_PATH=$1
MISSING_OCAID_DUMP_PATH=$2
MALFORMED_EDITIONS_DUMP_PATH=$3

echo "Saving editions with Internet Archive scans but no ocaid..."
bash no_ocaid_filter.sh $EDITION_DUMP_PATH $MISSING_OCAID_DUMP_PATH
echo "Saving editions that need to be updated..."
python missing_ocaid_finder.py $MISSING_OCAID_DUMP_PATH $MALFORMED_EDITIONS_DUMP_PATH