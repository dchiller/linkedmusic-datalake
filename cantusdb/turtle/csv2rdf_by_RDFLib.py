from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
import csv
import validators

# Define the base and prefix URIs
base_uri = "http://www.semanticweb.org/LinkedMusic/ontologies/"
prefix_uri = {
    "wdt": "http://www.wikidata.org/prop/direct/",
    "cantusDB": "https://cantusdatabase.org/",
}

P_INCIPIT = URIRef(f"{prefix_uri['wdt']}P1922")
P_GENRE = URIRef(f"{prefix_uri['wdt']}P136")
P_SRC = URIRef(f"{prefix_uri['cantusDB']}sources")
CHANT_TYPE = URIRef(f"{prefix_uri['wdt']}chant")

def convert_csv_to_turtle(csv_filename):
    with open(csv_filename, 'r', encoding='utf-8') as csv_file:
        g = Graph()
        csv_reader = csv.DictReader(csv_file)

        # Convert each row to Turtle format and add it to the output
        for row in csv_reader:
            # Extract csv line info
            chant_uri = URIRef(row["Absolute_url"])
            incipit = Literal(row["incipit"])
            
            if validators.url(row["genre"]): # Genre can be url or string
                genre = URIRef(row["genre"])
            else:
                genre = Literal(row["genre"])
                
            src_link = URIRef(row["src_link"])
            
            # Add triples
            g.add((chant_uri, RDF.type, CHANT_TYPE))
            g.add((chant_uri, P_INCIPIT, incipit))
            g.add((chant_uri, P_GENRE, genre))
            g.add((chant_uri, P_SRC, src_link))
            
        return g


csv_filename = 'reconciled_cantus_01102024_updated_simplified_samples.csv'

# Convert the CSV data to Turtle format and print the result
turtle_data = convert_csv_to_turtle(csv_filename)
print(turtle_data.serialize(format="turtle", destination="test.ttl"))