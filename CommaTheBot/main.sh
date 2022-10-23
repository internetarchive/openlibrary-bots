#!/bin/bash

# init
python -m venv venv;
cp CommaTheBot.py requirements.txt venv/;
cd venv

source bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# dl latest dump
curl https://openlibrary.org/data/ol_dump_latest.txt.gz -O

# prefilter it
file=( ol_dump*.gz )
zgrep -E "^/type/(?:edition|work)" "$file" | pv | gzip > "filtered_$file"

python CommaTheBot.py --file "filtered_$file" "$@"
