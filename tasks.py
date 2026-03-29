# tasks.py — Optimized: 3 tasks instead of 8
# Token math: 3 tasks × ~512 output tokens = ~1500 LLM output tokens
# Input context stays small because tasks are sequential and focused

from crewai import Task
from agents import research_agent, report_agent

# ── TASK 1: Biology + Safety (combined to save one full LLM call) ──────────────
bio_safety_task = Task(
    description=(
        "Research {molecule} for repurposing in {disease}. Do the following:\n"
        "1. Use internal_knowledge_tool with input '{molecule}|{disease}' to find biological paths.\n"
        "2. Use web_search to find: top 2 clinical trials with NCT IDs or study names.\n"
        "3. Use web_search to find: LD50 and top 3 side effects of {molecule}.\n"
        "Report findings in bullet points. Max 120 words total. "
        "You MUST write 'Final Answer:' followed by your summary."
    ),
    expected_output=(
        "Bullet point summary covering: biological path (or 'No path found'), "
        "2 clinical trials, LD50 value, 3 side effects. Max 120 words."
    ),
    agent=research_agent,
)

# ── TASK 2: Market + Patents + EXIM (combined) ────────────────────────────────
market_task = Task(
    description=(
        "Find commercial data for {molecule} in {disease} market. Do the following:\n"
        "1. Use web_search: '{disease} treatment market size CAGR 2024'\n"
        "2. Use web_search: '{molecule} patent expiry generic entry'\n"
        "3. Use web_search: '{molecule} import export volume India'\n"
        "Report only numbers and facts. Max 100 words total. "
        "You MUST write 'Final Answer:' followed by your summary."
    ),
    expected_output=(
        "Bullet points: market size (USD), CAGR %, patent expiry year, "
        "top export/import country. Max 100 words."
    ),
    agent=research_agent,
)

# ── TASK 3: Final Report (synthesis only, no tool calls) ──────────────────────
report_task = Task(
    description=(
        "Using ONLY the context provided by previous tasks, write a professional "
        "AIDRA Research Report in markdown. Structure:\n\n"
        "# AIDRA Report: {molecule} for {disease}\n\n"
        "## 1. Biological Pathway\n"
        "## 2. Clinical Evidence\n"
        "## 3. Safety Profile\n"
        "## 4. Market Analysis\n"
        "## 5. Patent & EXIM Status\n"
        "## 6. Final Verdict: Go / No-Go\n\n"
        "Rules: Each section max 60 words. Verdict must be one of: "
        "'GO ✅', 'NO-GO ❌', or 'CONDITIONAL GO ⚠️' with a one-line reason. "
        "Do NOT call any tools. Do NOT add extra sections. "
        "You MUST write 'Final Answer:' followed by the complete markdown report."
    ),
    expected_output=(
        "Complete markdown AIDRA report with 6 sections and a clear Go/No-Go verdict."
    ),
    agent=report_agent,
    context=[bio_safety_task, market_task],
)
