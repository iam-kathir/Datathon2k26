"""
Generate a synthetic expanded claims dataset (5000+ rows).
Run once:  python data/generate_dataset.py
Appends to healthcare_compliance_cleaned.xlsx if it exists,
or creates a new file.
"""
import os
import random
import pandas as pd
from datetime import datetime, timedelta

CPT_CODES = [
    "99213", "99214", "80053", "G0438", "G0439",
    "71046", "36415", "99291", "99285", "99232",
    "93000", "85025", "82947", "81003", "99203",
]
ICD10_CODES = [
    "I10", "M54.5", "E11.9", "J06.9", "N18.3",
    "F32.1", "Z79.899", "K21.0", "J18.9", "E78.5",
]
CPT_DESC = {
    "99213": "Office/outpatient visit established",
    "99214": "Office/outpatient visit established moderate",
    "80053": "Comprehensive metabolic panel",
    "G0438": "Annual wellness visit initial",
    "G0439": "Annual wellness visit subsequent",
    "71046": "Chest X-ray 2 views",
    "36415": "Venipuncture",
    "99291": "Critical care first 30-74 min",
    "99285": "Emergency dept visit high severity",
    "99232": "Hospital inpatient subsequent visit",
    "93000": "Electrocardiogram routine ECG",
    "85025": "Complete CBC with differential",
    "82947": "Glucose blood quantitative",
    "81003": "Urinalysis automated",
    "99203": "Office/outpatient visit new patient low",
}
ICD10_DESC = {
    "I10":    "Essential hypertension",
    "M54.5":  "Low back pain",
    "E11.9":  "Type 2 diabetes mellitus without complication",
    "J06.9":  "Acute upper respiratory infection",
    "N18.3":  "Chronic kidney disease stage 3",
    "F32.1":  "Major depressive disorder single episode moderate",
    "Z79.899":"Long-term drug use other",
    "K21.0":  "GERD with esophagitis",
    "J18.9":  "Pneumonia unspecified",
    "E78.5":  "Hyperlipidemia unspecified",
}
PAYERS   = ["Medicare Part B", "Medicare Part A", "Medicaid", "Aetna",
            "Cigna", "Humana", "Blue Cross Blue Shield", "UnitedHealthcare"]
PROVIDERS= ["Dr. Emily Davis", "Dr. Robert Chen", "Dr. Sarah Johnson",
            "Dr. Priya Patel", "Dr. Michael Lee"]
FACILITIES=["General Hospital", "Community Care Center", "Regional Health Clinic",
            "University Hospital", "City Medical Center"]
DENIAL_REASONS=[
    "Missing prior authorization",
    "Service not covered",
    "Incorrect billing code",
    "Medical necessity not established",
    "Timely filing limit exceeded",
    "Duplicate claim",
    "Coverage terminated",
]
POLICY_TYPES=["LCD","Fee Schedule Update","Prior Auth Requirement",
              "CMS Transmittal","Coverage Determination","NCD","APC Update"]
POLICY_ISSUERS=["CMS HQ","OIG","HHS","AMA"]
POLICY_ACTIONS=[
    "Documentation requirements tightened",
    "Reimbursement rate reduced",
    "New prior auth required",
    "Billing code retired",
    "Coverage criteria updated",
    "New billing code added",
    "Modifier requirement changed",
]


def gen_policy_title(ptype, quarter, year):
    return f"CMS Update {ptype} - Q{quarter} {year}"


def generate(n=5000):
    rows = []
    base = datetime(2022, 1, 1)

    for i in range(n):
        svc_date = base + timedelta(days=random.randint(0, 900))
        sub_date = svc_date + timedelta(days=random.randint(1, 14))
        denied   = random.random() < 0.26

        cpt  = random.choice(CPT_CODES)
        icd  = random.choice(ICD10_CODES)
        payer= random.choice(PAYERS)
        ptype= random.choice(POLICY_TYPES)
        qtr  = random.randint(1, 4)
        yr   = random.choice([2022, 2023, 2024])

        prior_auth = "Y" if random.random() < 0.3 else "N"
        doc_req    = "Y" if random.random() < 0.4 else "N"
        impact_lvl = random.choices(["HIGH","MEDIUM","LOW"], weights=[0.2,0.28,0.52])[0]
        compliance = random.choice([72.7, 77.8, 79.2, 88.6, 91.1])
        deadline   = random.choice([30, 60, 90, 120, 180])
        billed     = round(random.uniform(150, 5000), 2)
        allowed    = round(billed * random.uniform(0.4, 0.95), 2)
        paid       = 0.0 if denied else round(allowed * random.uniform(0.7, 1.0), 2)
        fin_impact = round(random.uniform(50, 500), 2)
        risk_flag  = 1 if denied else 0

        policy_eff = svc_date - timedelta(days=random.randint(10, 180))

        rows.append({
            "claim_id":                     f"CLM{100000 + i:06d}",
            "patient_id":                   f"PAT{random.randint(10000,99999)}",
            "service_date":                 svc_date.strftime("%Y-%m-%d"),
            "submission_date":              sub_date.strftime("%Y-%m-%d"),
            "year":                         svc_date.year,
            "provider_name":                random.choice(PROVIDERS),
            "facility":                     random.choice(FACILITIES),
            "payer":                        payer,
            "icd10_code":                   icd,
            "icd10_description":            ICD10_DESC.get(icd, icd),
            "cpt_code":                     cpt,
            "cpt_description":              CPT_DESC.get(cpt, cpt),
            "billed_amount":                billed,
            "allowed_amount":               allowed,
            "paid_amount":                  paid,
            "claim_status":                 "DENIED" if denied else "APPROVED",
            "denial_reason":                random.choice(DENIAL_REASONS) if denied else "N/A",
            "resubmission_flag":            "Y" if denied else "N",
            "claim_denial_flag":            risk_flag,
            "medicare_reimbursement_rate_usd": round(allowed * 1.05, 2),
            "prior_auth_required":          prior_auth,
            "documentation_required":       doc_req,
            "policy_impact_level":          impact_lvl,
            "policy_compliance_deadline_days": deadline,
            "policy_risk_flag":             1 if impact_lvl == "HIGH" else 0,
            "prior_auth_missing_risk":      1 if (prior_auth == "Y" and denied) else 0,
            "fee_work_rvu":                 round(random.uniform(0.5, 5.0), 2),
            "fee_conversion_factor":        random.choice([32.74, 33.06]),
            "provider_compliance_score":    compliance,
            "policy_type":                  ptype,
            "policy_title":                 gen_policy_title(ptype, qtr, yr),
            "policy_effective_date":        policy_eff.strftime("%Y-%m-%d"),
            "policy_action_required":       random.choice(POLICY_ACTIONS),
            "policy_financial_impact_usd":  fin_impact,
            "policy_issuing_body":          random.choice(POLICY_ISSUERS),
            "linked_policy_id":             f"POL{random.randint(10000,99999)}",
            "latest_audit_finding":         random.choices(
                ["No issues","Billing pattern anomaly"], weights=[0.85,0.15])[0],
            "audit_repayment_usd":          round(random.uniform(0,3000),2) if denied else 0,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    out_path = "data/healthcare_compliance_cleaned.xlsx"

    existing = None
    if os.path.exists(out_path):
        print(f"Existing file found — appending synthetic rows ...")
        existing = pd.read_excel(out_path)

    new_df = generate(5000)

    if existing is not None:
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["claim_id"])
    else:
        combined = new_df

    combined.to_excel(out_path, index=False)
    print(f"Dataset saved: {len(combined)} rows → {out_path}")
