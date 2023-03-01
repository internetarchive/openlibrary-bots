#!/bin/bash
if [[ -z $1 ]]
  then
    echo "No dump file provided"
    exit 1
fi
if [[ -z $2 ]]
  then
    echo "No output file provided"
    exit 1
fi

OL_DUMP=$1
OUTPUT=$2

echo "#"
echo "# Pass 1 of 2: Find Internet Archive scans with no 'covers' key"
echo "#"
echo ""

pv "$OL_DUMP" | zgrep ^/type/edition | grep '"ocaid":' | grep -v '"covers":' | gzip > "$OUTPUT"

echo ""
echo "#"
echo "# Pass 2 of 2: Find Internet Archive scans with invalid cover"
echo "#"
echo ""
pv "$OL_DUMP" | zgrep ^/type/edition | grep '"ocaid":' | grep -E -e '"covers": \[(-1|null)\]|"covers": \[(-1, null|null, -1)\]' | gzip >> "$OUTPUT"
