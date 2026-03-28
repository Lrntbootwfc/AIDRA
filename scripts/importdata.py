from neo4j import GraphDatabase
import csv, os
from dotenv import load_dotenv
load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def import_drugbank(filepath):
    """Import DrugBank CSV: columns drug_name, protein_name, disease_name"""
    with driver.session() as session:
        with open(filepath) as f:
            for row in csv.DictReader(f):
                session.run("""
                    MERGE (d:Drug {name: toLower($drug)})
                    MERGE (p:Protein {name: $protein})
                    MERGE (s:Disease {name: toLower($disease)})
                    MERGE (d)-[:TARGETS]->(p)
                    MERGE (p)-[:ASSOCIATED_WITH]->(s)
                """, drug=row['drug_name'], protein=row['protein_name'], disease=row['disease_name'])
    print("DrugBank import done.")

import_drugbank("data/drugbank.csv")
driver.close()
