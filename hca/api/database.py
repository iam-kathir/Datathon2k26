"""
Database setup — SQLAlchemy + SQLite
Creates all tables on first run.
"""
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, DateTime, Text, Boolean
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

os.makedirs("data", exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/database.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── Tables ────────────────────────────────────────────────────────

class Policy(Base):
    __tablename__ = "policies"
    id                       = Column(Integer, primary_key=True, index=True)
    policy_id                = Column(String, unique=True, index=True)
    title                    = Column(String)
    policy_type              = Column(String)
    issuer                   = Column(String)
    effective_date           = Column(String)
    affected_codes           = Column(Text)        # JSON list
    new_requirements         = Column(Text)        # JSON list
    denial_triggers          = Column(Text)        # JSON list
    impact_level             = Column(String)
    financial_impact_usd     = Column(Float, default=0)
    deadline_days            = Column(Integer, default=30)
    summary                  = Column(Text)
    raw_text                 = Column(Text)
    source_url               = Column(String)
    created_at               = Column(DateTime, default=datetime.utcnow)
    updated_at               = Column(DateTime, default=datetime.utcnow,
                                      onupdate=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"
    id            = Column(Integer, primary_key=True, index=True)
    patient_id    = Column(String, unique=True, index=True)
    name          = Column(String)
    dob           = Column(String)
    gender        = Column(String)
    provider_name = Column(String)
    facility      = Column(String)
    payer         = Column(String)
    added_date    = Column(DateTime, default=datetime.utcnow)


class Claim(Base):
    __tablename__ = "claims"
    id                     = Column(Integer, primary_key=True, index=True)
    claim_id               = Column(String, unique=True, index=True)
    patient_id             = Column(String, index=True)
    provider_name          = Column(String)
    facility               = Column(String)
    payer                  = Column(String)
    icd10_code             = Column(String)
    icd10_description      = Column(String)
    cpt_code               = Column(String)
    cpt_description        = Column(String)
    billed_amount          = Column(Float)
    allowed_amount         = Column(Float)
    paid_amount            = Column(Float)
    claim_status           = Column(String, default="PENDING")
    denial_reason          = Column(String)
    service_date           = Column(String)
    submission_date        = Column(String)
    prior_auth_required    = Column(String, default="N")
    documentation_required = Column(String, default="N")
    policy_impact_level    = Column(String, default="LOW")
    claim_denial_flag      = Column(Integer, default=0)
    risk_score             = Column(Float)
    risk_level             = Column(String)
    shap_explanation       = Column(Text)
    provider_compliance_score = Column(Float, default=80.0)
    resubmission_flag      = Column(String, default="N")
    created_at             = Column(DateTime, default=datetime.utcnow)
    updated_at             = Column(DateTime, default=datetime.utcnow,
                                    onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id        = Column(Integer, primary_key=True, index=True)
    action    = Column(String)
    agent     = Column(String)
    entity_id = Column(String)
    details   = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ── DB helpers ────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
