# LinkedMusic Data Lake

# Indexing and Searching

## Basic Solr Instance

A basic solr instance can easily be created locally for testing indexing functionality. Files for this instance are found in the `solr` directory. 

To build and run the solr instance locally:

```bash
> docker build -t lmdlsolr:latest ./solr
> bash ./solr/solr_run.sh
```

To perform basic queries, and perform administrative tasks on the solr server, visit localhost:8983.

## Basic Indexing Functionality

Basic index functionality is found in the `index_data.py` file. This is theoretically generalized but has only been tested thus far with extracts from Cantus DB, Simssa DB, and the Session. 

To index, make sure a solr instance is running at port 8983, and:

```python
>>> from index_data import index_docs
>>> index_docs('/path/to/jsonld_file')
'Returns response from solr server (eg. 200 = Success)'
```

To delete indexed documents:

```python
>>> from index_data import delete_all_docs
>>> delete_all_docs()
```
