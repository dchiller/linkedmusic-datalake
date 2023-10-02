from flask import Flask, render_template
import requests

app = Flask(__name__)

@app.route("/")
def lmdl_search():
    return render_template("search.html")