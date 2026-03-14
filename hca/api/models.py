"""
Pydantic models (request/response schemas) for FastAPI.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Policy ────────────────────────────────────────────────────────

class PolicyCreate(BaseModel):
    policy_id:            Optional[str] = None
    title:                str
    policy_type:          Optional[str] = "LCD"
    issuer:               Optional[str] = "CMS HQ"
    effective_date:       Optional[str] = None
    affected_codes:       Optional[str] = "[]"
    new_requirements:     Optional[str] = "[]"
    denial_triggers:      Optional[str] = "[]"
    impact_level:         Optional[str] = "MEDIUM"
    financial_impact_usd: Optional[float] = 0.0
    deadline_days:        Optional[int] = 30
    summary:              Optional[str] = ""
    raw_text:             Optional[str] = ""
    source_url:           Optional[str] = ""


class PolicyUpdate(BaseModel):
    title:                Optional[str] = None
    policy_type:          Optional[str] = None
    issuer:               Optional[str] = None
    effective_date:       Optional[str] = None
    affected_codes:       Optional[str] = None
    new_requirements:     Optional[str] = None
    denial_triggers:      Optional[str] = None
    impact_level:         Optional[str] = None
    financial_impact_usd: Optional[float] = None
    deadline_days:        Optional[int] = None
    summary:              Optional[str] = None


class PolicyOut(PolicyCreate):
    id:         int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Patient ───────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    patient_id:    str
    name:          str
    dob:           Optional[str] = None
    gender:        Optional[str] = None
    provider_name: Optional[str] = None
    facility:      Optional[str] = None
    payer:         Optional[str] = None


class PatientOut(PatientCreate):
    id:         int
    added_date: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Claim ─────────────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    claim_id:               str
    patient_id:             str
    provider_name:          Optional[str] = None
    facility:               Optional[str] = None
    payer:                  Optional[str] = None
    icd10_code:             Optional[str] = None
    icd10_description:      Optional[str] = None
    cpt_code:               Optional[str] = None
    cpt_description:        Optional[str] = None
    billed_amount:          Optional[float] = 0.0
    allowed_amount:         Optional[float] = 0.0
    paid_amount:            Optional[float] = 0.0
    claim_status:           Optional[str] = "PENDING"
    denial_reason:          Optional[str] = None
    service_date:           Optional[str] = None
    submission_date:        Optional[str] = None
    prior_auth_required:    Optional[str] = "N"
    documentation_required: Optional[str] = "N"
    policy_impact_level:    Optional[str] = "LOW"
    claim_denial_flag:      Optional[int] = 0
    provider_compliance_score: Optional[float] = 80.0


class ClaimUpdate(BaseModel):
    claim_status:           Optional[str] = None
    denial_reason:          Optional[str] = None
    risk_score:             Optional[float] = None
    risk_level:             Optional[str] = None
    shap_explanation:       Optional[str] = None
    policy_impact_level:    Optional[str] = None
    resubmission_flag:      Optional[str] = None
    prior_auth_required:    Optional[str] = None
    documentation_required: Optional[str] = None


class ClaimOut(ClaimCreate):
    id:               int
    risk_score:       Optional[float] = None
    risk_level:       Optional[str] = None
    shap_explanation: Optional[str] = None
    resubmission_flag: Optional[str] = None
    created_at:       Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── AuditLog ──────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id:        int
    action:    str
    agent:     str
    entity_id: Optional[str] = None
    details:   Optional[str] = None
    timestamp: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Agent request/response models ─────────────────────────────────

class WatcherRequest(BaseModel):
    url:  Optional[str] = None
    text: Optional[str] = None   # raw text if user types/pastes


class ThinkerRequest(BaseModel):
    policy_id:  str
    check_date: Optional[str] = None  # defaults to today


class FixerRequest(BaseModel):
    claim_id:  str
    policy_id: str


class FixerResponse(BaseModel):
    claim_id:   str
    fix_plan:   str
    priority:   str
    saved_to_log: bool
