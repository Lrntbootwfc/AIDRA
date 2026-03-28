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
        query = """
        MATCH (d:Drug)-[r1]->(p:Protein)-[r2]->(s:Disease)
        WHERE toLower(d.name) = toLower($drug) 
        AND toLower(s.name) = toLower($disease)
        RETURN d.name as drug, p.name as protein, s.name as disease,
        type(r1) as rel1, type(r2) as rel2
        LIMIT 1
    """
        try:
            with self.driver.session() as session:
                result = session.run(query, drug=drug_name, disease=disease_name)
                record = result.single()
                if record:
                    return (f"Path Found: {record['drug']} "
                        f"-[{record['rel1']}]-> {record['protein']} "
                        f"-[{record['rel2']}]-> {record['disease']}")
            return "No direct path found in Knowledge Graph."
        except Exception as e:
            return f"Database Connection Error: {str(e)}"