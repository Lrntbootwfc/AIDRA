# ####################################################### 
# #local instance 

# from neo4j import GraphDatabase
# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Neo4jTool:
#     def __init__(self):
#         # Force the driver to use the URI from .env
#         uri = os.getenv("NEO4J_URI")
#         user = os.getenv("NEO4J_USERNAME")
#         password = os.getenv("NEO4J_PASSWORD")
        
#         self.driver = GraphDatabase.driver(
#             uri, 
#             auth=(user, password),
#             encrypted=False  # Required for most local Neo4j Desktop setups
#         )

#     def close(self):
#         self.driver.close()

#     def search_evidence(self, drug_name, disease_name):
#         query = """
#         MATCH (d:Drug)-[r1]->(p:Protein)-[r2]->(s:Disease)
#         WHERE toLower(d.name) = toLower($drug) 
#         AND toLower(s.name) = toLower($disease)
#         RETURN d.name as drug, p.name as protein, s.name as disease,
#         type(r1) as rel1, type(r2) as rel2
#         LIMIT 1
#     """
#         try:
#             with self.driver.session() as session:
#                 result = session.run(query, drug=drug_name, disease=disease_name)
#                 record = result.single()
#                 if record:
#                     return (f"Path Found: {record['drug']} "
#                         f"-[{record['rel1']}]-> {record['protein']} "
#                         f"-[{record['rel2']}]-> {record['disease']}")
#             return "No direct path found in Knowledge Graph."
#         except Exception as e:
#             return f"Database Connection Error: {str(e)}"






import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jTool:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI") # neo4j+ssc://da546353...
        self.user = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        try:
            # +ssc automatically ignores SSL certificate errors
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            print("✅ AuraDB Bolt Connected via +ssc!")
        except Exception as e:
            print(f"❌ Connection Fail: {e}")
            self.driver = None

    def search_evidence(self, drug_name, disease_name):
        if not self.driver: return None

        # Super Flexible Regex Query: Quotes aur Case ignore karega
        query = """
        MATCH path = (d)-[*1..3]-(s)
        WHERE (toLower(d.name) CONTAINS toLower($drug) OR toLower(d.id) CONTAINS toLower($drug))
          AND (toLower(s.name) CONTAINS toLower($disease) OR toLower(s.id) CONTAINS toLower($disease))
        RETURN nodes(path) as nodes, relationships(path) as rels
        LIMIT 1
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, drug=drug_name, disease=disease_name)
                record = result.single()
                
                if record:
                    nodes = record['nodes']
                    rels = record['rels']
                    path_parts = []
                    for i in range(len(nodes)):
                        name = nodes[i].get('name') or nodes[i].get('id') or "Unknown"
                        path_parts.append(f"({str(name).replace('"', '')})")
                        if i < len(rels):
                            path_parts.append(f"-[{rels[i].type}]->")
                    return " | ".join(path_parts)
                
            return None
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return None

    def close(self):
        if self.driver: self.driver.close()

############################################### 
###Cloud db
# import os
# import base64
# import requests
# from dotenv import load_dotenv

# load_dotenv()


# class Neo4jTool:

#     def __init__(self):
#         self.uri = os.getenv("NEO4J_URI")  # optional now
#         self.user = os.getenv("NEO4J_USERNAME")
#         self.password = os.getenv("NEO4J_PASSWORD")

#         if not self.user or not self.password:
#             raise ValueError("❌ Missing environment variables!")

#         print("✅ Using Neo4j HTTP API (No SSL issues)")

#     def close(self):
#         pass  # nothing to close

#     def search_evidence(self, drug_name, disease_name):
#         url = "https://da546353.databases.neo4j.io/db/neo4j/tx/commit"

#         auth = base64.b64encode(
#             f"{self.user}:{self.password}".encode()
#         ).decode()

#         headers = {
#             "Authorization": f"Basic {auth}",
#             "Content-Type": "application/json"
#         }

#         payload = {
#             "statements": [
#                 {
#                     "statement": """
#                     MATCH path = (d:Drug)-[*1..3]-(s:Disease)
#                     WHERE replace(replace(toLower(d.name), "-", ""), "_", "") 
#                           CONTAINS replace(toLower($drug), "_", "")
#                     AND replace(replace(toLower(s.name), "-", ""), "_", "") 
#                           CONTAINS replace(toLower($disease), "_", "")
#                     RETURN path
#                     LIMIT 1
#                     """,
#                     "parameters": {
#                         "drug": drug_name,
#                         "disease": disease_name
#                     },
#                     "resultDataContents": ["graph"]   # 🔥 critical
#                 }
#             ]
#         }

#         try:
#             res = requests.post(url, json=payload, headers=headers)
#             data = res.json()

#             results = data.get("results", [])

#             if results and results[0]["data"]:
#                 graph = results[0]["data"][0]["graph"]

#                 nodes = graph["nodes"]
#                 rels = graph["relationships"]

#                 # map node id → name
#                 node_map = {
#                     n["id"]: n["properties"].get("name", "Unknown")
#                     for n in nodes
#                 }

#                 path_parts = []

#                 for rel in rels:
#                     start = node_map.get(rel["startNode"], "Unknown")
#                     end = node_map.get(rel["endNode"], "Unknown")
#                     path_parts.append(f"{start} -[{rel['type']}]-> {end}")

#                 return "Path Found: " + " | ".join(path_parts)

#             return "No path found in AuraDB."

#         except Exception as e:
#             return f"HTTP Error: {str(e)}"