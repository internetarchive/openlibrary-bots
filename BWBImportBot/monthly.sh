ITEM='book-private'
ROOT_DIR=/bwb-monthly
SCRIPT_DIR=${ROOT_DIR}/openlibrary-bots/BWBImportBot

# Set vars for tmp directories and files
printf -v DATE_M '%(%Y-%m)T'    -1  # sets $DATE_M
printf -v DATE_D '%(%Y-%m-%d)T' -1  # sets $DATE_D

# =============
# Download Data
# =============

# Create dir YYYY-MM
mkdir -p ${ROOT_DIR}/${DATE_M}
cd $DATE_M

# Fetch Monthly BWB Data into dir YYYY-MM
lftp <<EOF
- DL
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
DL

EOF

# ============
# Upload to IA
# ============

# Zip YYYY-MM assets into YYYY-MM-DD.zip in UPLOADED dir
mkdir -p ${ROOT_DIR}/UPLOADED
cd ${ROOT_DIR}/UPLOADED
sudo zip ${DATE_D}.zip ${ROOT_DIR}/${DATE_M}/*

# Upload YYYY-MM-DD.zip to archive.org/details/book-private
ia upload $ITEM ${DATE_D}.zip

# ============
# Process Data
# ============

cd ${ROOT_DIR}/${DATE_M}
sudo unzip Bibliographic.zip
cd Bibliographic/* # e.g. cd into Bibliographic/2020-07-07

# Extract from BWB format to OL Json & detect duplicate isbns
sudo sh -c '${ROOT_DIR}/venv/bin/python ${SCRIPT_DIR}/parse-biblio.py bettworldbks* > books.jsonl'

# ============
# import to OL
# ============

sudo sh -c '${ROOT_DIR}/venv/bin/python ${SCRIPT_DIR}/import-ol.py books.jsonl > import.log'
