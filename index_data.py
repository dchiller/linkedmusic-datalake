import json
from pyld import jsonld
import requests


class LDIndexer:
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

    _SIMILAR_TERMS_LIST = [
        [
            "http://www.wikidata.org/prop/direct/P826",
            "http://www.wikidata.org/entity/Q731978",
            "http://www.wikidata.org/entity/Q4484726",
        ],
    ]

    def __init__(self):
        self.items_wdid = set()
        self.props_wdid = set()

    def parse_json_file(self, json_file: str) -> list[dict]:
        """
        Open and expand a JSON-LD file with a remote context.

        Parameters
        ----------
        json_file: str
            Path to JSON-LD file

        Returns
        -------
        list
            List of dictionaries representing JSON-LD data
        """
        with open(json_file, encoding="utf-8") as f:
            data: list = json.load(f)
        data = jsonld.expand(data)
        return data

    def post_docs_to_solr(self, docs: list) -> int:
        """
        Makes POST request to solr with documents to index.

        Parameters
        ----------
        docs: list
            List of dictionaries representing JSON-LD data

        Returns
        -------
        int
            Status code of POST request
        """
        solr_url: str = "http://localhost:8983/solr/test_core/update/json/"
        headers: dict = {"Content-type": "application/json"}
        update_json: dict = {"add": docs, "commit": {}}
        r = requests.post(solr_url, json=update_json, headers=headers, timeout=20)
        return r.status_code

    def _map_key_types(self, key: str):
        key_suffix = self._TYPE_MAPPINGS.get(key)
        if key_suffix:
            return f"{key}_{key_suffix}"
        return f"{key}_s"

    def _prefix_keys(self, key: str):
        rl_prefix = "/".join(key.split("/")[0:-1]) + "/"
        try:
            new_key_prefix = self._AUTHORITY_MAPPINGS[rl_prefix]
        except KeyError:
            print(rl_prefix)
            print("Ensure that all keys are prefixed with a known authority")
        new_key_prefix = new_key_prefix.rstrip("_")
        new_key = f"{new_key_prefix}_{key.split('/')[-1]}"
        return new_key

    def _prep_doc_keys(self, doc):
        prepped_doc = {}
        prepped_doc["@id"] = doc.pop("@id")
        prepped_doc["@type"] = doc.pop("@type")[0]
        for key, val in doc.items():
            key = self._prefix_keys(key)
            if key.startswith("wd"):
                self.props_wdid.add(key)
            if len(val) > 1:
                prepped_rec_docs = [self._prep_doc_keys(val_item) for val_item in val]
                prepped_doc[key] = prepped_rec_docs
            elif len(val) == 0:
                continue
            elif isinstance(val[0], dict):
                val_dict = val[0]
                if "@id" in val_dict:
                    prepped_doc[f"{key}_s"] = val_dict["@id"]
                    if "www.wikidata.org" in val_dict["@id"]:
                        self.items_wdid.add(val_dict["@id"])
                if "@value" in val_dict:
                    key_to_index = (
                        self._map_key_types(key) if "@type" in val_dict else f"{key}_t"
                    )
                    val_to_index = val_dict["@value"]
                    prepped_doc[key_to_index] = val_to_index
                if "http://www.wikidata.org/entity/P2561" in val_dict:
                    prepped_doc[f"{key}_t"] = val_dict[
                        "http://www.wikidata.org/entity/P2561"
                    ][0]["@value"]
        return prepped_doc

    def index_wd_labels(self, entity_type: str):
        if entity_type == "item":
            wd_ids = [wd_url.split("/")[-1] for wd_url in self.items_wdid]
        elif entity_type == "prop":
            wd_ids = [prefixed_key.split("_")[-1] for prefixed_key in self.props_wdid]
        idx_as_type = f"ld_{entity_type}"
        docs = []
        for i in range(0, len(wd_ids), 50):
            wd_ids_slice = wd_ids[i : i + 50]
            wd_ids_str = "|".join(wd_ids_slice)
            wd_api_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={wd_ids_str}&format=json&props=labels|aliases"
            r = requests.get(wd_api_url).json()
            r_entities = r["entities"]
            for wd_id, res in r_entities.items():
                labels = [label["value"] for key, label in res["labels"].items()]
                alias_list = []
                for lang, lang_aliases in res["aliases"].items():
                    alias_list.extend([alias["value"] for alias in lang_aliases])
                labels.extend(alias_list)
                doc = {"@id": wd_id, "@type": idx_as_type, "wd_label_txt": labels}
                docs.append(doc)
        post_status = self.post_docs_to_solr(docs)
        return post_status

    def index_docs(self, jsonld_file_path):
        data = self.parse_json_file(jsonld_file_path)
        docs = [self._prep_doc_keys(doc) for doc in data]
        post_status = self.post_docs_to_solr(docs)
        return post_status

    def delete_all_docs(self):
        solr_url: str = "http://localhost:8983/solr/test_core/update/json/"
        headers: dict = {"Content-type": "application/json"}
        update_json: dict = {"delete": {"query": "*:*"}, "commit": {}}
        r = requests.post(solr_url, json=update_json, headers=headers, timeout=20)
        return r.status_code

    def index_similar_terms(self):
        similar_terms_objs = []
        for term_group in self._SIMILAR_TERMS_LIST:
            for term in term_group:
                term_dict = {
                    "@id": term,
                    "@type": "ld_similar_terms",
                    "wdt_P460": [
                        {"@id": other_term, "@type": "ld_similar_terms"}
                        for other_term in term_group
                        if other_term != term
                    ],
                }
                similar_terms_objs.append(term_dict)
        post_status = self.post_docs_to_solr(similar_terms_objs)
        return post_status
