import json
from pyld import jsonld
import requests

def parse_json_file(json_file: str, expand: bool = False):
    with open(json_file) as f:
        data: list = json.load(f)
    if expand:
        data = jsonld.expand(data)
    return data

def post_docs_to_solr(docs: list):
    solr_url: str = "http://localhost:8983/solr/test_core/update/json/"
    headers: dict = {"Content-type": "application/json"}
    update_json: dict = {"add": docs, "commit": {}}
    r = requests.post(solr_url, json=update_json, headers=headers)
    return r.status_code

def _map_key_types(key: str):
    return f"{key}_s"

def _prep_doc_keys(doc):
    prepped_doc = {}
    if "@context" in doc:
        doc.pop("@context")
    prepped_doc["@id"] = doc.pop("@id")
    prepped_doc["@type"] = doc.pop("@type")
    for key, val in doc.items():
        if not val:
            continue
        if isinstance(val, list):
            prepped_rec_docs = [_prep_doc_keys(val_item) for val_item in val]
            prepped_doc[key] = prepped_rec_docs
        else:
            prepped_doc[_map_key_types(key)] = val
    return prepped_doc

def index_docs(jsonld_file_path):
    data = parse_json_file(jsonld_file_path, expand=False)
    docs = [_prep_doc_keys(doc) for doc in data]
    post_status = post_docs_to_solr(docs)
    return post_status

def delete_all_docs():
    solr_url: str = "http://localhost:8983/solr/test_core/update/json/"
    headers: dict = {"Content-type": "application/json"}
    update_json: dict = {"delete": {"query": "*:*"}, "commit": {}}
    r = requests.post(solr_url, json=update_json, headers=headers)
    return r.status_code
