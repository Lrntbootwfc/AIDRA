import os
import logging 
os.environ["LITELLM_LOGGING"] = "False"
logging.getLogger("root").setLevel(logging.CRITICAL)
logging.getLogger("lite-llm").setLevel(logging.CRITICAL) 

import litellm
logging.getLogger("litellm").setLevel(logging.CRITICAL)
litellm.set_verbose = False
litellm.suppress_debug_info = True

from dotenv import load_dotenv
load_dotenv()

from crewai import   Crew, Process
from agents import (
    research_lead, chemical_analyst, clinical_specialist, 
    safety_expert, market_strategist, regulatory_lead, summarizer, llm
)
from tasks import kg_task, clinical_task, toxicity_task, market_task, reg_task, final_task
from scripts.mathutil import calculate_confidence_score 
# from langchain_groq import ChatGroq





# 1. BRAIN SETUP - Groq standard integration
# # Hum is object ko direct Agent mein pass karenge
# os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
# os.environ["OPENAI_MODEL_NAME"] = "llama-3.3-70b-versatile"
# os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY")


# llm = ChatGroq(
#     api_key=os.getenv("GROQ_API_KEY"),
#     model="llama-3.3-70b-versatile"
# )


crew = Crew(
    agents=[research_lead, chemical_analyst, clinical_specialist, 
            safety_expert, market_strategist, regulatory_lead, summarizer],
    tasks=[kg_task, clinical_task, toxicity_task, market_task, reg_task, final_task],
    process=Process.sequential, 
    #manager_llm=llm, 
    verbose=True,
    memory=False,
    cache=True,
    max_rpm=2
)

if __name__ == "__main__":
    molecule = input("Enter Drug (e.g., Metformin): ")
    disease = input("Enter Disease (e.g., Alzheimers): ")
    
    print(f"\n--- AIDRA Launching Parallel Research for {molecule} in {disease} ---\n")
    
    # Kickoff the process
    result = crew.kickoff(inputs={'molecule': molecule, 'disease': disease})
    
    print("\n--- FINAL RESEARCH REPORT ---\n")
    print(result)

    # 6. SYSTEM METRICS (Using mathutil)
    report_text = str(result)
 
    path_found_status = any(word in report_text.lower() for word in ["path found", "biological connection", "molecular target"])
    
    # Final calculation (Entropy standard 0.4)
    final_score = calculate_confidence_score(path_found=path_found_status, entropy_score=0.4)
    
    print("\n--- AIDRA SYSTEM METRICS ---")
    print(f"Validated Confidence Score: {final_score}")
    print(f"Knowledge Graph Status: {'Path Validated' if path_found_status else 'No Direct Path Found'}")

# # 2. WORKER AGENTS
# chemical_agent = Agent(
#     role='Chemical Analyst',
#     goal='Search Knowledge Graph for drug-disease associations.',
#     backstory='You are a bio-informatics expert specialized in Neo4j graph traversal.',
#     #llm=my_llm,
#     verbose=True,
#     allow_delegation=False
# )

# commercial_agent = Agent(
#     role='Commercial Strategist',
#     goal='Analyze market demand and EXIM data.',
#     backstory='You focus on pharmaceutical trade volumes and patent status.',
#     #llm=my_llm,
#     verbose=True,
#     allow_delegation=False
# )

# # 3. MASTER AGENT
# # master_agent = Agent(
# #     role='Research Lead',
# #     goal='Synthesize chemical and commercial data into a final X-AAR report.',
# #     backstory='You coordinate between analysts to provide a final repurposing score.',
# #     #llm=my_llm,
# #     verbose=True,
# #     allow_delegation=True
# # )

# master_agent = Agent(
#     role='Research Lead',
#     goal='Validate biological paths. If no path exists, HALT research immediately.',
#     backstory='''You are a rigorous scientist. Your first priority is the Chemical Analyst's 
#     report. If they report "No Path Found" in the Knowledge Graph, you must NOT 
#     ask the Commercial Strategist for data. Instead, finalize the report as "Infeasible" 
#     and stop the process to save time.''',
#     verbose=True,
#     allow_delegation=True
# )

# def execute_aidra(molecule, disease):
#     task = Task(
#     description=f"Quick Scan: Assess {molecule} for {disease}. 1. Path check. 2. Market check. 3. Stop if toxicity > 0.8.",
#     expected_output="Bullet points of evidence ONLY. No essays. Final Verdict: [Go/No-Go].",
#     agent=master_agent
# )

#     crew = Crew(
#         agents=[master_agent, chemical_agent, commercial_agent],
#         tasks=[task],
#         process=Process.hierarchical, # This makes Master Agent act as a real Boss
#         manager_llm=master_agent.llm,
#         verbose=True,
#         halt_on_error=True
#     )
    
#     result = crew.kickoff()
    
#     # Simple post-process evidence check
#     evidence = kg_tool.search_evidence(molecule, disease)
#     path_exists = "path found" in str(evidence).lower()
#     score = calculate_confidence_score(path_found=path_exists, entropy_score=0.4)
    
#     return f"{result}\n\n--- AIDRA SYSTEM METRICS ---\nConfidence Score: {score}\nKG Path: {evidence}"

# if __name__ == "__main__":
#     m = input("Enter Drug (e.g., Gemcitabine): ")
#     d = input("Enter Disease (e.g., Rheumatoid Arthritis): ")
#     print(execute_aidra(m, d))