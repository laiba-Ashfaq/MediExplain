"""
MediExplain — Value Parser
Extracts lab test names, values, units, and reference ranges from free text.
"""
import re

ALIAS_MAP = {
    "hgb": "Hemoglobin", "hb": "Hemoglobin", "haemoglobin": "Hemoglobin",
    "hct": "Hematocrit", "pcv": "Hematocrit",
    "wbc": "White Blood Cell Count", "tlc": "White Blood Cell Count",
    "rbc": "Red Blood Cell Count", "erythrocytes": "Red Blood Cell Count",
    "plt": "Platelets", "thrombocytes": "Platelets",
    "mcv": "MCV", "mch": "MCH", "mchc": "MCHC",
    "anc": "Neutrophils", "segs": "Neutrophils",
    "esr": "ESR",
    "fbs": "Glucose", "rbs": "Glucose", "blood sugar": "Glucose",
    "hba1c": "HbA1c", "a1c": "HbA1c", "glycated hemoglobin": "HbA1c",
    "na": "Sodium", "k": "Potassium", "cl": "Chloride",
    "bun": "BUN", "blood urea nitrogen": "BUN",
    "cr": "Creatinine", "serum creatinine": "Creatinine",
    "egfr": "eGFR", "gfr": "eGFR",
    "tc": "Total Cholesterol", "cholesterol": "Total Cholesterol",
    "ldl": "LDL Cholesterol", "bad cholesterol": "LDL Cholesterol",
    "hdl": "HDL Cholesterol", "good cholesterol": "HDL Cholesterol",
    "tg": "Triglycerides", "trig": "Triglycerides",
    "alt": "ALT", "sgpt": "ALT",
    "ast": "AST", "sgot": "AST",
    "alp": "ALP", "alkaline phosphatase": "ALP",
    "t.bili": "Total Bilirubin", "bilirubin": "Total Bilirubin",
    "tp": "Total Protein", "alb": "Albumin",
    "tsh": "TSH", "thyroid stimulating hormone": "TSH",
    "ft3": "T3", "free t3": "T3", "ft4": "T4", "free t4": "T4",
    "ca": "Calcium", "fe": "Iron", "serum iron": "Iron",
    "vit d": "Vitamin D", "vitamin d": "Vitamin D",
    "b12": "Vitamin B12", "cobalamin": "Vitamin B12",
    "crp": "CRP", "c-reactive protein": "CRP",
    "inr": "INR", "uric acid": "Uric Acid", "urate": "Uric Acid",
}

UNIT_PATTERNS = [
    r'g/dl', r'mg/dl', r'ug/dl', r'mmol/l', r'umol/l', r'nmol/l',
    r'meq/l', r'u/l', r'iu/l', r'pg/ml', r'ng/ml', r'ng/dl',
    r'10\^3/ul', r'10\^6/ul', r'k/ul', r'k/mm3',
    r'mm/hr', r'seconds', r'sec', r'fl', r'pg',
    r'miu/l', r'ml/min/1\.73m2', r'miu/ml', r'%',
]

EXTRACT_RE = re.compile(
    r'([A-Za-z][A-Za-z0-9\.\-\s/]*?)'
    r'\s*(?:=|:|is|was|came|shows?|results?\s*(?:is)?)\s*'
    r'([<>]?\s*\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'
    r'\s*(' + '|'.join(UNIT_PATTERNS) + r')?',
    re.IGNORECASE
)

REF_RE = re.compile(
    r'(?:normal\s*range|reference\s*range|ref(?:erence)?|range)\s*(?:for\s*\w+\s*)?'
    r'[:\s]+(\d+(?:\.\d+)?)\s*[-\u2013\u2014to]+\s*(\d+(?:\.\d+)?)',
    re.IGNORECASE
)


def normalise_name(raw):
    key = raw.strip().lower()
    return ALIAS_MAP.get(key, raw.strip().title())


def parse_query(text):
    results = []
    seen = set()
    ref_ranges = REF_RE.findall(text)
    ref_idx = 0

    for m in EXTRACT_RE.finditer(text):
        raw_name = m.group(1).strip()
        raw_value = m.group(2).strip().lstrip('<>').strip()
        raw_unit = m.group(3).strip() if m.group(3) else ""

        if len(raw_name) < 2 or raw_name.lower() in {'my', 'the', 'a', 'an', 'is', 'was'}:
            continue

        canonical = normalise_name(raw_name)
        if canonical in seen:
            continue
        seen.add(canonical)

        try:
            value = float(raw_value)
        except ValueError:
            continue

        entry = {
            "test_name": canonical,
            "value": value,
            "unit": raw_unit,
            "user_ref_low": None,
            "user_ref_high": None,
        }

        if ref_idx < len(ref_ranges):
            entry["user_ref_low"] = float(ref_ranges[ref_idx][0])
            entry["user_ref_high"] = float(ref_ranges[ref_idx][1])
            ref_idx += 1

        results.append(entry)

    return results
