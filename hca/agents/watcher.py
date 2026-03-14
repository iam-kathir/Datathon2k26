"""
Agent 1 — Watcher
Monitors CMS portals, reads uploaded policy files,
and uses Claude API to extract structured compliance data
from unstructured legal text.
"""
import os
import json
import anthropic
from dotenv import load_dotenv

from utils.pdf_reader import extract_text
from utils.cms_scraper import fetch_page_text, fetch_cms_news

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Claude extraction prompt ──────────────────────────────────────
EXTRACT_PROMPT = """
You are a US Medicare billing compliance expert with 20 years of experience.

Read the policy document text below and extract EXACTLY these fields.
Respond ONLY in valid JSON — no markdown, no preamble, no explanation.

{{
  "title":                "short human-readable policy title",
  "policy_type":          "one of: LCD | NCD | Fee Schedule Update | Prior Auth Requirement | CMS Transmittal | Coverage Determination | APC Update",
  "issuer":               "one of: CMS HQ | OIG | HHS | AMA | N/A",
  "effective_date":       "YYYY-MM-DD or empty string",
  "affected_codes":       ["list of CPT or HCPCS codes mentioned, e.g. G0439, 99213"],
  "new_requirements":     ["list of new documentation, tests, or forms now required"],
  "denial_triggers":      ["list of exact conditions that will cause claim denial"],
  "impact_level":         "HIGH or MEDIUM or LOW",
  "financial_impact_usd": 0,
  "deadline_days":        30,
  "summary":              "ONE sentence plain-English summary of what changed and why it matters"
}}

Rules:
- affected_codes must be real CPT/HCPCS code strings
- If you cannot find a field, use an empty string or empty list
- financial_impact_usd: estimate dollar impact if mentioned, else 0
- deadline_days: compliance window in days, default 30 if not stated
- impact_level HIGH = denial risk or major reimbursement change
- impact_level MEDIUM = documentation change, moderate impact
- impact_level LOW = minor update, informational

Policy document text:
{text}
"""


# ── Core extraction function ──────────────────────────────────────

def analyse_policy_text(raw_text: str) -> dict:
    """
    Send raw policy text to Claude.
    Claude extracts structured compliance data and returns JSON.
    """
    prompt = EXTRACT_PROMPT.replace("{text}", raw_text[:6000])
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    # Strip any accidental markdown fences
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return a safe fallback with raw text included
        return {
            "title": "Policy extracted (parse error)",
            "policy_type": "Unknown",
            "issuer": "Unknown",
            "effective_date": "",
            "affected_codes": [],
            "new_requirements": [],
            "denial_triggers": [],
            "impact_level": "MEDIUM",
            "financial_impact_usd": 0,
            "deadline_days": 30,
            "summary": text[:500],
        }


# ── Input handlers ────────────────────────────────────────────────

def process_uploaded_file(file_bytes: bytes, filename: str) -> tuple:
    """
    Handle user-uploaded PDF or TXT file.
    Returns (extracted_policy_dict, raw_text).
    """
    raw = extract_text(file_bytes, filename)
    policy = analyse_policy_text(raw)
    return policy, raw


def watch_cms_url(url: str) -> tuple:
    """
    Fetch a CMS page URL, extract its text, run through Claude.
    Returns (extracted_policy_dict, raw_text).
    """
    raw = fetch_page_text(url)
    policy = analyse_policy_text(raw)
    return policy, raw


def get_live_news() -> list:
    """Return live CMS news articles."""
    return fetch_cms_news()


# ── Policy comparison helper ──────────────────────────────────────

def compare_policies(old_dict: dict, new_dict: dict) -> dict:
    """
    Compare two policy versions and return what changed.
    Useful for showing the delta when a policy is updated.
    """
    changes = {}
    for key in ["affected_codes", "new_requirements", "denial_triggers",
                "impact_level", "effective_date", "deadline_days"]:
        old_val = old_dict.get(key)
        new_val = new_dict.get(key)
        if old_val != new_val:
            changes[key] = {"before": old_val, "after": new_val}
    return changes
