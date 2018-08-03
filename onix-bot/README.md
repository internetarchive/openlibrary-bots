# ONIX Bot

## Description
This Bot does the following tasks:
* Validates and check if its a correct ONIX Record.
* Extracts product records from the ONIX Record and check if a duplicate does exist on Open Library.
* Add records which do not exist to Open Library.

### General Scripts
- onixparser.py

### Data dependent Scripts
None

## Steps followed:
* Install requirements using pip with the following commands.
```
cd onix-bot/
pip install -r requirements.txt
```

* **Using a default file**: Run the following command to run the file on a test ONIX Record which can be found [here](https://storage.googleapis.com/support-kms-prod/SNP_EFDA74818D56F47DE13B6FF3520E468126FD_3285388_en_v2).

```bash
python onixparser.py
```

* **Using a custom ONIX File**: Run the following command to run the script on a custom file.
```bash
python onixparser.py <custom-file>.xml
```

## Next Steps for ONIX Bot
1. Use ONIX Reference Code List to parse and obtain Language Codes - [#19](https://github.com/internetarchive/openlibrary-bots/issues/19)
2. Add functionalities to ONIX Bot - [#12](https://github.com/internetarchive/openlibrary-bots/issues/12)
3. Using iterparse to avoid running out of memory errors - [#17](https://github.com/internetarchive/openlibrary-bots/issues/17)