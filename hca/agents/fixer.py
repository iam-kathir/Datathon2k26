"""
Agent 3 — Fixer
Generates specific, numbered corrective action plans
for flagged claims using Claude API.
"""
import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

FIX_PROMPT = """
You are a senior US healthcare billing compliance specialist with 15 years of experience.

A claim has been flagged as HIGH RISK of denial due to a recent Medicare policy change.
Generate a specific, actionable corrective action plan.

POLICY CHANGE:
Summary: {policy_summary}
New requirements: {requirements}
What triggers denial: {denial_triggers}
Compliance deadline: {deadline_days} days from today

FLAGGED CLAIM:
Claim ID: {claim_id}
Patient ID: {patient_id}
CPT Code: {cpt_code}
Payer: {payer}
Billed Amount: ${billed_amount}
Current Status: {status}
Denial Reason (if denied): {denial_reason}
Prior Auth Required: {prior_auth}
Documentation on File: {doc_required}

Generate a numbered corrective action checklist with 5 to 7 steps.
Rules:
- Each step must be specific and actionable
- Reference exact document names or form numbers where applicable
- Step 1 should always be the MOST URGENT action
- Last step must always be the resubmission instruction with deadline
- End with a single line: PRIORITY: URGENT or HIGH or MEDIUM
"""


def generate_fix_plan(claim_dict: dict, policy_dict: dict) -> str:
    prompt = FIX_PROMPT.format(
        policy_summary  = policy_dict.get("summary", "Policy change detected"),
        requirements    = ", ".join(policy_dict.get("new_requirements", [])),
        denial_triggers = ", ".join(policy_dict.get("denial_triggers", [])),
        deadline_days   = policy_dict.get("deadline_days", 30),
        claim_id        = claim_dict.get("claim_id", ""),
        patient_id      = claim_dict.get("patient_id", ""),
        cpt_code        = claim_dict.get("cpt_code", ""),
        payer           = claim_dict.get("payer", ""),
        billed_amount   = claim_dict.get("billed_amount", 0),
        status          = claim_dict.get("claim_status", "PENDING"),
        denial_reason   = claim_dict.get("denial_reason", "N/A"),
        prior_auth      = claim_dict.get("prior_auth_required", "N"),
        doc_required    = claim_dict.get("documentation_required", "N"),
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return (
            f"1. Verify claim {claim_dict.get('claim_id')} on payer portal\n"
            f"2. Obtain required documentation\n"
            f"3. Resubmit within {policy_dict.get('deadline_days', 30)} days\n"
            f"[Claude error: {e}]"
        )


def extract_priority(fix_text: str) -> str:
    for line in fix_text.split("\n"):
        u = line.upper()
        if "PRIORITY:" in u:
            if "URGENT" in u: return "URGENT"
            if "HIGH"   in u: return "HIGH"
            if "MEDIUM" in u: return "MEDIUM"
    return "HIGH"


def parse_fix_steps(fix_text: str) -> list:
    steps = []
    for line in fix_text.split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "." in line[:3]:
            steps.append(line)
    return steps if steps else [fix_text]


def generate_fixes_for_all(flagged_claims: list, policy_dict: dict) -> list:
    results = []
    for claim in flagged_claims:
        fix_text = generate_fix_plan(claim, policy_dict)
        results.append({
            "claim_id":      claim.get("claim_id"),
            "patient_id":    claim.get("patient_id"),
            "cpt_code":      claim.get("cpt_code"),
            "billed_amount": claim.get("billed_amount"),
            "risk_level":    claim.get("risk_level", "MEDIUM"),
            "fix_plan":      fix_text,
            "steps":         parse_fix_steps(fix_text),
            "priority":      extract_priority(fix_text),
        })
    return results
