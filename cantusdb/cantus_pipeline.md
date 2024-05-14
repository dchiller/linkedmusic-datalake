# CantusDB flattening and json-ld structures

> Summarize:    
>   1. Reconcile the flattened csv dump
>   2. With the output run `jsonld/generate_jsonld.py`(which also takes `jsonld/context.jsonld` as an input)

I was provided with a csv file of 50 entries of CantusDB
Since each lines represent a chant_id already, there was no need to flatten like simssadb. 

## 1. Reconciliation with OpenRefine
I performed OpenRefine reconciliation with 3 columns: **genre, mode_name, and composer** (which defaulted to Anonymous since all values of this column is so)
I then generate the csv with the corresponding wikidata IDs in the reconciled cells 
You can use `openrefine/history.json` to apply reconciliation steps and `openrefine/export_template.json` to export the file.  

## 2. Reconcile column names and generating json-ld
Currently the json-ld is generated as follow:
In `jsonld/generate_jsonld.py`
- Load the reconciled csv as a dataframe in pandas and convert them to json documents (each corresponds to an entry/line in the csv)
- Loop through each json document and edit each entry, creating the compact jsonld. More information can be found in `generate_jsonld.py`
- Generate the jsonld file at `compact.jsonld`
- The contexts used in the compact.jsonld file is imported from `context.jsonld`
