from flask import Flask, render_template, request
import requests
from pyld import jsonld

app = Flask(__name__)


def prepare_link(doc):
    expanded_doc = jsonld.expand(doc)
    return expanded_doc[0]["@id"]


def query_solr(search_string, search_field):
    r = requests.get(
        f"http://solr:8983/solr/test_core/select?q=*:*&fq={search_field}:{search_string}&rows=30"
    ).json()
    result_ids = [prepare_link(query_result) for query_result in r["response"]["docs"]]
    num_results = r["response"]["numFound"]
    return result_ids, num_results


def get_available_fields():
    r = requests.get(
        f"http://solr:8983/solr/test_core/select?q=*:*&rows=0&facet&wt=csv"
    ).text.split(",")
    r.remove("@id")
    r.remove("@type")
    r.remove("@context")
    r.remove("_version_")
    r.remove("_root_")
    r.remove("_nest_parent_")
    r = [{"field": r_item, "display": " ".join(r_item.split("_")[:-1])} for r_item in r]
    return r


@app.route("/")
def lmdl_search():
    fields = get_available_fields()
    if search_string := request.args.get("search-string"):
        search_field = request.args.get("search-field")
        results, num_results = query_solr(search_string, search_field)
        return render_template(
            "search.html", results=results, num_results=num_results, fields=fields
        )
    return render_template("search.html", fields=fields)
