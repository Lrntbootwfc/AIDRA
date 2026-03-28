from crewai import Task
from agents import (
    research_lead, chemical_analyst, clinical_specialist,
    safety_expert, market_strategist, regulatory_lead, summarizer
)

# Task 1: KG Search (Base Evidence)
kg_task = Task(
    description="Use knowledge_graph_tool with EXACT input '{molecule}|{disease}' to find protein paths. "
                "Do NOT explain Neo4j. Do NOT write Cypher. Just call the tool and report the output.",
    expected_output="One line only: 'Path Found: X' or 'No Path Found'. Nothing else.",
    agent=chemical_analyst
)

clinical_task = Task(
    description="Search Google for clinical trials of {molecule} for {disease}. Return 3 bullet points max.",
    expected_output="3 bullet points of clinical evidence.",
    agent=clinical_specialist,
    context=[kg_task]
)

toxicity_task = Task(
    description="Search Google for toxicity profile of {molecule}. Return LD50 and top 3 side effects only.",
    expected_output="LD50 value and 3 side effects.",
    agent=safety_expert
)

market_task = Task(
    description="Search Google for {disease} treatment market size and top competitors.",
    expected_output="Market size figure and 3 competitor names.",
    agent=market_strategist
)

reg_task = Task(
    description="Search Google for FDA regulatory pathway for {molecule} repurposing for {disease}.",
    expected_output="One paragraph on regulatory strategy.",
    agent=regulatory_lead
)

final_task = Task(
    description="Compile all findings into AIDRA Final Report with these exact sections:\n"
                "1) KG Path\n2) Clinical Evidence\n3) Toxicity\n4) Market\n5) Regulatory\n6) Final Verdict: Go/No-Go",
    expected_output="Structured AIDRA report with all 6 sections and a Go/No-Go verdict.",
    agent=summarizer,
    context=[kg_task, clinical_task, toxicity_task, market_task, reg_task]
)