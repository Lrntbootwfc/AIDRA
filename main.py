# main.py — Hybrid Architecture
# Phase 1: Data collection via direct Python calls (ZERO LLM tokens)
# Phase 2: Report via single 70b API call (~700 tokens only)
# Total token usage per report: ~700-900 tokens

import os
import re
import time
import warnings
import requests
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

from scripts.dbtool import Neo4jTool
from langchain_community.tools.tavily_search import TavilySearchResults
from scripts.mathutil import calculate_confidence_score


# ── PHASE 1: Direct tool calls — no LLM, zero tokens ─────────────────────────

def fetch_kg_path(molecule: str, disease: str) -> str:
    try:
        db = Neo4jTool()
        result = db.search_evidence(molecule, disease)
        db.close()
        return str(result)[:400] if result else "No path found in knowledge graph."
    except Exception as e:
        return f"DB unavailable: {str(e)[:80]}"


def fetch_web(query: str) -> str:
    try:
        time.sleep(2)
        tavily = TavilySearchResults(
            api_key=os.getenv("TAVILY_API_KEY"),
            search_depth="basic",
            max_results=2
        )
        raw = tavily.run(query)
        if not raw:
            return "No results found."
        output = ""
        for item in raw:
            content = item.get("content", "")[:250]
            output += f"{content}\n"
        return output[:500]
    except Exception as e:
        return f"Search failed: {str(e)[:60]}"


def collect_all_data(molecule: str, disease: str) -> dict:
    print("  [1/5] Querying knowledge graph...")
    kg = fetch_kg_path(molecule, disease)

    print("  [2/5] Fetching clinical trials...")
    trials = fetch_web(f"{molecule} {disease} clinical trials NCT")

    print("  [3/5] Fetching safety data...")
    safety = fetch_web(f"{molecule} LD50 side effects toxicity")

    print("  [4/5] Fetching market data...")
    market = fetch_web(f"{disease} treatment market size CAGR 2024")

    print("  [5/5] Fetching patent data...")
    patent = fetch_web(f"{molecule} patent expiry generic")

    return {
        "kg_path": kg,
        "trials": trials,
        "safety": safety,
        "market": market,
        "patent": patent,
    }


# ── PHASE 2: Single 70b call — structured prompt, clean output ────────────────

def generate_report(molecule: str, disease: str, data: dict) -> str:
    print("\n  [6/6] Generating report with 70b model...")

    prompt = f"""You are a pharmaceutical research analyst. Write a concise AIDRA Research Report.

RESEARCH DATA:
- Biological Path: {data['kg_path']}
- Clinical Trials: {data['trials']}
- Safety Profile: {data['safety']}
- Market Data: {data['market']}
- Patent Status: {data['patent']}

Write EXACTLY in this format (each section max 60 words):

# AIDRA Report: {molecule} for {disease}

## 1. Biological Pathway
[mechanism from KG path]

## 2. Clinical Evidence
[trial names and NCT IDs]

## 3. Safety Profile
[LD50 and top 3 side effects]

## 4. Market Analysis
[market size USD and CAGR %]

## 5. Patent Status
[expiry year and generic status]

## 6. Final Verdict
[Exactly one of: GO ✅ / NO-GO ❌ / CONDITIONAL GO ⚠️ + one sentence reason]"""

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700,
        "temperature": 0.1,
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

        except requests.exceptions.HTTPError:
            if resp.status_code == 429:
                wait = 65
                match = re.search(r"try again in (\d+\.?\d*)s", resp.text)
                if match:
                    wait = int(float(match.group(1))) + 5
                print(f"\n  ⚠️  Rate limit. Waiting {wait}s... (attempt {attempt+1}/3)")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            raise RuntimeError(f"Report generation failed: {e}")

    raise RuntimeError("Failed after 3 retries.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("       AIDRA — Drug Repurposing Intelligence")
    print("=" * 55)

    molecule = input("\nEnter Drug    (e.g., Metformin): ").strip()
    disease  = input("Enter Disease  (e.g., Alzheimers): ").strip()

    if not molecule or not disease:
        print("❌ Drug aur Disease dono required hain.")
        exit(1)

    print(f"\n🚀 Launching AIDRA: [{molecule}] → [{disease}]\n")
    print("ℹ️  Phase 1 — Data collection (zero LLM tokens)")
    print("ℹ️  Phase 2 — Report writing  (~700 tokens, 1 call)\n")
    start = time.time()

    try:
        data = collect_all_data(molecule, disease)
        report_text = generate_report(molecule, disease, data)
        elapsed = round(time.time() - start, 1)

        path_found = any(
            kw in data["kg_path"].lower()
            for kw in ["path found", "modulates", "inhibits",
                       "activates", "associated_with", "target"]
        )
        score = calculate_confidence_score(path_found=path_found, entropy_score=0.4)

        filename = f"AIDRA_{molecule}_{disease}.md".replace(" ", "_")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_text)
            f.write(f"\n\n---\n")
            f.write(f"**Confidence Score:** {score}  \n")
            f.write(f"**KG Path:** {'Validated ✅' if path_found else 'Not Found ❌'}  \n")
            f.write(f"**Time:** {elapsed}s\n")

        print("\n" + "=" * 55)
        print(f"✅ Report saved : {filename}")
        print(f"📊 Confidence   : {score}")
        print(f"🔬 KG Path      : {'Validated ✅' if path_found else 'Not Found ❌'}")
        print(f"⏱  Time         : {elapsed}s")
        print("=" * 55 + "\n")
        print(report_text)

    except Exception as e:
        print(f"\n❌ AIDRA Failed: {e}")
        print("\n🔧 Check:")
        print("  • GROQ_API_KEY in .env")
        print("  • TAVILY_API_KEY in .env")
        print("  • Neo4j running")
        raise

# import os
# import warnings
# import time
# from crewai import Crew, Process
# from dotenv import load_dotenv

# warnings.filterwarnings("ignore")
# load_dotenv()

# from agents import research_agent, report_agent
# from tasks import bio_safety_task, market_task, report_task
# from scripts.mathutil import calculate_confidence_score


# def run_aidra(molecule: str, disease: str) -> str:
#     """
#     Runs the AIDRA pipeline.
#     Token budget: ~20k-30k total (input + output across all 3 tasks).
#     """
#     crew = Crew(
#         agents=[research_agent, report_agent],
#         tasks=[bio_safety_task, market_task, report_task],
#         process=Process.sequential,
#         verbose=True,       # Set False in production to save ~5k tokens
#         max_rpm=3,         # Groq free tier: ~30 RPM; 10 gives safe headroom
#         memory=False,       # No memory = no extra token overhead
#         cache=True,         # Cache tool results so repeat queries don't cost tokens
#         planning=False,
#         share_crew=False,
#     )

#     result = crew.kickoff(inputs={"molecule": molecule, "disease": disease})
#     return str(result)


# if __name__ == "__main__":
#     print("=" * 55)
#     print("       AIDRA — Drug Repurposing Intelligence System")
#     print("=" * 55)

#     molecule = input("\nEnter Drug (e.g., Metformin): ").strip()
#     disease = input("Enter Disease (e.g., Alzheimers): ").strip()

#     if not molecule or not disease:
#         print("❌ Error: Drug and Disease cannot be empty.")
#         exit(1)

#     print(f"\n  Launching AIDRA for [{molecule}] → [{disease}]...\n")
#     start = time.time()

#     try:
#         report_text = run_aidra(molecule, disease)

#         elapsed = round(time.time() - start, 1)

#         # Confidence score
#         path_found = any(
#             kw in report_text.lower()
#             for kw in ["path found", "target", "connection", "modulates", "inhibits", "activates"]
#         )
#         score = calculate_confidence_score(path_found=path_found, entropy_score=0.4)

#         # Save report
#         filename = f"AIDRA_{molecule}_{disease}.md".replace(" ", "_")
#         with open(filename, "w", encoding="utf-8") as f:
#             f.write(f"# AIDRA Report: {molecule} for {disease}\n\n")
#             f.write(report_text)
#             f.write(f"\n\n---\n**Confidence Score:** {score}  \n")
#             f.write(f"**Time Elapsed:** {elapsed}s  \n")
#             f.write(f"**KG Path Status:** {'Validated ✅' if path_found else 'Not Found ❌'}\n")

#         print("\n" + "=" * 55)
#         print(f"✅ Report saved: {filename}")
#         print(f"📊 Confidence Score : {score}")
#         print(f"🔬 KG Path Status   : {'Validated' if path_found else 'Not Found'}")
#         print(f"⏱  Time Elapsed     : {elapsed}s")
#         print("=" * 55)
#         print("\n📄 REPORT PREVIEW:\n")
#         print(report_text[:1500])  # Preview first 1500 chars in terminal
#         if len(report_text) > 1500:
#             print(f"\n... [Full report saved to {filename}]")

#     except Exception as e:
#         print(f"\n❌ AIDRA Failed: {e}")
#         print("\n🔧 Troubleshooting:")
#         print("  1. Check GROQ_API_KEY and TAVILY_API_KEY in .env")
#         print("  2. Check if Neo4j is running (scripts/dbtool.py)")
#         print("  3. If rate limited, wait 60s and retry")
#         raise
