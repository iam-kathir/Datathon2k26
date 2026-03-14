"""
Agent 2 — Thinker
Scans claims against policy changes.
Uses XGBoost to score rejection probability.
Uses Claude to explain the clinical risk reasoning.
Updates policies_master.xlsx with new rules.
"""
import os
import json
import pickle
import pandas as pd
import anthropic
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL_PATH    = "ml/model.pkl"
ENCODERS_PATH = "ml/encoders.pkl"
POLICY_EXCEL  = "data/policies_master.xlsx"

FEATURES = [
    "cpt_code", "icd10_code", "payer",
    "prior_auth_required", "documentation_required",
    "policy_impact_level", "provider_compliance_score",
    "policy_compliance_deadline_days",
]

# ── ML scoring ────────────────────────────────────────────────────

def _load_model():
    """Load XGBoost model and label encoders from disk."""
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    return bundle["model"], bundle["encoders"]


def scan_and_score(claim_dict: dict) -> dict:
    """
    Score a single claim using XGBoost.
    Returns risk_score (0-1), risk_level, and SHAP explanation.
    """
    try:
        model, encoders = _load_model()
    except FileNotFoundError:
        # Model not trained yet — return neutral score
        return {"risk_score": 0.5, "risk_level": "MEDIUM", "shap_explanation": []}

    import shap
    row = {}
    for feat in FEATURES:
        val = str(claim_dict.get(feat, "Unknown"))
        if feat in encoders:
            le = encoders[feat]
            val = int(le.transform([val])[0]) if val in le.classes_ else 0
        else:
            try:
                val = float(val)
            except ValueError:
                val = 0.0
        row[feat] = val

    df = pd.DataFrame([row])
    prob = float(model.predict_proba(df)[0][1])
    level = "HIGH" if prob > 0.7 else ("MEDIUM" if prob > 0.4 else "LOW")

    # SHAP explanation
    try:
        explainer  = shap.TreeExplainer(model)
        shap_vals  = explainer.shap_values(df)
        top = sorted(zip(FEATURES, shap_vals[0]),
                     key=lambda x: abs(x[1]), reverse=True)[:3]
        explanation = [f"{f}: {v:+.3f}" for f, v in top]
    except Exception:
        explanation = []

    return {
        "risk_score":       round(prob, 4),
        "risk_level":       level,
        "shap_explanation": explanation,
    }


# ── Claude clinical reasoning ─────────────────────────────────────

def claude_explain_risk(claim_dict: dict, policy_dict: dict) -> str:
    """
    Claude explains in plain English why this specific claim
    is at risk under the new policy.
    """
    prompt = f"""
You are a US Medicare billing compliance specialist.

A policy change has been detected. A specific patient claim may be affected.

Policy change summary: {policy_dict.get('summary', '')}
Codes affected by this policy: {policy_dict.get('affected_codes', [])}
New documentation required: {policy_dict.get('new_requirements', [])}
What triggers a denial: {policy_dict.get('denial_triggers', [])}

Patient claim details:
- Claim ID: {claim_dict.get('claim_id', '')}
- CPT Code: {claim_dict.get('cpt_code', '')}
- Payer: {claim_dict.get('payer', '')}
- Prior auth required: {claim_dict.get('prior_auth_required', 'N')}
- Documentation on file: {claim_dict.get('documentation_required', 'N')}
- XGBoost risk score: {claim_dict.get('risk_score', 0):.2f}
- Current status: {claim_dict.get('claim_status', 'PENDING')}

In 2-3 sentences, explain specifically WHY this claim is at risk of denial.
Be clinical and specific. Reference the exact policy requirement and the claim gap.
Do not use bullet points. Plain paragraph only.
"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Risk identified: Claim uses code {claim_dict.get('cpt_code')} which is affected by the policy change. ({e})"


# ── Policy Excel update ───────────────────────────────────────────

def update_policy_excel(policy_dict: dict) -> str:
    """
    Add or update a row in policies_master.xlsx.
    If policy_id exists → update existing row.
    If new → append a new row.
    Returns: 'ADDED' or 'UPDATED'
    """
    os.makedirs("data", exist_ok=True)
    if os.path.exists(POLICY_EXCEL):
        df = pd.read_excel(POLICY_EXCEL)
    else:
        df = pd.DataFrame()

    pid = policy_dict.get("policy_id", "")
    flat = {
        k: (json.dumps(v) if isinstance(v, list) else v)
        for k, v in policy_dict.items()
    }
    flat["last_updated"] = datetime.utcnow().isoformat()

    if pid and "policy_id" in df.columns and pid in df["policy_id"].values:
        for col, val in flat.items():
            df.loc[df["policy_id"] == pid, col] = val
        action = "UPDATED"
    else:
        df = pd.concat([df, pd.DataFrame([flat])], ignore_index=True)
        action = "ADDED"

    df.to_excel(POLICY_EXCEL, index=False)
    return action


# ── Dynamic date-based claim filtering ───────────────────────────

def get_claims_for_date(claims_df: pd.DataFrame, check_date: str = None) -> pd.DataFrame:
    """
    Return only claims where service_date <= check_date.
    Defaults to today — simulates real-time daily monitoring.
    """
    if check_date is None:
        check_date = date.today().isoformat()
    claims_df = claims_df.copy()
    claims_df["service_date"] = pd.to_datetime(claims_df["service_date"], errors="coerce")
    mask = claims_df["service_date"].dt.date <= datetime.strptime(check_date, "%Y-%m-%d").date()
    return claims_df[mask]


# ── Scan claims against a policy ─────────────────────────────────

def scan_claims_against_policy(claims_df: pd.DataFrame, policy_dict: dict) -> list:
    """
    Filter claims by affected codes, score each, get Claude explanation.
    Returns list of enriched claim dicts.
    """
    affected_codes = [str(c) for c in policy_dict.get("affected_codes", [])]
    if not affected_codes:
        return []

    mask = claims_df["cpt_code"].astype(str).isin(affected_codes)
    affected = claims_df[mask].copy()

    results = []
    for _, row in affected.iterrows():
        claim = row.to_dict()
        risk = scan_and_score(claim)
        claim.update(risk)
        explanation = claude_explain_risk(claim, policy_dict)
        claim["claude_reasoning"] = explanation
        results.append(claim)

    # Sort by risk descending
    results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return results
