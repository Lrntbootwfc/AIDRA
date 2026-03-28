import os
import requests
from crewai import Agent, LLM
from crewai.tools import BaseTool          # ✅ Use CrewAI's BaseTool
from pydantic import Field
from scripts.dbtool import Neo4jTool
from langchain_community.tools import DuckDuckGoSearchRun

from dotenv import load_dotenv

load_dotenv()
llm = LLM(
    # model="groq/llama-3.1-8b-instant",
    model="groq/llama-3.3-70b-versatile",  # ✅ Provider prefix required
    api_key=os.getenv("GROQ_API_KEY")
)

# --- 1. NEO4J TOOL (CrewAI-compatible) ---
class KnowledgeGraphTool(BaseTool):
    name: str = "knowledge_graph_tool"
    description: str = "Search Neo4j for biological paths between Drug and Disease. Input format: 'drug_name|disease_name' e.g. 'metformin|alzheimers'"

    def _run(self, input_str: str) -> str:
        try:
            from scripts.dbtool import Neo4jTool
            db = Neo4jTool()
            
            # Parse "drug|disease" format
            if "|" in input_str:
                parts = input_str.split("|")
                drug = parts[0].strip()
                disease = parts[1].strip()
            else:
                # fallback: treat whole string as drug, use generic disease
                drug = input_str.strip()
                disease = ""
            
            result = db.search_evidence(drug, disease)  # ✅ correct method
            db.close()
            return result
        except Exception as e:
            return f"Database Error: {str(e)}"

kg_tool_wrapper = KnowledgeGraphTool()


class FreeSearchTool(BaseTool):
    name: str = "internet_search"
    description: str = "Search the internet for real-time drug data, clinical trials, and market info. No API key needed."

    def _run(self, search_query: str) -> str:
        try:
            ddg = DuckDuckGoSearchRun()
            return ddg.run(search_query)
        except Exception as e:
            return f"Search failed, using internal knowledge. Error: {str(e)}"

internet_search = FreeSearchTool()


# --- 4. AGENTS DEFINITION ---

research_lead = Agent(
    role="Chief Research Officer",
    goal="Oversee the entire drug repurposing pipeline for {molecule} in {disease}.",
    backstory="Strategic lead. If no biological path exists, you HALT.",
    llm=llm,
    allow_delegation=True,
    max_iter=5,
    max_retry_limit=2
)

chemical_analyst = Agent(
    role="Lead Bioinformatics Scientist",
    goal="Find molecular targets for {molecule} in {disease}.",
    backstory="Expert in Neo4j. You find Drug -> Protein -> Disease paths.",
    tools=[kg_tool_wrapper],   # ✅ Now a CrewAI BaseTool instance
    llm=llm,
    max_iter=3,        # ✅ stop after 3 attempts
    max_retry_limit=1,
    
)

clinical_specialist = Agent(
    role="Clinical Trials Analyst",
    goal="Search for existing trials of {molecule}.",
    backstory="Master of PubMed. You find clinical evidence.",
    tools=[internet_search],
    llm=llm,
    max_iter=3,
    max_retry_limit=1
)

safety_expert = Agent(
    role="Toxicology Lead",
    goal="Assess toxicity of {molecule}.",
    backstory="You evaluate if the drug is safe for humans.",
    tools=[internet_search],
    llm=llm,
    max_iter=3,
    max_retry_limit=1
)

market_strategist = Agent(
    role="Commercial Viability Lead",
    goal="Analyze market size and competitors.",
    backstory="Business expert in pharmaceuticals.",
    tools=[internet_search],
    llm=llm,
    max_iter=3,
    max_retry_limit=1
)

regulatory_lead = Agent(
    role="FDA Regulatory Consultant",
    goal="Evaluate legal pathways for {molecule}.",
    backstory="Expert in 505(b)(2) regulatory pathways.",
    tools=[internet_search],
    llm=llm,
    max_iter=3,
    max_retry_limit=1
    
)

summarizer = Agent(
    role="Scientific Technical Writer",
    goal="Synthesize all findings into a final AIDRA report.",
    backstory="Final gatekeeper and report writer.",
    llm=llm,
    max_iter=3,
    max_retry_limit=1
)