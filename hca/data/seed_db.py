"""
Seed the SQLite database from the Excel dataset.
Run once after init_db():
    python data/seed_db.py
"""
import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import init_db, SessionLocal, Claim, Patient, Policy

DATASET = "data/healthcare_compliance_cleaned.xlsx"


def seed():
    init_db()
    db = SessionLocal()

    if not os.path.exists(DATASET):
        print(f"Dataset not found: {DATASET}")
        print("Run:  python data/generate_dataset.py  first")
        return

    df = pd.read_excel(DATASET)
    print(f"Seeding {len(df)} rows from {DATASET} ...")

    claim_count   = 0
    patient_ids   = set()

    for _, row in df.iterrows():
        r = row.where(pd.notnull(row), None).to_dict()

        # ── Patient ──────────────────────────────────────────────
        pid = str(r.get("patient_id", ""))
        if pid and pid not in patient_ids:
            if not db.query(Patient).filter(Patient.patient_id == pid).first():
                db.add(Patient(
                    patient_id    = pid,
                    name          = f"Patient {pid}",
                    provider_name = r.get("provider_name"),
                    facility      = r.get("facility"),
                    payer         = r.get("payer"),
                ))
            patient_ids.add(pid)

        # ── Claim ─────────────────────────────────────────────────
        cid = str(r.get("claim_id", ""))
        if cid and not db.query(Claim).filter(Claim.claim_id == cid).first():
            db.add(Claim(
                claim_id                  = cid,
                patient_id                = pid,
                provider_name             = r.get("provider_name"),
                facility                  = r.get("facility"),
                payer                     = r.get("payer"),
                icd10_code                = str(r.get("icd10_code", "") or ""),
                icd10_description         = r.get("icd10_description"),
                cpt_code                  = str(r.get("cpt_code", "") or ""),
                cpt_description           = r.get("cpt_description"),
                billed_amount             = float(r.get("billed_amount") or 0),
                allowed_amount            = float(r.get("allowed_amount") or 0),
                paid_amount               = float(r.get("paid_amount") or 0),
                claim_status              = r.get("claim_status", "PENDING"),
                denial_reason             = r.get("denial_reason"),
                service_date              = str(r.get("service_date", ""))[:10],
                submission_date           = str(r.get("submission_date", ""))[:10],
                prior_auth_required       = str(r.get("prior_auth_required", "N")),
                documentation_required    = str(r.get("documentation_required", "N")),
                policy_impact_level       = r.get("policy_impact_level", "LOW"),
                claim_denial_flag         = int(r.get("claim_denial_flag") or 0),
                provider_compliance_score = float(r.get("provider_compliance_score") or 80),
                resubmission_flag         = str(r.get("resubmission_flag", "N")),
            ))
            claim_count += 1

    db.commit()
    db.close()
    print(f"Seeded: {claim_count} claims, {len(patient_ids)} patients")


if __name__ == "__main__":
    seed()
