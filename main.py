import os
from crewai import Agent, Task, Crew, Process
#from langchain_openai import ChatOpenAI
from scripts.dbtool import Neo4jTool
from scripts.mathutil import calculate_confidence_score
from dotenv import load_dotenv

load_dotenv()

# 1. BRAIN SETUP - Groq standard integration
# Hum is object ko direct Agent mein pass karenge
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
os.environ["OPENAI_MODEL_NAME"] = "llama-3.3-70b-versatile"
os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY")

# Create the LLM object explicitly
# my_llm = ChatOpenAI(
#     model_name="llama3-70b-8192",
#     openai_api_base="https://api.groq.com/openai/v1",
#     openai_api_key=os.getenv("GROQ_API_KEY")
# )

kg_tool = Neo4jTool()

# 2. WORKER AGENTS
chemical_agent = Agent(
    role='Chemical Analyst',
    goal='Search Knowledge Graph for drug-disease associations.',
    backstory='You are a bio-informatics expert specialized in Neo4j graph traversal.',
    #llm=my_llm,
    verbose=True,
    allow_delegation=False
)

commercial_agent = Agent(
    role='Commercial Strategist',
    goal='Analyze market demand and EXIM data.',
    backstory='You focus on pharmaceutical trade volumes and patent status.',
    #llm=my_llm,
    verbose=True,
    allow_delegation=False
)

# 3. MASTER AGENT
master_agent = Agent(
    role='Research Lead',
    goal='Synthesize chemical and commercial data into a final X-AAR report.',
    backstory='You coordinate between analysts to provide a final repurposing score.',
    #llm=my_llm,
    verbose=True,
    allow_delegation=True
)

def execute_aidra(molecule, disease):
    task = Task(
        description=f"Analyze if {molecule} can be used for {disease}. Get path evidence from Chemical Agent and market data from Commercial Agent.",
        expected_output="Detailed report with reasoning and evidence.",
        agent=master_agent
    )

    crew = Crew(
        agents=[master_agent, chemical_agent, commercial_agent],
        tasks=[task],
        process=Process.sequential # Faster for debugging
    )
    
    result = crew.kickoff()
    
    # Simple post-process evidence check
    evidence = kg_tool.search_evidence(molecule, disease)
    score = calculate_confidence_score(path_found=("Path Found" in evidence), entropy_score=0.4)
    
    return f"{result}\n\n--- AIDRA SYSTEM METRICS ---\nConfidence Score: {score}\nKG Path: {evidence}"

if __name__ == "__main__":
    m = input("Enter Drug (e.g., Gemcitabine): ")
    d = input("Enter Disease (e.g., Rheumatoid Arthritis): ")
    print(execute_aidra(m, d))