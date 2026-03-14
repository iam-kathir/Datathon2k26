"""
Claims CRUD routes.
GET  /claims/                  — list all (with filters)
GET  /claims/{id}              — get one
POST /claims/                  — create
PUT  /claims/{id}              — update
DELETE /claims/{id}            — delete
GET  /claims/stats             — dashboard stats
GET  /claims/at-risk           — claims with HIGH/MEDIUM risk
GET  /claims/by-date/{date}    — claims with service_date <= date
GET  /claims/by-code/{code}    — filter by CPT code
POST /claims/bulk              — bulk insert (for dataset import)
"""
import json
from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db, Claim, AuditLog
from api.models import ClaimCreate, ClaimUpdate, ClaimOut

router = APIRouter()


def _log(db, action, eid, details):
    db.add(AuditLog(action=action, agent="API", entity_id=str(eid), details=details))
    db.commit()


@router.get("/stats")
def claims_stats(db: Session = Depends(get_db)):
    all_c = db.query(Claim).all()
    denied   = [c for c in all_c if c.claim_status == "DENIED"]
    approved = [c for c in all_c if c.claim_status == "APPROVED"]
    at_risk  = [c for c in all_c if c.risk_level in ("HIGH", "MEDIUM")]
    return {
        "total_claims":       len(all_c),
        "denied":             len(denied),
        "approved":           len(approved),
        "pending":            len([c for c in all_c if c.claim_status == "PENDING"]),
        "at_risk":            len(at_risk),
        "high_risk":          sum(1 for c in all_c if c.risk_level == "HIGH"),
        "medium_risk":        sum(1 for c in all_c if c.risk_level == "MEDIUM"),
        "total_billed":       round(sum(c.billed_amount or 0 for c in all_c), 2),
        "total_at_risk_usd":  round(sum(c.billed_amount or 0 for c in at_risk), 2),
        "rejection_rate_pct": round(len(denied) / max(len(all_c), 1) * 100, 2),
        "denial_reasons": _top_denial_reasons(denied),
    }


def _top_denial_reasons(denied_claims):
    from collections import Counter
    reasons = [c.denial_reason for c in denied_claims if c.denial_reason]
    return dict(Counter(reasons).most_common(5))


@router.get("/at-risk", response_model=List[ClaimOut])
def at_risk_claims(
    level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Claim).filter(Claim.risk_level.in_(["HIGH", "MEDIUM"]))
    if level:
        q = q.filter(Claim.risk_level == level.upper())
    return q.order_by(Claim.risk_score.desc()).all()


@router.get("/by-date/{check_date}", response_model=List[ClaimOut])
def claims_by_date(check_date: str, db: Session = Depends(get_db)):
    """Return all claims with service_date <= check_date (dynamic daily scan)"""
    return db.query(Claim).filter(Claim.service_date <= check_date).all()


@router.get("/by-code/{cpt_code}", response_model=List[ClaimOut])
def claims_by_code(cpt_code: str, db: Session = Depends(get_db)):
    return db.query(Claim).filter(Claim.cpt_code == cpt_code).all()


@router.get("/today", response_model=List[ClaimOut])
def claims_today(db: Session = Depends(get_db)):
    today = date.today().isoformat()
    return db.query(Claim).filter(Claim.service_date <= today).all()


@router.get("/", response_model=List[ClaimOut])
def list_claims(
    status_filter: Optional[str] = None,
    payer: Optional[str] = None,
    risk_level: Optional[str] = None,
    cpt_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    q = db.query(Claim)
    if status_filter:
        q = q.filter(Claim.claim_status == status_filter.upper())
    if payer:
        q = q.filter(Claim.payer == payer)
    if risk_level:
        q = q.filter(Claim.risk_level == risk_level.upper())
    if cpt_code:
        q = q.filter(Claim.cpt_code == cpt_code)
    return q.offset(skip).limit(limit).all()


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    c = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return c


@router.post("/", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
def create_claim(data: ClaimCreate, db: Session = Depends(get_db)):
    existing = db.query(Claim).filter(Claim.claim_id == data.claim_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Claim {data.claim_id} already exists")
    c = Claim(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    _log(db, "CLAIM_CREATED", c.claim_id, f"Payer:{c.payer} CPT:{c.cpt_code} Amount:{c.billed_amount}")
    return c


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_claims(claims: List[ClaimCreate], db: Session = Depends(get_db)):
    added, skipped = 0, 0
    for data in claims:
        if db.query(Claim).filter(Claim.claim_id == data.claim_id).first():
            skipped += 1
            continue
        db.add(Claim(**data.model_dump()))
        added += 1
    db.commit()
    _log(db, "BULK_IMPORT", "SYSTEM", f"Added:{added} Skipped:{skipped}")
    return {"added": added, "skipped": skipped}


@router.put("/{claim_id}", response_model=ClaimOut)
def update_claim(claim_id: str, data: ClaimUpdate, db: Session = Depends(get_db)):
    c = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(c, field, val)
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    _log(db, "CLAIM_UPDATED", claim_id, str(data.model_dump(exclude_none=True)))
    return c


@router.delete("/{claim_id}")
def delete_claim(claim_id: str, db: Session = Depends(get_db)):
    c = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    db.delete(c)
    db.commit()
    _log(db, "CLAIM_DELETED", claim_id, f"CPT:{c.cpt_code} Payer:{c.payer}")
    return {"deleted": claim_id}
