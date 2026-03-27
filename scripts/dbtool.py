from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jTool:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )

    def close(self):
        self.driver.close()

    def search_evidence(self, drug_name, disease_name):
        """Cypher query to find a path between drug and disease."""
        query = (
            "MATCH (d:Drug {name: $drug})-[:TARGETS]->(p:Protein)-[:ASSOCIATED_WITH]->(s:Disease {name: $disease}) "
            "RETURN d.name, p.name, s.name LIMIT 1"
        )
        with self.driver.session() as session:
            result = session.run(query, drug=drug_name, disease=disease_name)
            record = result.single()
            if record:
                return f"Evidence Found: Path exists through {record['p.name']}"
            return "No direct path found in Knowledge Graph."