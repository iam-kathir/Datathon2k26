"""Standalone risk predictor — wraps trained XGBoost model."""
import pickle
import pandas as pd

FEATURES = [
    "cpt_code","icd10_code","payer",
    "prior_auth_required","documentation_required",
    "policy_impact_level","provider_compliance_score",
    "policy_compliance_deadline_days",
]
MODEL_PATH = "ml/model.pkl"


def _load():
    with open(MODEL_PATH,"rb") as f:
        return pickle.load(f)


def predict_single(claim_dict: dict) -> dict:
    try:
        bundle = _load()
    except FileNotFoundError:
        return {"risk_score":0.5,"risk_level":"MEDIUM","shap_explanation":[]}

    model, encoders = bundle["model"], bundle["encoders"]
    row = {}
    for feat in FEATURES:
        val = str(claim_dict.get(feat,"Unknown"))
        if feat in encoders:
            le = encoders[feat]
            row[feat] = int(le.transform([val])[0]) if val in le.classes_ else 0
        else:
            try: row[feat] = float(val)
            except: row[feat] = 0.0

    df   = pd.DataFrame([row])
    prob = float(model.predict_proba(df)[0][1])
    level = "HIGH" if prob > 0.7 else ("MEDIUM" if prob > 0.4 else "LOW")

    try:
        import shap
        exp = shap.TreeExplainer(model)
        sv  = exp.shap_values(df)
        top = sorted(zip(FEATURES,sv[0]),key=lambda x:abs(x[1]),reverse=True)[:3]
        explanation = [f"{f}: {v:+.3f}" for f,v in top]
    except:
        explanation = []

    return {"risk_score":round(prob,4),"risk_level":level,"shap_explanation":explanation}


def predict_batch(claims:list)->list:
    return [{**c,**predict_single(c)} for c in claims]
