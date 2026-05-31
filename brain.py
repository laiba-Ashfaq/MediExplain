"""
MediExplain — Brain Module
Handles LLM API calls for GPT-4, Gemini, Claude, and Llama.
Falls back to a rule-based explainer if no API key is available (demo mode).
"""

import os
import json
from typing import Optional
from prompts.templates import build_prompt, DISCLAIMER


# ── API caller ────────────────────────────────────────────────────────────────

def call_llm(test_blocks: list[dict], model: str = "gpt-4-turbo") -> str:
    """
    Send test data to the selected LLM and return its explanation.

    Supported models:
        "gpt-4-turbo"       → OpenAI API  (needs OPENAI_API_KEY)
        "gemini-1.5-pro"    → Google API  (needs GOOGLE_API_KEY)
        "claude-3-opus"     → Anthropic   (needs ANTHROPIC_API_KEY)
        "llama-3-70b"       → Together AI (needs TOGETHER_API_KEY)
        "demo"              → Rule-based fallback, no API key needed
    """
    messages = build_prompt(test_blocks)

    if model == "gpt-4-turbo":
        return _call_openai(messages, model_id="gpt-4-turbo")
    elif model == "gemini-1.5-pro":
        return _call_gemini(messages)
    elif model == "claude-3-opus":
        return _call_claude(messages)
    elif model == "llama-3-70b":
        return _call_together(messages)
    else:
        return _demo_explainer(test_blocks)


def _call_openai(messages: list[dict], model_id: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except ImportError:
        return "[ERROR] openai package not installed. Run: pip install openai"
    except KeyError:
        return "[ERROR] OPENAI_API_KEY not set. See README for setup instructions."
    except Exception as e:
        return f"[ERROR] OpenAI API call failed: {e}"


def _call_gemini(messages: list[dict]) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-pro")
        # Merge system + user messages for Gemini
        full_prompt = messages[0]["content"] + "\n\n" + messages[1]["content"]
        response = model.generate_content(full_prompt)
        return response.text
    except ImportError:
        return "[ERROR] google-generativeai package not installed. Run: pip install google-generativeai"
    except KeyError:
        return "[ERROR] GOOGLE_API_KEY not set. See README for setup instructions."
    except Exception as e:
        return f"[ERROR] Gemini API call failed: {e}"


def _call_claude(messages: list[dict]) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            system=messages[0]["content"],
            messages=[{"role": "user", "content": messages[1]["content"]}],
        )
        return response.content[0].text
    except ImportError:
        return "[ERROR] anthropic package not installed. Run: pip install anthropic"
    except KeyError:
        return "[ERROR] ANTHROPIC_API_KEY not set. See README for setup instructions."
    except Exception as e:
        return f"[ERROR] Anthropic API call failed: {e}"


def _call_together(messages: list[dict]) -> str:
    try:
        from together import Together
        client = Together(api_key=os.environ["TOGETHER_API_KEY"])
        response = client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except ImportError:
        return "[ERROR] together package not installed. Run: pip install together"
    except KeyError:
        return "[ERROR] TOGETHER_API_KEY not set. See README for setup instructions."
    except Exception as e:
        return f"[ERROR] Together AI call failed: {e}"


# ── Rule-based demo explainer (no API needed) ─────────────────────────────────

_EXPLANATIONS = {
    "LOW": {
        "Hemoglobin": ("carries oxygen in red blood cells", "anemia — your blood carries less oxygen than normal",
                       ["Iron deficiency (most common cause)", "Vitamin B12 or folate deficiency",
                        "Chronic blood loss (e.g., heavy periods, GI bleeding)", "Chronic illness affecting red blood cell production"]),
        "White Blood Cell Count": ("fights infections", "leukopenia — your immune defense is reduced",
                                   ["Viral infection suppressing bone marrow", "Certain medications (chemotherapy, antibiotics)",
                                    "Autoimmune conditions", "Bone marrow disorders"]),
        "Platelet Count": ("helps blood to clot", "thrombocytopenia — increased risk of bruising or bleeding",
                           ["Viral infections", "Certain medications", "Immune thrombocytopenia (ITP)", "Liver disease"]),
        "HDL Cholesterol": ("the 'good' protective cholesterol", "low HDL increases cardiovascular risk",
                            ["Sedentary lifestyle", "Smoking", "Obesity", "High refined carbohydrate diet"]),
        "DEFAULT": ("performs an important function in your body", "below the normal range — your doctor should review this",
                    ["Various nutritional, physiological, or medical causes", "Please discuss with your healthcare provider"])
    },
    "HIGH": {
        "White Blood Cell Count": ("fights infections", "leukocytosis — your body may be fighting an infection or inflammation",
                                   ["Bacterial infection", "Inflammation or physical stress", "Allergic reaction", "Steroid medications"]),
        "Platelet Count": ("helps blood to clot", "thrombocytosis — mildly elevated; usually temporary",
                           ["Infection or inflammation", "Iron deficiency anemia", "Surgical stress or recent surgery", "Inflammatory bowel disease"]),
        "LDL Cholesterol": ("the 'bad' cholesterol that can clog arteries", "high LDL increases cardiovascular disease risk",
                            ["High saturated fat diet", "Genetic predisposition (familial hypercholesterolemia)", "Sedentary lifestyle", "Hypothyroidism"]),
        "Total Cholesterol": ("all cholesterol in the blood", "elevated total cholesterol requires dietary and lifestyle review",
                              ["High fat diet", "Obesity", "Genetic factors", "Thyroid disorders"]),
        "Triglycerides": ("blood fats stored for energy", "hypertriglyceridemia — high blood fats increase heart and pancreas risk",
                          ["High sugar and refined carbohydrate diet", "Alcohol consumption", "Obesity", "Uncontrolled diabetes"]),
        "HbA1c": ("your 3-month average blood sugar level", "elevated HbA1c suggests poor blood sugar control over the past 3 months",
                  ["Uncontrolled or undiagnosed diabetes", "Pre-diabetes", "High carbohydrate diet", "Insufficient physical activity"]),
        "Glucose (Fasting)": ("sugar in your blood measured after fasting", "elevated fasting glucose may indicate pre-diabetes or diabetes",
                              ["Insufficient insulin production or response", "Pre-diabetic state", "High carbohydrate diet", "Stress or illness"]),
        "Alanine Aminotransferase": ("a liver enzyme that leaks into blood when liver cells are damaged", "elevated ALT suggests liver stress or inflammation",
                                     ["Fatty liver disease", "Recent alcohol consumption", "Certain medications", "Viral hepatitis"]),
        "Aspartate Aminotransferase": ("a liver and heart enzyme", "elevated AST may indicate liver or muscle damage",
                                       ["Liver inflammation", "Muscle injury or strenuous exercise", "Heart conditions", "Certain medications"]),
        "Creatinine": ("a waste product filtered by your kidneys", "elevated creatinine suggests the kidneys may not be filtering as efficiently",
                       ["Dehydration (most common reversible cause)", "Kidney stress or early kidney disease", "High protein diet", "Certain medications"]),
        "TSH": ("controls how active your thyroid gland is", "high TSH means your thyroid is underactive (hypothyroidism)",
                ["Autoimmune thyroid disease (Hashimoto's)", "Iodine deficiency", "Thyroid medications needing dose adjustment", "Post-thyroid surgery"]),
        "DEFAULT": ("performs an important function in your body", "above the normal range — your doctor should review this",
                    ["Various nutritional, physiological, or medical causes", "Please discuss with your healthcare provider"])
    },
    "NORMAL": {
        "DEFAULT": ("", "within the normal reference range — this is a healthy result", [])
    }
}


def _get_explanation(test_name: str, status: str) -> tuple:
    cat = _EXPLANATIONS.get(status, _EXPLANATIONS["NORMAL"])
    return cat.get(test_name, cat["DEFAULT"])


def _demo_explainer(test_blocks: list[dict]) -> str:
    """Generate explanations without any API key (demo / offline mode)."""
    output_lines = [
        "=" * 55,
        "  MediExplain Report  [DEMO MODE — no LLM API key used]",
        "=" * 55,
    ]

    for t in test_blocks:
        status = t["status"]
        name = t["test_name"]
        value = t["value"]
        unit = t["unit"]
        ref_low = t.get("ref_low")
        ref_high = t.get("ref_high")

        ref_str = f"{ref_low} – {ref_high} {unit}" if ref_low is not None else "N/A"

        function_desc, meaning, reasons = _get_explanation(name, status)

        emoji = {"NORMAL": "🟢", "LOW": "🔴", "HIGH": "🟡",
                 "CRITICAL LOW": "🚨", "CRITICAL HIGH": "🚨"}.get(status, "⚪")

        lines = [
            "",
            "━" * 55,
            f"🔬 TEST: {name}",
            f"📊 YOUR VALUE: {value} {unit}",
            f"📏 NORMAL RANGE: {ref_str}",
            f"{emoji} STATUS: {status}",
            "━" * 55,
        ]

        if status == "NORMAL":
            lines += [
                "",
                "WHAT THIS MEANS:",
                f"Your {name} result is within the normal reference range.",
                "This is a healthy result. No action is needed for this test.",
            ]
        else:
            direction = "below" if "LOW" in status else "above"
            lines += [
                "",
                "WHAT THIS MEANS:",
                f"{name} {function_desc}." if function_desc else "",
                f"Your result is {direction} the normal range. This is called {meaning}.",
                "",
                "POSSIBLE REASONS (this is NOT a diagnosis):",
            ]
            for reason in reasons:
                lines.append(f"  • {reason}")
            lines += [
                "",
                "RECOMMENDATION:",
                "Please share this result with your doctor or healthcare provider.",
                "They can run additional tests to identify the exact cause and recommend appropriate next steps.",
            ]

        output_lines.extend(lines)

    output_lines.append(DISCLAIMER)
    return "\n".join(output_lines)
