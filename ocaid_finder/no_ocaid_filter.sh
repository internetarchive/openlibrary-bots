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

EDITION_DUMP_PATH=$1
MISSING_OCAID_DUMP_PATH=$2
pv $EDITION_DUMP_PATH | zgrep -v '"ocaid":' | zgrep -E '("ia_loaded_id|"ia:)' | gzip > $MISSING_OCAID_DUMP_PATH