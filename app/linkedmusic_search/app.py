from flask import Flask, render_template, request
import requests
from pyld import jsonld

app = Flask(__name__)

FIELDS_TO_REMOVE = [
    "@id",
    "@type",
    "_version_",
    "_root_",
    "_nest_parent_",
    "text_txt",
    "wd_label_txt",
]


def get_labels(wd_ids, include_aliases=False):
    label_qs = "|".join(wd_ids)
    if include_aliases:
        wd_api_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={label_qs}&format=json&props=labels|aliases&languages=en"
    else:
        wd_api_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={label_qs}&format=json&props=labels&languages=en"
    r = requests.get(wd_api_url).json()
    r_entities = r["entities"]
    labels = {}
    for wd_id, res in r_entities.items():
        labels[wd_id] = [res["labels"]["en"]["value"]]
        if include_aliases:
            aliases = [alias["value"] for alias in res["aliases"]["en"]]
            labels[wd_id].extend(aliases)
    return labels


def prepare_results(results):
    prepped_results = []
    fields_to_label = set()
    for res_doc in results:
        prepped_res = {}
        prepped_res["link"] = res_doc.pop("@id")
        prepped_res["type"] = res_doc.pop("@type").split("/")[-1]
        if prepped_res["type"] != "":
            fields_to_label.add(prepped_res["type"])
        prepped_res["int_metadata"] = []
        prepped_res["metadata"] = []
        for field in res_doc:
            if field.startswith("wd") and field.endswith("_t"):
                wd_id = field.split("_")[1]
                prepped_res["int_metadata"].append((wd_id, res_doc[field]))
                fields_to_label.add(wd_id)
        prepped_results.append(prepped_res)
    field_label_dict = get_labels(fields_to_label)
    for res in prepped_results:
        if res["type"]:
            res["type"] = field_label_dict[res["type"]][0]
        for metadata_tup in res["int_metadata"]:
            res["metadata"].append((field_label_dict[metadata_tup[0]], metadata_tup[1]))
    return prepped_results


def query_solr(search_string, search_fields, search_type):
    if search_fields:
        filter_q_search_fields = []
        q_search_fields = []
        for search_field in search_fields:
            search_field = (
                f"wdt_{search_field}"
                if search_field.startswith("P")
                else f"wd_{search_field}"
            )
            filter_q_search_fields.append(f"{search_field}_s")
            q_search_fields.append(f"{search_field}_t")
    else:
        filter_q_search_fields = ["text_ss"]
        q_search_fields = ["text_txt"]
    rec_query = f"http://solr:8983/solr/test_core/select?q=wd_label_txt:{search_string}&fq=@type:ld_item&wt=json"
    rec_results = requests.get(rec_query).json()["response"]["docs"]
    filter_query_add = ""
    if rec_results:
        filter_query_add = [
            f'{filter_q_search_field}:"http://www.wikidata.org/entity/{doc["@id"]}"'
            for doc in rec_results
            for filter_q_search_field in filter_q_search_fields
        ]
        filter_query_add = " OR ".join(filter_query_add)
        filter_query_add = " OR " + filter_query_add
    type_add = ""
    if search_type:
        type_add += f'&fq=@type:"http://www.wikidata.org/entity/{search_type}"'
    q_add = (
        " OR ".join(
            [
                f"&q={q_search_field}:{search_string}"
                for q_search_field in q_search_fields
            ]
        )
        + filter_query_add
    )
    gen_query_str = (
        f"http://solr:8983/solr/test_core/select?{q_add}{type_add}&wt=json&rows=40"
    )
    gen_query_results = requests.get(gen_query_str).json()["response"]
    num_found = gen_query_results["numFound"]
    res_docs = gen_query_results["docs"]
    if num_found > 0:
        res_docs = prepare_results(res_docs)
    else:
        res_docs = []
    return res_docs, num_found


def get_available_fields():
    r = requests.get(
        f"http://solr:8983/solr/test_core/select?q=*:*&rows=0&facet=true&wt=csv"
    ).text.split(",")
    for field in FIELDS_TO_REMOVE:
        r.remove(field)
    filtered_fields = set()
    for field in r:
        if not field.startswith("wd"):
            continue
        filtered_field = field.split("_")[1]
        filtered_fields.add(filtered_field)
    filtered_fields = list(filtered_fields)
    field_labels = get_labels(filtered_fields, include_aliases=True)
    field_label_pairs = []
    for field_id, labels in field_labels.items():
        for label_option in labels:
            field_label_pairs.append((field_id, label_option))
    return field_label_pairs


def get_available_types():
    r = requests.get(
        f"http://solr:8983/solr/test_core/select?q=*:*&rows=0&facet=true&facet.field=@type&wt=json"
    ).json()
    avail_types = r["facet_counts"]["facet_fields"]["@type"][0::2]
    avail_types.remove("ld_item")
    avail_types.remove("ld_prop")
    avail_types = [t for t in avail_types if t.startswith("http://www.wikidata.org/")]
    avail_types = [t.split("/")[-1] for t in avail_types]
    type_labels = get_labels(avail_types)
    return type_labels


def get_related_search_fields(search_field):
    search_field_url = (
        f"http://www.wikidata.org/entity/{search_field}"
        if search_field.startswith("Q")
        else f"http://www.wikidata.org/prop/direct/{search_field}"
    )
    r = requests.get(
        f'http://solr:8983/solr/test_core/select?q=*:*&rows=10&fq=@type:ld_similar_terms AND @id:"{search_field_url}"&wt=json'
    ).json()
    if r["response"]["numFound"] == 0:
        return []
    rel_term_set = set()
    for rel_term_res in r["response"]["docs"]:
        if "_nest_parent_" in rel_term_res:
            rel_term_set.add(rel_term_res["_nest_parent_"].split("/")[-1])
    rel_term_labels = get_labels(rel_term_set)
    return rel_term_labels


@app.route("/")
def lmdl_search():
    avail_fields = get_available_fields()
    avail_types = get_available_types()
    if search_string := request.args.get("search-string"):
        search_field = request.args.getlist("field-value")
        search_type = request.args.get("search-type")
        if len(search_field) == 1 and search_field[0] == "":
            search_field = ""
        results, num_results = query_solr(search_string, search_field, search_type)
        if len(search_field) == 1:
            search_field = search_field[0]
            related_search_fields = get_related_search_fields(search_field)
            if related_search_fields:
                comb_related_search_fields = "&search-value=".join(
                    [
                        f"{field_id}"
                        for field_id, field_label in related_search_fields.items()
                    ]
                )
            else:
                related_search_fields = ""
                comb_related_search_fields = ""
        else:
            related_search_fields = ""
            comb_related_search_fields = ""
        return render_template(
            "search.html",
            results=results,
            num_results=num_results,
            avail_fields=avail_fields,
            avail_types=avail_types,
            related_search_fields=related_search_fields,
            search_string=search_string,
            search_field=search_field,
            search_type=search_type,
            comb_related_search_fields=comb_related_search_fields,
        )
    return render_template(
        "search.html", avail_fields=avail_fields, avail_types=avail_types
    )
