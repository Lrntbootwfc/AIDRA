import os
import time
from crewai import Agent, LLM
from crewai.tools import BaseTool
from scripts.dbtool import Neo4jTool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

# ── LLM 1: 8b-instant — Tool calls ke liye ───────────────────────────────────
# Free tier: 6000 TPM
# max_tokens=300 → ek tool call + short summary = ~500-600 tokens per call
# 6 tool calls × 600 = ~3600 tokens total → safely under 6000 TPM
llm_fast = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0,
    max_tokens=300,
    timeout=60,
)

# ── LLM 2: 70b-versatile — Final report ke liye ──────────────────────────────
# Sirf EK baar call hoga — ~600 tokens only
# Daily limit 100k mein se sirf 600 jaenge
llm_smart = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
    max_tokens=600,
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
            return str(result)[:500] if result else "No path found in knowledge graph."
        except Exception as e:
            return f"DB unavailable: {str(e)[:80]}"


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search web for pharmaceutical data. "
        "Input: plain keywords, max 5 words."
    )

    def _run(self, query: str) -> str:
        try:
            if isinstance(query, dict):
                query = " ".join(str(v) for v in query.values())
            query = str(query).translate(str.maketrans("", "", '"{}[]\\'))
            query = " ".join(query.split()[:6])

            # 3 second pause — 8b TPM bucket ko recover karne deta hai
            time.sleep(3)

            tavily = TavilySearchResults(
                api_key=os.getenv("TAVILY_API_KEY"),
                search_depth="basic",
                max_results=2
            )
            raw = tavily.run(query)
            if not raw:
                return "No results. Use internal knowledge."

            output = ""
            for item in raw:
                content = item.get("content", "")[:300]
                url = item.get("url", "")
                output += f"Source: {url}\n{content}\n\n"
            return output[:700]

        except Exception as e:
            return f"Search failed. Use internal knowledge. Error: {str(e)[:60]}"


kg_tool = KGSearchTool()
web_tool = WebSearchTool()

# ── AGENT 1: llm_fast (8b) — data fetching only ───────────────────────────────
research_agent = Agent(
    role="Drug Repurposing Researcher",
    goal=(
        "For {molecule} in {disease}: fetch biological paths, "
        "clinical trial IDs, LD50, side effects, market size, patents, EXIM data. "
        "Return only facts and numbers in bullet points."
    ),
    backstory=(
        "Data collection specialist. Call tools, report raw findings "
        "as bullet points. No analysis, no fluff."
    ),
    tools=[kg_tool, web_tool],
    llm=llm_fast,
    max_iter=6,
    max_retry_limit=1,
    verbose=False,
    allow_delegation=False,
    cache=False,
)

# ── AGENT 2: llm_smart (70b) — report writing only ────────────────────────────
report_agent = Agent(
    role="Scientific Report Writer",
    goal="Compile all research into a structured 6-section markdown AIDRA report.",
    backstory=(
        "Expert pharmaceutical writer. Synthesize bullet point data "
        "into a professional report. Every section needs one concrete data point."
    ),
    tools=[],
    llm=llm_smart,
    max_iter=1,
    max_retry_limit=1,
    verbose=False,
    allow_delegation=False,
    cache=False,
)


# import os
# from crewai import Agent, LLM
# from crewai.tools import BaseTool
# from scripts.dbtool import Neo4jTool
# from langchain_community.tools.tavily_search import TavilySearchResults
# from dotenv import load_dotenv

# load_dotenv()

# # ✅ LLM: stop[] REMOVED — ye hi empty response ka main culprit tha
# llm = LLM(
#     model="groq/llama-3.1-8b-instant",
# #    model="groq/llama-3.3-70b-versatile",
#     api_key=os.getenv("GROQ_API_KEY"),
#     temperature=0.1,   # Low = deterministic, less hallucination
#     max_tokens=300,     
#     timeout=90,
# )


# class KGSearchTool(BaseTool):
#     name: str = "internal_knowledge_tool"
#     description: str = (
#         "Query Neo4j knowledge graph for biological paths. "
#         "Input format: 'molecule|disease' e.g. 'Metformin|Alzheimers'"
#     )

#     def _run(self, input_str: str) -> str:
#         try:
#             db = Neo4jTool()
#             parts = input_str.split("|") if "|" in input_str else [input_str, ""]
#             result = db.search_evidence(parts[0].strip(), parts[1].strip())
#             db.close()
#             # Cap output to save tokens
#             return str(result)[:600] if result else "No direct path found in knowledge graph."
#         except Exception as e:
#             return f"DB unavailable: {str(e)[:100]}"


# class WebSearchTool(BaseTool):
#     name: str = "web_search"
#     description: str = (
#         "Search web for pharmaceutical data. "
#         "Input: plain keyword string, max 5 words. Example: 'Metformin Alzheimers clinical trials 2024'"
#     )

#     def _run(self, query: str) -> str:
#         try:
#             # Input sanitization
#             if isinstance(query, dict):
#                 query = " ".join(str(v) for v in query.values())
#             # Remove special chars that break JSON parsing
#             query = str(query).translate(str.maketrans("", "", '"{}[]\\'))
#             query = " ".join(query.split()[:6])  # Max 6 words

#             tavily = TavilySearchResults(
#                 api_key=os.getenv("TAVILY_API_KEY"),
#                 search_depth="basic",   # 'basic' = fewer tokens than 'advanced'
#                 max_results=2           # Only 2 results to save tokens
#             )
#             raw = tavily.run(query)

#             if not raw:
#                 return "No web results. Use internal knowledge."

#             # Extract and cap content
#             output = ""
#             for item in raw:
#                 content = item.get("content", "")[:400]
#                 url = item.get("url", "")
#                 output += f"Source: {url}\n{content}\n\n"

#             return output[:900]  # Hard cap on total web output

#         except Exception as e:
#             return f"Web search failed. Use internal knowledge. Error: {str(e)[:80]}"


# # Tool instances
# kg_tool = KGSearchTool()
# web_tool = WebSearchTool()

# # ─────────────────────────────────────────────
# # AGENTS — Only 2, each handling multiple tasks
# # This is the biggest token-saver vs 4-8 agents
# # ─────────────────────────────────────────────

# research_agent = Agent(
#     role="Drug Repurposing Researcher",
#     goal=(
#         "For {molecule} in {disease}: find biological paths, clinical trial evidence, "
#         "patents, safety profile, and EXIM/market data. Be factual and concise."
#     ),
#     backstory=(
#         "Senior pharmaceutical scientist with expertise in drug repurposing. "
#         "You report only verified facts in bullet points. No fluff."
#     ),
#     tools=[kg_tool, web_tool],
#     llm=llm,
#     max_iter=4,
#     max_retry_limit=1,  # 1 retry only — prevents token waste on repeated failures
#     verbose=False,      # CRITICAL: verbose=False saves ~30% tokens
#     allow_delegation=False,
#     cache=False,
# )

# report_agent = Agent(
#     role="Scientific Report Writer",
#     goal="Compile all research into a structured 6-section markdown report with Go/No-Go verdict.",
#     backstory=(
#         "Technical writer who synthesizes pharmaceutical research into clear, "
#         "data-rich reports. Every section must have at least one concrete data point."
#     ),
#     tools=[],           # No tools — only synthesis, saves tokens
#     llm=llm,
#     max_iter=2,
#     max_retry_limit=1,
#     verbose=False,
#     allow_delegation=False,
#     cache=False,
# )
