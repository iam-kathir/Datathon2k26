"""
Train XGBoost claim denial model.
Run once: python ml/train_model.py
"""
import os, pickle, random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

FEATURES = [
    "cpt_code","icd10_code","payer",
    "prior_auth_required","documentation_required",
    "policy_impact_level","provider_compliance_score",
    "policy_compliance_deadline_days",
]
TARGET = "claim_denial_flag"

CPT_CODES     = ["99213","99214","80053","G0438","G0439","71046","36415","99291","99285","93000"]
ICD10_CODES   = ["I10","M54.5","E11.9","J06.9","N18.3","F32.1","Z79.899","K21.0","J18.9","R51"]
PAYERS        = ["Medicare Part B","Medicare Part A","Medicaid","Aetna","Cigna",
                 "Humana","Blue Cross Blue Shield","UnitedHealth","Anthem"]
PROVIDERS     = ["Dr. Emily Davis","Dr. Robert Chen","Dr. Sarah Johnson","Dr. Priya Patel","Dr. Michael Lee"]
IMPACT_LEVELS = ["LOW","MEDIUM","HIGH"]
DENIAL_CODES  = {"G0439","G0438","80053","99291"}


def generate_synthetic(n=5000):
    random.seed(42); np.random.seed(42)
    base = datetime(2022,1,1)
    rows = []
    for i in range(n):
        cpt    = random.choice(CPT_CODES)
        impact = random.choice(IMPACT_LEVELS)
        prior  = random.choice(["Y","N"])
        doc    = random.choice(["Y","N"])
        comp   = round(random.uniform(65,95),1)
        dead   = random.choice([30,60,90,120,180])
        p = 0.15
        if cpt in DENIAL_CODES: p += 0.20
        if prior == "Y":        p += 0.15
        if doc == "N":          p += 0.10
        if impact == "HIGH":    p += 0.12
        if comp < 75:           p += 0.08
        p = min(p, 0.85)
        denied = 1 if random.random() < p else 0
        svc = base + timedelta(days=random.randint(0,800))
        rows.append({
            "claim_id": f"CLM{100000+i:06d}",
            "patient_id": f"PAT{random.randint(10000,99999)}",
            "service_date": svc.strftime("%Y-%m-%d"),
            "cpt_code": cpt,
            "icd10_code": random.choice(ICD10_CODES),
            "payer": random.choice(PAYERS),
            "provider_name": random.choice(PROVIDERS),
            "billed_amount": round(random.uniform(200,5000),2),
            "prior_auth_required": prior,
            "documentation_required": doc,
            "policy_impact_level": impact,
            "provider_compliance_score": comp,
            "policy_compliance_deadline_days": dead,
            TARGET: denied,
            "claim_status": "DENIED" if denied else "APPROVED",
        })
    return pd.DataFrame(rows)


def train():
    os.makedirs("ml",   exist_ok=True)
    os.makedirs("data", exist_ok=True)

    real = "data/healthcare_compliance_cleaned.xlsx"
    if os.path.exists(real):
        print("Loading real dataset...")
        df_real = pd.read_excel(real)
        cols = [c for c in FEATURES+[TARGET] if c in df_real.columns]
        df_real = df_real[cols].dropna()
    else:
        df_real = pd.DataFrame()

    print("Generating 5000 synthetic rows...")
    df_synth = generate_synthetic(5000)
    df_synth.to_excel("data/expanded_claims.xlsx", index=False)

    df = pd.concat([df_real, df_synth[FEATURES+[TARGET]]], ignore_index=True)
    print(f"Total training rows: {len(df)}")

    encoders = {}
    cat_cols = ["cpt_code","icd10_code","payer","prior_auth_required",
                "documentation_required","policy_impact_level"]
    for col in cat_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

    X = df[FEATURES].fillna(0)
    y = df[TARGET].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                          subsample=0.8, colsample_bytree=0.8,
                          use_label_encoder=False, eval_metric="logloss", random_state=42)
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    y_pred = model.predict(X_te)
    y_prob = model.predict_proba(X_te)[:,1]
    print("\n=== Model Evaluation ===")
    print(classification_report(y_te, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y_te, y_prob):.4f}")

    with open("ml/model.pkl","wb") as f:
        pickle.dump({"model": model, "encoders": encoders, "features": FEATURES}, f)
    print("Saved: ml/model.pkl")


if __name__ == "__main__":
    train()
