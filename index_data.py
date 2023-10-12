import json
from pyld import jsonld
import requests

_TYPE_MAPPINGS = {
    "http://www.w3.org/2001/XMLSchema#dateTime": "dt",
}

_AUTHORITY_MAPPINGS = {
    "http://www.wikidata.org/entity/": "wd",
    "http://www.wikidata.org/prop/direct/": "wdt",
    "https://schema.org/": "schema",
    "https://cantusdatabase.org/chant/": "cdb_chant",
    "https://cantusdatabase.org/source/": "cdb_source",
    "https://cantusdatabase.org/about/": "cdb",
    "https://cantusindex.org/id/": "cid",
    "https://db.simssa.ca/files/": "simssadb_file",
    "https://db.simssa.ca/musicalworks/": "simssadb_musicalwork",
    "https://thesession.org/tunes/": "thesession_tune",
    "https://thesession.org/tunes/popular/": "thesession_popular",
}


def parse_json_file(json_file: str) -> list:
    with open(json_file) as f:
        data: list = json.load(f)
    data = jsonld.expand(data)
    return data


def post_docs_to_solr(docs: list):
    solr_url: str = "http://localhost:8983/solr/test_core/update/json/"
    headers: dict = {"Content-type": "application/json"}
    update_json: dict = {"add": docs, "commit": {}}
    r = requests.post(solr_url, json=update_json, headers=headers)
    return r.status_code


def _map_key_types(key: str):
    key_suffix = _TYPE_MAPPINGS.get(key)
    if key_suffix:
        return f"{key}_{key_suffix}"
    return f"{key}_s"


def _prefix_keys(key: str):
    rl_prefix = "/".join(key.split("/")[0:-1]) + "/"
    try:
        new_key_prefix = _AUTHORITY_MAPPINGS[rl_prefix]
    except KeyError:
        print(rl_prefix)
        print("Ensure that all keys are prefixed with a known authority")
    new_key_prefix = new_key_prefix.rstrip("_")
    new_key = f"{new_key_prefix}_{key.split('/')[-1]}"
    return new_key


def _prep_doc_keys(doc):
    prepped_doc = {}
    prepped_doc["@id"] = doc.pop("@id")
    prepped_doc["@type"] = doc.pop("@type")[0]
    for key, val in doc.items():
        key = _prefix_keys(key)
        if len(val) > 1:
            prepped_rec_docs = [_prep_doc_keys(val_item) for val_item in val]
            prepped_doc[key] = prepped_rec_docs
        elif len(val) == 0:
            continue
        elif isinstance(val[0], dict):
            val_dict = val[0]
            if "@id" in val_dict:
                prepped_doc[f"{key}_s"] = val_dict["@id"]
            elif "@value" in val_dict:
                key_to_index = (
                    _map_key_types(key) if "@type" in val_dict else f"{key}_t"
                )
                val_to_index = val_dict["@value"]
                prepped_doc[key_to_index] = val_to_index
    return prepped_doc


def index_docs(jsonld_file_path):
    data = parse_json_file(jsonld_file_path)
    docs = [_prep_doc_keys(doc) for doc in data]
    post_status = post_docs_to_solr(docs)
    return post_status


def delete_all_docs():
    solr_url: str = "http://localhost:8983/solr/test_core/update/json/"
    headers: dict = {"Content-type": "application/json"}
    update_json: dict = {"delete": {"query": "*:*"}, "commit": {}}
    r = requests.post(solr_url, json=update_json, headers=headers)
    return r.status_code
