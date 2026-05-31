"""
MediExplain — Demo Script
Runs several example queries in demo mode (no API key needed).
Usage:  python demo.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import run_agent

DEMO_QUERIES = [
    {
        "label": "Example 1 — Low Hemoglobin (Anemia)",
        "query": "My Hemoglobin is 10.2 g/dL. The lab's normal range is 12.0 to 16.0 g/dL.",
        "sex": "female",
    },
    {
        "label": "Example 2 — High LDL Cholesterol",
        "query": "LDL = 165 mg/dL, HDL = 35 mg/dL, Total Cholesterol = 240 mg/dL",
        "sex": "both",
    },
    {
        "label": "Example 3 — Complete CBC Panel",
        "query": (
            "CBC results: Hemoglobin = 10.2 g/dL (ref 12-16), "
            "WBC = 12.5 (ref 4.5-11.0), Platelets = 450 (ref 150-400)"
        ),
        "sex": "female",
    },
    {
        "label": "Example 4 — Elevated HbA1c (Diabetes Screening)",
        "query": "My HbA1c came out to 8.2 percent. Is that bad?",
        "sex": "both",
    },
    {
        "label": "Example 5 — Liver Function (High ALT)",
        "query": "ALT: 85 U/L, AST: 62 U/L. Doctor said normal is up to 40.",
        "sex": "male",
    },
]


def main():
    print("\n" + "═" * 60)
    print("  MediExplain — DEMO MODE  (no API key required)")
    print("  AI-based Medical Lab Report Explanation Agent")
    print("  UET Taxila | AI 23-SE-350")
    print("═" * 60)

    for i, demo in enumerate(DEMO_QUERIES, 1):
        print(f"\n\n{'#'*60}")
        print(f"  DEMO QUERY {i}: {demo['label']}")
        print(f"{'#'*60}")
        print(f"  User input: \"{demo['query']}\"")
        print()

        result = run_agent(
            user_query=demo["query"],
            model="demo",
            sex=demo.get("sex", "both"),
            verbose=True,
        )
        print(result)
        input("\n  [Press Enter for next example...]\n") if i < len(DEMO_QUERIES) else None

    print("\n" + "═" * 60)
    print("  Demo complete! To use with a real LLM:")
    print("    export OPENAI_API_KEY=your_key_here")
    print("    export MEDIEXPLAIN_MODEL=gpt-4-turbo")
    print("    python agent.py")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
