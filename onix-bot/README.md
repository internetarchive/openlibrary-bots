# ONIX Bot

## Description
This Bot is used for parsing ONIX files

### General Scripts
- onixparser.py

### Data dependent Scripts
None

## Steps followed:
* **Using a default file**: Run the following command to run the file on a test ONIX Record which can be found [here](https://storage.googleapis.com/support-kms-prod/SNP_EFDA74818D56F47DE13B6FF3520E468126FD_3285388_en_v2).

```bash
python onixparser.py
```

* **Using a custom ONIX File**: Run the following command to run the script on a custom file.
```bash
python onixparser.py <custom-file>.xml
```