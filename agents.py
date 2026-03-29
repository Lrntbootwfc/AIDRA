import os
from crewai import Agent, LLM
from crewai.tools import BaseTool
from scripts.dbtool import Neo4jTool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

# ✅ LLM: stop[] REMOVED — ye hi empty response ka main culprit tha
llm = LLM(
    model="groq/llama-3.1-8b-instant",
#    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,   # Low = deterministic, less hallucination
    max_tokens=300,     
    timeout=90,
)


class KGSearchTool(BaseTool):
    name: str = "internal_knowledge_tool"
    description: str = (
        "Query Neo4j knowledge graph for biological paths. "
        "Input format: 'molecule|disease' e.g. 'Metformin|Alzheimers'"
    )

    def _run(self, input_str: str) -> str:
        try:
            db = Neo4jTool()
            parts = input_str.split("|") if "|" in input_str else [input_str, ""]
            result = db.search_evidence(parts[0].strip(), parts[1].strip())
            db.close()
            # Cap output to save tokens
            return str(result)[:600] if result else "No direct path found in knowledge graph."
        except Exception as e:
            return f"DB unavailable: {str(e)[:100]}"


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search web for pharmaceutical data. "
        "Input: plain keyword string, max 5 words. Example: 'Metformin Alzheimers clinical trials 2024'"
    )

    def _run(self, query: str) -> str:
        try:
            # Input sanitization
            if isinstance(query, dict):
                query = " ".join(str(v) for v in query.values())
            # Remove special chars that break JSON parsing
            query = str(query).translate(str.maketrans("", "", '"{}[]\\'))
            query = " ".join(query.split()[:6])  # Max 6 words

            tavily = TavilySearchResults(
                api_key=os.getenv("TAVILY_API_KEY"),
                search_depth="basic",   # 'basic' = fewer tokens than 'advanced'
                max_results=2           # Only 2 results to save tokens
            )
            raw = tavily.run(query)

            if not raw:
                return "No web results. Use internal knowledge."

            # Extract and cap content
            output = ""
            for item in raw:
                content = item.get("content", "")[:400]
                url = item.get("url", "")
                output += f"Source: {url}\n{content}\n\n"

            return output[:900]  # Hard cap on total web output

        except Exception as e:
            return f"Web search failed. Use internal knowledge. Error: {str(e)[:80]}"


# Tool instances
kg_tool = KGSearchTool()
web_tool = WebSearchTool()

# ─────────────────────────────────────────────
# AGENTS — Only 2, each handling multiple tasks
# This is the biggest token-saver vs 4-8 agents
# ─────────────────────────────────────────────

research_agent = Agent(
    role="Drug Repurposing Researcher",
    goal=(
        "For {molecule} in {disease}: find biological paths, clinical trial evidence, "
        "patents, safety profile, and EXIM/market data. Be factual and concise."
    ),
    backstory=(
        "Senior pharmaceutical scientist with expertise in drug repurposing. "
        "You report only verified facts in bullet points. No fluff."
    ),
    tools=[kg_tool, web_tool],
    llm=llm,
    max_iter=4,
    max_retry_limit=1,  # 1 retry only — prevents token waste on repeated failures
    verbose=False,      # CRITICAL: verbose=False saves ~30% tokens
    allow_delegation=False,
    cache=False,
)

report_agent = Agent(
    role="Scientific Report Writer",
    goal="Compile all research into a structured 6-section markdown report with Go/No-Go verdict.",
    backstory=(
        "Technical writer who synthesizes pharmaceutical research into clear, "
        "data-rich reports. Every section must have at least one concrete data point."
    ),
    tools=[],           # No tools — only synthesis, saves tokens
    llm=llm,
    max_iter=2,
    max_retry_limit=1,
    verbose=False,
    allow_delegation=False,
    cache=False,
)
