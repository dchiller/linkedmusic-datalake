import json
import requests

def parse_json_file(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data

def post_docs_to_solr(docs):
    solr_url = 'http://localhost:8983/solr/test_core/update/json/'
    headers = {'Content-type': 'application/json'}
    update_json = {"add": docs, "commit": {}}
    r = requests.post(solr_url, json=update_json, headers=headers)
    return r.status_code

def index_docs_cantusdb(file_path):
    data = parse_json_file(file_path)
    drop_keys = ["@context"]
    for doc in data:
        for key in drop_keys:
            if key in doc:
                del doc[key]
    field_mapper = {
        "volpiano": "volpiano_t",
        "@id": "id",
        "@type": "type",
        "database": "database_s",
        "P86": "P86_s", # Composer
        "P1922": "P1922_s", # Incipit
        "P136": "P136_s", # Genre
        "Q731978": "Q731978_s", # Mode
        "Q4484726": "Q4484726_s", # Final
        "source": "source_s",
    }
    docs = [dict((field_mapper[key], value) for (key, value) in doc.items()) for doc in data]
    post_status = post_docs_to_solr(docs)
    return post_status

def index_docs_simssadb(file_path):
    data = parse_json_file(file_path)
    drop_keys = ["@context"]
    for doc in data:
        for key in drop_keys:
            if key in doc:
                del doc[key]
    field_mapper = {
        "@id": "id",
        "@type": "type",
        "database": "database_s",
        #"P86": "P86_ss", # Composer
        "P136": "P136_s", # Genre
        "P1476": "P1476_s", # Title
        "P2701": "P2701_s", # File type,
        "P214": "P214_i", # VIAF ID
        "Last_Pitch_Class": "Last_Pitch_Class_s",
    }
    docs = []
    for doc in data:
        new_doc = {}
        new_doc["P86_ss"] = [value for value in doc["P86"].values()]
        new_doc["files"] = [dict((field_mapper[key], value) for (key, value) in file.items()) for file in doc["files"]]
        for key, value in field_mapper.items():
            if key in doc:
                new_doc[value] = doc[key]
        docs.append(new_doc)
        print(new_doc)
    post_status = post_docs_to_solr(docs)
    return post_status