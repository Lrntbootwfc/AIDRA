from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def test_conn():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    
    print(f"Attempting to connect to: {uri} as {user}...")
    try:
        # Use encrypted=False for local desktop
        driver = GraphDatabase.driver(uri, auth=(user, pwd), encrypted=False)
        with driver.session() as session:
            result = session.run("RETURN 'Connection Successful!' as msg")
            print(result.single()["msg"])
        driver.close()
    except Exception as e:
        print(f"\nSTILL FAILING: {e}")

if __name__ == "__main__":
    test_conn()