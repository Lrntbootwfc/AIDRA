from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jTool:
    def __init__(self):
        # Force the driver to use the URI from .env
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            encrypted=False  # Required for most local Neo4j Desktop setups
        )

    def close(self):
        self.driver.close()

    def search_evidence(self, drug_name, disease_name):
        # We use TOLOWER to make the search case-insensitive
        query = (
            "MATCH (d:Drug)-[:TARGETS]->(p:Protein)-[:ASSOCIATED_WITH]->(s:Disease) "
            "WHERE toLower(d.name) = toLower($drug) AND toLower(s.name) = toLower($disease) "
            "RETURN d.name as drug, p.name as protein, s.name as disease LIMIT 1"
        )
        try:
            with self.driver.session() as session:
                result = session.run(query, drug=drug_name, disease=disease_name)
                record = result.single()
                if record:
                    # Return a string that matches your main.py check "Path Found"
                    return f"Path Found: Evidence exists through Protein {record['protein']}"
                return "No direct path found in Knowledge Graph."
        except Exception as e:
            return f"Database Connection Error: {str(e)}"