#  MediExplain
### An LLM-Based AI Agent for Automated Explanation of Medical Laboratory Reports

##  Project Overview

MediExplain is a task-oriented AI agent that accepts unstructured text from a medical laboratory report and generates a **patient-friendly, plain-language explanation** of the results. It uses **LLaMA 3.3 70B** (via Groq) as its reasoning brain, a **CSV-based reference database** (50+ lab tests) as memory, and a **regex-based value parser** as its perception toolkit — all served via a **Flask web UI**.

The agent is built on the **ReACT (Reason + Act)** framework and uses an **One-Shot + Chain-of-Thought + Few Knowledge** prompting strategy to minimise hallucinations and maximise explanation quality.

---

##  System Architecture

```
User Query (free text)
       │
       ▼
┌──────────────────┐     ┌──────────────────────┐
│  VALUE PARSER    │────▶│  REFERENCE DB LOOKUP  │
│  (parser.py)     │     │  (reference_db.py)    │
│  regex + aliases │     │  reference_ranges.csv │
└──────────────────┘     └──────────────────────┘
       │                          │
       └────────────┬─────────────┘
                    ▼
         ┌─────────────────────────┐
         │   BRAIN  (LLM)          │
         │   agent.py              │
         │   LLaMA 3.3 70B (Groq) │
         │   One-Shot + CoT        │
         └─────────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  SESSION MEMORY     │
         │  session_history.csv│
         └─────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  FLASK WEB UI       │
         │  app.py + index.html│
         └─────────────────────┘
```

---

##  Project Structure

```
MediExplain/
├── app.py                  # Flask web application (entry point)
├── agent.py                # Core agent — orchestrates all components
├── parser.py               # Value Parser — extracts test names, values, units
├── reference_db.py         # Reference DB Toolkit — looks up normal ranges
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── data/
│   ├── reference_ranges.csv    # 50+ lab tests with normal ranges
│   └── session_history.csv     # Auto-generated session log (memory)
│
├── prompts/
│   ├── system_prompt.txt       # System role + safety constraints
│   └── one_shot_example.txt    # One-shot demonstration for LLM
│
└── templates/
    └── index.html              # Flask HTML/CSS/JS web UI
```

---

##  Setup Instructions

### Prerequisites
- Python 3.10 or higher
- A free Groq API key — get one at **https://console.groq.com** (no credit card needed)

### Step 1 — Clone the repository
```bash
git clone https://github.com/23SE-09-55/MediExplain.git
cd MediExplain
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure your API key
```bash
# Copy the example file
cp .env.example .env

# Open .env and add your Groq key:
# GROQ_API_KEY=gsk_your-actual-key-here
```

### Step 5 — Run the application
```bash
python app.py
```

Then open your browser at: **http://localhost:5000**

---

##  Usage

### Web UI
1. Open **http://localhost:5000**
2. Type or paste your lab values in the text box, e.g.:
   ```
   My Hemoglobin is 10.2 g/dL (normal range 12-16)
   WBC = 12.5, Platelets = 450
   ```
3. Select your biological sex (for sex-specific ranges)
4. Click **Explain My Results**

### Example Inputs

**Single value:**
```
My HbA1c came out to 8.1%. Is that bad?
```

**Multiple values with lab-specific ranges:**
```
CBC report: Hemoglobin = 10.2 g/dL, WBC = 12.5, Platelets = 450
Normal ranges from my lab: Hgb 12-16, WBC 4.5-11, Platelets 150-400
```

**Lipid panel:**
```
Cholesterol = 230 mg/dL, LDL = 155, HDL = 38, Triglycerides = 210
```

---

##  Prompting Strategy

MediExplain uses **One-Shot + Chain-of-Thought + Few Knowledge**:

| Component | Purpose |
|-----------|---------|
| System Prompt | Defines agent role, safety rules, mandatory disclaimer |
| One-Shot Example | Shows the LLM the exact desired output format |
| Chain-of-Thought | Instructs step-by-step: identify → classify → explain → disclaim |
| Few Knowledge | Injects reference ranges into context to reduce hallucination |

---

##  LLM Used

| Property | Value |
|----------|-------|
| Model | LLaMA 3.3 70B Versatile |
| Provider | Groq Cloud |
| API Identifier | `llama-3.3-70b-versatile` |
| Cost | Free (Groq free tier) |
| Avg Response Time | ~2–4 seconds |

---

##  Supported Lab Tests

The reference database (`data/reference_ranges.csv`) covers 50+ tests including:

| Category | Tests |
|----------|-------|
| CBC | Hemoglobin, Hematocrit, WBC, RBC, Platelets, MCV, MCH, MCHC, Neutrophils, Lymphocytes |
| Metabolic | Glucose, HbA1c, Sodium, Potassium, Creatinine, BUN, eGFR |
| Lipid Panel | Total Cholesterol, LDL, HDL, Triglycerides |
| Liver Function | ALT, AST, ALP, Total Bilirubin, Total Protein, Albumin |
| Thyroid | TSH, Free T3, Free T4 |
| Others | Iron, Ferritin, Vitamin D, B12, CRP, INR, Uric Acid, Calcium |

Sex-specific ranges are provided for: Hemoglobin, Hematocrit, RBC, Creatinine, HDL, Iron, Ferritin, ESR, Uric Acid.

---

##  Troubleshooting

| Problem | Solution |
|---------|----------|
| `Groq API key not set` | Make sure `.env` exists and contains `GROQ_API_KEY=gsk_...` |
| `No lab values detected` | Include test name AND value, e.g. `Hemoglobin = 10.2` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in your virtualenv |
| `model_decommissioned` error | Make sure model is `llama-3.3-70b-versatile` in `agent.py` |
| Port 5000 already in use | Change port in `app.py`: `app.run(port=5001)` |

---

##  Medical Disclaimer

> MediExplain is an **educational AI tool** and does **NOT** provide medical diagnoses. All explanations generated by this system must be interpreted by a qualified healthcare professional in the context of the patient's complete medical history. The developers assume no medical liability for the use of this tool.

---

##  References

1. Xu W, et al. MRAgent: LLM-based automated agent for causal knowledge discovery. *Brief Bioinform.* 2025.
2. Inoue Y, et al. DrugAgent: Multi-Agent LLM for Drug-Target Interaction. *arXiv:2408.13378.* 2025.
3. Yao S, et al. ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023.*
4. Singhal K, et al. Large language models encode clinical knowledge. *Nature.* 2023.
5. Xi Z, et al. The Rise and Potential of LLM-Based Agents: A Survey. *arXiv:2309.07864.* 2023.
6. Meta AI. LLaMA 3: Open Foundation and Fine-Tuned Chat Models. 2024.
7. Groq. Groq Cloud Inference Platform. https://console.groq.com. 2024.
