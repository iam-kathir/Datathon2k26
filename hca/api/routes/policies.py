"""
Policy CRUD routes.
GET  /policies/           — list all
GET  /policies/{id}       — get one
POST /policies/           — create
PUT  /policies/{id}       — update
DELETE /policies/{id}     — delete
GET  /policies/impact/{level} — filter by HIGH/MEDIUM/LOW
"""
import json, uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db, Policy, AuditLog
from api.models import PolicyCreate, PolicyUpdate, PolicyOut

router = APIRouter()


def _log(db, action, entity_id, details):
    db.add(AuditLog(action=action, agent="API", entity_id=str(entity_id), details=details))
    db.commit()


@router.get("/", response_model=List[PolicyOut])
def list_policies(
    impact: Optional[str] = None,
    policy_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Policy)
    if impact:
        q = q.filter(Policy.impact_level == impact.upper())
    if policy_type:
        q = q.filter(Policy.policy_type == policy_type)
    return q.offset(skip).limit(limit).all()


@router.get("/stats")
def policy_stats(db: Session = Depends(get_db)):
    all_p = db.query(Policy).all()
    return {
        "total":  len(all_p),
        "high":   sum(1 for p in all_p if p.impact_level == "HIGH"),
        "medium": sum(1 for p in all_p if p.impact_level == "MEDIUM"),
        "low":    sum(1 for p in all_p if p.impact_level == "LOW"),
        "total_financial_impact": sum(p.financial_impact_usd or 0 for p in all_p),
    }


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    p = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return p


@router.post("/", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(data: PolicyCreate, db: Session = Depends(get_db)):
    # Auto-generate policy_id if not provided
    if not data.policy_id:
        data.policy_id = f"POL-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    # Check duplicate
    existing = db.query(Policy).filter(Policy.policy_id == data.policy_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Policy {data.policy_id} already exists")
    p = Policy(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    _log(db, "POLICY_CREATED", p.policy_id, f"Created: {p.title}")
    return p


@router.put("/{policy_id}", response_model=PolicyOut)
def update_policy(policy_id: str, data: PolicyUpdate, db: Session = Depends(get_db)):
    p = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(p, field, val)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    _log(db, "POLICY_UPDATED", policy_id, f"Updated fields: {list(data.model_dump(exclude_none=True).keys())}")
    return p


@router.delete("/{policy_id}")
def delete_policy(policy_id: str, db: Session = Depends(get_db)):
    p = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    db.delete(p)
    db.commit()
    _log(db, "POLICY_DELETED", policy_id, f"Deleted: {p.title}")
    return {"deleted": policy_id, "title": p.title}


@router.get("/impact/{level}", response_model=List[PolicyOut])
def filter_by_impact(level: str, db: Session = Depends(get_db)):
    return db.query(Policy).filter(Policy.impact_level == level.upper()).all()
