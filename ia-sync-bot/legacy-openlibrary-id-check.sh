#!/bin/bash

# Some Archive.org items have old-style `openlibrary` IDs, and no `openlibrary-edition`.
# Many of these OL editions don't have `ocaid`
#    https://github.com/internetarchive/openlibrary/issues/1046
# This scripts collects data from archive.org and openlibrary.org and creates lists and stats
# for the various categories.


# Test for Open Library edition dump file in current dir:

ol_dump="ol_dump_editions_latest.txt"

if [ ! -f "$ol_dump" ]; then
  echo ""
  echo "Open Library Editions dump file '$ol_dump' not found!"
  echo "Please download and extract it to the current directory by running the following commands:"
  echo "  wget https://openlibrary.org/data/ol_dump_editions_latest.txt.gz"
  echo "  gunzip ol_dump_editions_latest.txt.gz"
  exit 1
fi

# Get IA items with only legacy field:
echo " Getting list of archive.org items with only a legacy openlibrary field..."
ia search "openlibrary:* AND NOT openlibrary_edition:*" -f"openlibrary" > legacy-openlibrary-field.txt

# Extract OLIDs
egrep -o "OL[0-9]+M" legacy-openlibrary-field.txt > legacy-linked-olids.lst

# Get data of all uniq editions referenced by archive.org items with only legacy openlibrary field:
grep -Ff legacy-linked-olids.lst $ol_dump > legacy-linked-dump.txt

# Count of uniq editions referenced by archive.org items with only legacy openlibrary field.
legacy_linked=$(wc -l legacy-linked-dump.txt)

# How many of these are orphans?
orphans=$(grep -vc '"works":' legacy-linked-dump.txt)

# How many already have ocaids?
have_ocaid=$(grep -c '"ocaid"' legacy-linked-dump.txt)

# How many don't have ocaids:
no_ocaid=$(grep -vc '"ocaid"' legacy-linked-dump.txt)


echo "Report $(date):"
echo "Uniq editions referenced by archive.org items with only legacy openlibrary field"
echo " Total: $legacy_linked"
echo " Orphans: $orphans"
echo " No OCAID: $no_ocaid"

