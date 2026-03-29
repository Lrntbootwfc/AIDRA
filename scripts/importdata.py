from neo4j import GraphDatabase
import csv, os, json, requests
from dotenv import load_dotenv
load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

# ============================================
# 1. DRUGBANK — Drug + Protein targets
# ============================================
def import_drugbank(filepath):
    """
    DrugBank CSV format:
    Drug Name, Target Name, Disease, Action (inhibitor/activator)
    """
    with driver.session() as session:
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                session.run("""
                    MERGE (d:Drug {name: toLower($drug)})
                    MERGE (p:Protein {name: $protein})
                    MERGE (d)-[:TARGETS {action: $action}]->(p)
                """, 
                drug=row['Drug Name'],
                protein=row['Target Name'],
                action=row.get('Action', 'unknown'))
    print("✅ DrugBank imported")

# ============================================
# 2. DISGENET — Protein + Disease links
# ============================================
def import_disgenet(filepath):
    """
    DisGeNET TSV format:
    geneName, diseaseName, score
    Download from: disgenet.org/downloads
    """
    with driver.session() as session:
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                score = float(row.get('score', 0))
                if score > 0.3:  # sirf high confidence wale
                    session.run("""
                        MERGE (p:Protein {name: $protein})
                        MERGE (s:Disease {name: toLower($disease)})
                        MERGE (p)-[:ASSOCIATED_WITH {score: $score}]->(s)
                    """,
                    protein=row['geneName'],
                    disease=row['diseaseName'],
                    score=score)
    print("✅ DisGeNET imported")

# ============================================
# 3. MANUAL SEED DATA — Common drugs (instant)
# ============================================
def import_seed_data():
    """Turant kaam karne ke liye — no download needed"""
    data = [
        # (drug, protein, relationship, disease)
        ("metformin", "AMPK", "ACTIVATES", "alzheimers"),
        ("metformin", "AMPK", "ACTIVATES", "diabetes"),
        ("metformin", "mTOR", "INHIBITS", "cancer"),
        ("metformin", "Abeta_42", "MODULATES", "alzheimers"),
        ("aspirin", "COX1", "INHIBITS", "inflammation"),
        ("aspirin", "COX2", "INHIBITS", "cancer"),
        ("aspirin", "TNF-alpha", "REDUCES", "arthritis"),
        ("ibuprofen", "COX2", "INHIBITS", "inflammation"),
        ("ibuprofen", "COX2", "INHIBITS", "pain"),
        ("donepezil", "AChE", "INHIBITS", "alzheimers"),
        ("donepezil", "BuChE", "INHIBITS", "alzheimers"),
        ("rivastigmine", "AChE", "INHIBITS", "alzheimers"),
        ("memantine", "NMDA", "BLOCKS", "alzheimers"),
        ("atorvastatin", "HMG-CoA", "INHIBITS", "cardiovascular"),
        ("atorvastatin", "PCSK9", "REDUCES", "cardiovascular"),
        ("imatinib", "BCR-ABL", "INHIBITS", "leukemia"),
        ("imatinib", "c-KIT", "INHIBITS", "cancer"),
        ("tamoxifen", "ER-alpha", "BLOCKS", "breast cancer"),
        ("tamoxifen", "BRCA1", "MODULATES", "breast cancer"),
        ("rapamycin", "mTOR", "INHIBITS", "cancer"),
        ("rapamycin", "mTOR", "INHIBITS", "aging"),
        ("sildenafil", "PDE5", "INHIBITS", "hypertension"),
        ("sildenafil", "PDE5", "INHIBITS", "erectile dysfunction"),
        ("dexamethasone", "GR", "ACTIVATES", "inflammation"),
        ("dexamethasone", "NF-kB", "INHIBITS", "covid-19"),
        ("remdesivir", "RdRp", "INHIBITS", "covid-19"),
        ("hydroxychloroquine", "TLR7", "BLOCKS", "lupus"),
        ("hydroxychloroquine", "TLR9", "BLOCKS", "malaria"),
        ("semaglutide", "GLP-1R", "ACTIVATES", "diabetes"),
        ("semaglutide", "GLP-1R", "ACTIVATES", "obesity"),
    ]
    
    with driver.session() as session:
        # Pehle sab clear karo (fresh start)
        session.run("MATCH (n) DETACH DELETE n")
        
        for drug, protein, rel, disease in data:
            session.run(f"""
                MERGE (d:Drug {{name: $drug}})
                MERGE (p:Protein {{name: $protein}})
                MERGE (s:Disease {{name: $disease}})
                MERGE (d)-[:{rel}]->(p)
                MERGE (p)-[:ASSOCIATED_WITH]->(s)
            """, drug=drug, protein=protein, disease=disease)
    
    print(f"✅ Seed data imported: {len(data)} drug-protein-disease paths")

# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    print("Choose import type:")
    print("1. Seed data (instant, no download)")
    print("2. DrugBank CSV")
    print("3. DisGeNET TSV")
    
    choice = input("Enter choice (1/2/3): ")
    
    if choice == "1":
        import_seed_data()
    elif choice == "2":
        path = input("DrugBank CSV path: ")
        import_drugbank(path)
    elif choice == "3":
        path = input("DisGeNET TSV path: ")
        import_disgenet(path)
    
    driver.close()
    print("\n✅ Import complete! Run in Neo4j Browser: MATCH (n) RETURN n")