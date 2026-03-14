"""
Agent trigger routes — call Watcher, Thinker, Fixer from the API.
POST /agents/watcher/url       — trigger watcher on a URL
POST /agents/watcher/upload    — trigger watcher on uploaded text
POST /agents/thinker/scan      — trigger thinker scan
POST /agents/fixer/fix         — trigger fixer for a claim
GET  /agents/logs              — get audit log
"""
import json
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from api.database import get_db, Policy, Claim, Patient, AuditLog
from api.models import WatcherRequest, ThinkerRequest, FixerRequest, FixerResponse

router = APIRouter()


# ── Watcher ───────────────────────────────────────────────────────

@router.post("/watcher/url")
def watcher_scan_url(request: WatcherRequest, db: Session = Depends(get_db)):
    """Fetch CMS URL, extract policy with Claude, save to DB."""
    from agents.watcher import watch_cms_url
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        result, raw = watch_cms_url(request.url)
        _save_policy(result, raw, request.url, db)
        return {"status": "success", "policy": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watcher/upload")
async def watcher_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept PDF/TXT upload, extract policy with Claude, save to DB."""
    from agents.watcher import process_uploaded_file
    content = await file.read()
    try:
        result, raw = process_uploaded_file(content, file.filename)
        _save_policy(result, raw, f"upload:{file.filename}", db)
        return {"status": "success", "policy": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watcher/text")
def watcher_raw_text(request: WatcherRequest, db: Session = Depends(get_db)):
    """Paste raw text, Claude extracts policy."""
    from agents.watcher import analyse_policy_text
    if not request.text:
        raise HTTPException(status_code=400, detail="text is required")
    try:
        result = analyse_policy_text(request.text)
        _save_policy(result, request.text, "manual_text", db)
        return {"status": "success", "policy": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watcher/news")
def watcher_news():
    """Return live CMS news feed."""
    from utils.cms_scraper import fetch_cms_news
    return {"news": fetch_cms_news()}


def _save_policy(result, raw, source_url, db):
    import uuid
    from datetime import datetime
    from api.database import Policy
    pid = result.get("policy_id") or f"POL-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    existing = db.query(Policy).filter(Policy.policy_id == pid).first()
    if existing:
        # Update existing policy
        for k, v in result.items():
            if hasattr(existing, k):
                setattr(existing, k, json.dumps(v) if isinstance(v, list) else v)
        existing.updated_at = datetime.utcnow()
    else:
        p = Policy(
            policy_id            = pid,
            title                = result.get("title", "Unnamed Policy"),
            policy_type          = result.get("policy_type", "LCD"),
            issuer               = result.get("issuer", "CMS HQ"),
            effective_date       = result.get("effective_date", ""),
            affected_codes       = json.dumps(result.get("affected_codes", [])),
            new_requirements     = json.dumps(result.get("new_requirements", [])),
            denial_triggers      = json.dumps(result.get("denial_triggers", [])),
            impact_level         = result.get("impact_level", "MEDIUM"),
            financial_impact_usd = result.get("financial_impact_usd", 0),
            deadline_days        = result.get("deadline_days", 30),
            summary              = result.get("summary", ""),
            raw_text             = raw[:4000],
            source_url           = source_url,
        )
        db.add(p)
    db.add(AuditLog(action="POLICY_EXTRACTED", agent="Watcher",
                    entity_id=pid, details=f"Source:{source_url}"))
    db.commit()


# ── Thinker ───────────────────────────────────────────────────────

@router.post("/thinker/scan")
def thinker_scan(request: ThinkerRequest, db: Session = Depends(get_db)):
    """Scan all claims against a policy, score with XGBoost + Claude."""
    from agents.thinker import scan_and_score, claude_explain_risk
    import pandas as pd

    policy = db.query(Policy).filter(Policy.policy_id == request.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy_dict = {
        "policy_id":       policy.policy_id,
        "title":           policy.title,
        "affected_codes":  json.loads(policy.affected_codes or "[]"),
        "new_requirements":json.loads(policy.new_requirements or "[]"),
        "denial_triggers": json.loads(policy.denial_triggers or "[]"),
        "impact_level":    policy.impact_level,
        "deadline_days":   policy.deadline_days,
        "summary":         policy.summary,
    }

    check_date = request.check_date or date.today().isoformat()
    claims = db.query(Claim).filter(Claim.service_date <= check_date).all()

    affected_codes = policy_dict["affected_codes"]
    flagged = []

    for c in claims:
        if c.cpt_code not in affected_codes:
            continue
        claim_dict = {
            "claim_id":               c.claim_id,
            "patient_id":             c.patient_id,
            "cpt_code":               c.cpt_code,
            "icd10_code":             c.icd10_code,
            "payer":                  c.payer,
            "prior_auth_required":    c.prior_auth_required,
            "documentation_required": c.documentation_required,
            "policy_impact_level":    c.policy_impact_level,
            "provider_compliance_score": c.provider_compliance_score,
            "billed_amount":          c.billed_amount,
            "claim_status":           c.claim_status,
            "denial_reason":          c.denial_reason,
        }
        # Score with XGBoost
        try:
            risk = scan_and_score(claim_dict)
        except Exception:
            risk = {"risk_score": 0.5, "risk_level": "MEDIUM", "shap_explanation": []}

        # Claude explanation
        try:
            explanation = claude_explain_risk(claim_dict, policy_dict)
        except Exception:
            explanation = "Risk identified based on policy change."

        # Update claim in DB
        c.risk_score       = risk["risk_score"]
        c.risk_level       = risk["risk_level"]
        c.shap_explanation = json.dumps(risk.get("shap_explanation", []))
        db.commit()

        flagged.append({
            **claim_dict,
            "risk_score":       risk["risk_score"],
            "risk_level":       risk["risk_level"],
            "shap_explanation": risk.get("shap_explanation", []),
            "claude_reasoning": explanation,
        })

    db.add(AuditLog(action="THINKER_SCAN", agent="Thinker",
                    entity_id=request.policy_id,
                    details=f"Flagged {len(flagged)} claims on {check_date}"))
    db.commit()
    return {
        "policy_id":      request.policy_id,
        "check_date":     check_date,
        "total_scanned":  len(claims),
        "flagged_count":  len(flagged),
        "total_at_risk":  round(sum(f.get("billed_amount", 0) for f in flagged), 2),
        "flagged_claims": flagged,
    }


# ── Fixer ─────────────────────────────────────────────────────────

@router.post("/fixer/fix", response_model=FixerResponse)
def fixer_generate(request: FixerRequest, db: Session = Depends(get_db)):
    """Generate fix plan for a claim using Claude."""
    from agents.fixer import generate_fix_plan

    claim = db.query(Claim).filter(Claim.claim_id == request.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    policy = db.query(Policy).filter(Policy.policy_id == request.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    claim_dict = {
        "claim_id":     claim.claim_id,
        "patient_id":   claim.patient_id,
        "cpt_code":     claim.cpt_code,
        "payer":        claim.payer,
        "billed_amount": claim.billed_amount,
        "claim_status": claim.claim_status,
        "denial_reason": claim.denial_reason,
    }
    policy_dict = {
        "summary":          policy.summary,
        "new_requirements": json.loads(policy.new_requirements or "[]"),
        "denial_triggers":  json.loads(policy.denial_triggers or "[]"),
        "deadline_days":    policy.deadline_days,
    }

    try:
        fix_text = generate_fix_plan(claim_dict, policy_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Determine priority
    priority = "URGENT" if claim.risk_level == "HIGH" else (
               "HIGH"   if claim.risk_level == "MEDIUM" else "MEDIUM")

    # Save to audit log
    db.add(AuditLog(
        action="FIX_GENERATED", agent="Fixer",
        entity_id=claim.claim_id,
        details=json.dumps({"policy_id": request.policy_id, "fix": fix_text[:500]})
    ))
    # Mark claim for resubmission
    claim.resubmission_flag = "Y"
    db.commit()

    return FixerResponse(
        claim_id=request.claim_id,
        fix_plan=fix_text,
        priority=priority,
        saved_to_log=True
    )


# ── Audit log ─────────────────────────────────────────────────────

@router.get("/logs", response_model=List[dict])
def get_audit_logs(
    agent: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    q = db.query(AuditLog)
    if agent:
        q = q.filter(AuditLog.agent == agent)
    logs = q.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [{"id": l.id, "action": l.action, "agent": l.agent,
             "entity_id": l.entity_id, "details": l.details,
             "timestamp": str(l.timestamp)} for l in logs]
