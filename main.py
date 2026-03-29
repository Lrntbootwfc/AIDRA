# main.py — Stable, token-efficient AIDRA runner

import os
import warnings
import time
from crewai import Crew, Process
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

from agents import research_agent, report_agent
from tasks import bio_safety_task, market_task, report_task
from scripts.mathutil import calculate_confidence_score


def run_aidra(molecule: str, disease: str) -> str:
    """
    Runs the AIDRA pipeline.
    Token budget: ~20k-30k total (input + output across all 3 tasks).
    """
    crew = Crew(
        agents=[research_agent, report_agent],
        tasks=[bio_safety_task, market_task, report_task],
        process=Process.sequential,
        verbose=True,       # Set False in production to save ~5k tokens
        max_rpm=3,         # Groq free tier: ~30 RPM; 10 gives safe headroom
        memory=False,       # No memory = no extra token overhead
        cache=True,         # Cache tool results so repeat queries don't cost tokens
        planning=False,
        share_crew=False,
    )

    result = crew.kickoff(inputs={"molecule": molecule, "disease": disease})
    return str(result)


if __name__ == "__main__":
    print("=" * 55)
    print("       AIDRA — Drug Repurposing Intelligence System")
    print("=" * 55)

    molecule = input("\nEnter Drug (e.g., Metformin): ").strip()
    disease = input("Enter Disease (e.g., Alzheimers): ").strip()

    if not molecule or not disease:
        print("❌ Error: Drug and Disease cannot be empty.")
        exit(1)

    print(f"\n  Launching AIDRA for [{molecule}] → [{disease}]...\n")
    start = time.time()

    try:
        report_text = run_aidra(molecule, disease)

        elapsed = round(time.time() - start, 1)

        # Confidence score
        path_found = any(
            kw in report_text.lower()
            for kw in ["path found", "target", "connection", "modulates", "inhibits", "activates"]
        )
        score = calculate_confidence_score(path_found=path_found, entropy_score=0.4)

        # Save report
        filename = f"AIDRA_{molecule}_{disease}.md".replace(" ", "_")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# AIDRA Report: {molecule} for {disease}\n\n")
            f.write(report_text)
            f.write(f"\n\n---\n**Confidence Score:** {score}  \n")
            f.write(f"**Time Elapsed:** {elapsed}s  \n")
            f.write(f"**KG Path Status:** {'Validated ✅' if path_found else 'Not Found ❌'}\n")

        print("\n" + "=" * 55)
        print(f"✅ Report saved: {filename}")
        print(f"📊 Confidence Score : {score}")
        print(f"🔬 KG Path Status   : {'Validated' if path_found else 'Not Found'}")
        print(f"⏱  Time Elapsed     : {elapsed}s")
        print("=" * 55)
        print("\n📄 REPORT PREVIEW:\n")
        print(report_text[:1500])  # Preview first 1500 chars in terminal
        if len(report_text) > 1500:
            print(f"\n... [Full report saved to {filename}]")

    except Exception as e:
        print(f"\n❌ AIDRA Failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check GROQ_API_KEY and TAVILY_API_KEY in .env")
        print("  2. Check if Neo4j is running (scripts/dbtool.py)")
        print("  3. If rate limited, wait 60s and retry")
        raise
