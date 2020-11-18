#!/bin/bash

ITEM='book-private'
ROOT_DIR=/bwb-monthly
SCRIPT_DIR=${ROOT_DIR}/openlibrary-bots/BWBImportBot

# Set vars for tmp directories and files
printf -v TODAY_DATE_M '%(%Y-%m)T' -1  # today's YYYY-MM
DATE_M=${1:-$TODAY_DATE_M}

echo "Processing $DATE_M ..."

# =============
# Download Data
# =============

# Create dir YYYY-MM
mkdir -p ${ROOT_DIR}/${DATE_M}

# If directory is empty
if [ ! "$(ls -A ${ROOT_DIR}/${DATE_M})" ]
then
  echo "Pulling data from BWB"
  cd ${ROOT_DIR}/${DATE_M}
  # Fetch Monthly Bowker Data into dir YYYY-MM (previously: get-bowker.sh)
  lftp <<EOF
  # Comments can be added like this.
  set ssl:verify-certificate no
  open oplibrary@bwbftps.betterworldbooks.com
  ls
  local echo "== MetaData =="
  ls MetaData
  get MetaData/Awards.zip
  get MetaData/Pub.zip
  get MetaData/Bios.zip
  get MetaData/Bibliographic.zip
  get MetaData/Annotations.zip
  bye
EOF
else
  echo "Skipping: BWB data already fetched..."
fi

# ==================
# Zip & Upload to IA
# ==================
if [[ ! -f "${ROOT_DIR}/UPLOADED/${DATE_M}.zip" ]]
then
  echo "Creating Archival Zip for upload"
  echo "${ROOT_DIR}/UPLOADED/${DATE_M}"
  # Zip YYYY-MM assets into YYYY-MM-DD.zip in UPLOADED dir
  mkdir -p ${ROOT_DIR}/UPLOADED
  cd ${ROOT_DIR}/UPLOADED
  sudo zip ${DATE_M}.zip ${ROOT_DIR}/${DATE_M}/*
else
  echo "Skipping: Archival Zip already exists"
fi

found=$(curl -ILs https://archive.org/download/${ITEM}/${DATE_M}.zip | grep "200 OK" | wc -l)
if [[ $found == 0 ]]
then
  # Upload (3 retries) YYYY-MM-DD.zip to archive.org/details/book-private
  echo "Uploading https://archive.org/download/${ITEM}/${DATE_M}.zip"
  cd ${ROOT_DIR}/UPLOADED
  ia upload --retries 3 ${ITEM} ${DATE_M}.zip
else
  echo "Skipping: Upload (file already exists)"
fi

# ============
# Process Data
# ============
cd ${ROOT_DIR}/${DATE_M}
if [ ! -d "${ROOT_DIR}/${DATE_M}/Bibliographic" ]
then
  echo "Unzipping Bibliographic.zip"
  sudo unzip Bibliographic.zip
else
  echo "Skipping: Bibliographic already unzipped"
fi

# Change into the Bibliographic data dir
cd ${ROOT_DIR}/${DATE_M}/Bibliographic/* # e.g. cd into Bibliographic/2020-07-07

# Extract from BWB format to OL json & detect duplicate isbns
if [[ ! -f "${ROOT_DIR}/${DATE_M}/Bibliographic/books.jsonl" ]]
then
  echo "Generating books.jsonl seed list"
  sudo -E sh -c "${ROOT_DIR}/venv/bin/python ${SCRIPT_DIR}/parse-biblio.py ${ROOT_DIR}/${DATE_M}/Bibliographic/*/bettworldbks* > ${ROOT_DIR}/${DATE_M}/Bibliographic/books.jsonl"
else
  echo "Skipping: books.jsonl already detected"
fi

# ============
# import to OL
# ============
sudo -E sh -c "${ROOT_DIR}/venv/bin/python ${SCRIPT_DIR}/import-ol.py ${ROOT_DIR}/${DATE_M}/Bibliographic/books.jsonl > ${ROOT_DIR}/${DATE_M}/Bibliographic/import.log"
