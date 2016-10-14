# Kyrkosok.se Database

This application creates the database for the Kyrkosok.se API backend.

## Requirements

 - PAWS(`paws.wmflabs.org`)
 - KSamsok-py(`pip install ksamsok`)

## Usage

Running this on PAWS should take about 50 minutes and your PyWikiBot config file should be set to Wikidata.

```
python index_database.py
```

The generated file should be created in the same directory, wait until the script prints `Done` before you download the new database. For running the script a second time you will need to remove the generated SQLite database.