"""
Healthcare Compliance Agent — Streamlit Frontend
Run: streamlit run app.py
API must be running at localhost:8000
"""
import streamlit as st
import httpx, json, pandas as pd
from datetime import date, datetime

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare Compliance Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

API = "http://localhost:8000"

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:1.5rem 2rem;max-width:1400px;}
[data-testid="stSidebar"]{background:#0A1628;border-right:1px solid #1A2E4A;}
[data-testid="stSidebar"] *{color:#94A3B8!important;}
.metric-card{background:#0F172A;border:1px solid #1E293B;border-radius:12px;
             padding:1.1rem 1.3rem;text-align:center;}
.metric-val{font-size:1.9rem;font-weight:600;font-family:'DM Mono',monospace;margin-bottom:2px;}
.metric-lbl{font-size:0.7rem;text-transform:uppercase;letter-spacing:.08em;color:#64748B;}
.sec-hdr{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.12em;
         color:#38BDF8;margin-bottom:.8rem;padding-bottom:.4rem;border-bottom:1px solid #1E293B;}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.72rem;
       font-weight:600;font-family:'DM Mono',monospace;}
.badge-high  {background:#450A0A;color:#FCA5A5;border:1px solid #7F1D1D;}
.badge-med   {background:#451A03;color:#FCD34D;border:1px solid #78350F;}
.badge-low   {background:#052E16;color:#86EFAC;border:1px solid #14532D;}
.badge-denied{background:#450A0A;color:#FCA5A5;border:1px solid #7F1D1D;}
.badge-ok    {background:#052E16;color:#86EFAC;border:1px solid #14532D;}
.card{background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem 1.2rem;margin-bottom:.6rem;}
.fix-box{background:#071A10;border:1px solid #166534;border-radius:10px;
         padding:1rem 1.2rem;font-size:.83rem;color:#BBF7D0;
         font-family:'DM Mono',monospace;line-height:1.8;}
.stTabs [data-baseweb="tab-list"]{gap:0;background:#0A1628;border-radius:10px;
  padding:4px;border:1px solid #1E293B;}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:7px;
  color:#64748B;font-weight:500;font-size:.85rem;padding:8px 20px;}
.stTabs [aria-selected="true"]{background:#1E3A5F!important;color:#38BDF8!important;}
.stButton>button{background:#1A56DB;color:white;border:none;border-radius:8px;
  padding:.5rem 1.4rem;font-weight:500;font-family:'DM Sans',sans-serif;}
.stButton>button:hover{background:#1D4ED8;border:none;}
.main{background:#060D1A;}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────
def api_get(path, params=None):
    try:
        r = httpx.get(f"{API}{path}", params=params, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_post(path, data=None, files=None):
    try:
        if files:
            r = httpx.post(f"{API}{path}", files=files, timeout=60)
        else:
            r = httpx.post(f"{API}{path}", json=data, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_put(path, data):
    try:
        r = httpx.put(f"{API}{path}", json=data, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_delete(path):
    try:
        r = httpx.delete(f"{API}{path}", timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def badge(text, kind="high"):
    cls = {"HIGH":"badge-high","MEDIUM":"badge-med","LOW":"badge-low",
           "DENIED":"badge-denied","APPROVED":"badge-ok"}.get(text.upper(),"badge-med")
    return f"<span class='badge {cls}'>{text}</span>"

def color_map(level):
    return {"HIGH":"#F87171","MEDIUM":"#FBBF24","LOW":"#34D399"}.get(level,"#94A3B8")

def check_api():
    try:
        r = httpx.get(f"{API}/health", timeout=5)
        return r.status_code == 200
    except:
        return False


# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 .5rem;'>
      <div style='font-size:1.1rem;font-weight:700;color:#38BDF8;'>HealthGuard AI</div>
      <div style='font-size:.7rem;color:#475569;text-transform:uppercase;
                  letter-spacing:.1em;margin-top:2px;'>Compliance Agent v2.0</div>
    </div>
    <hr style='border-color:#1E293B;margin:.8rem 0;'>
    """, unsafe_allow_html=True)

    api_ok = check_api()
    st.markdown(
        f"<div style='font-size:.78rem;color:{'#22C55E' if api_ok else '#EF4444'};margin-bottom:.8rem;'>"
        f"{'● API online' if api_ok else '● API offline — run uvicorn api.main:app --reload'}</div>",
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        ["Dashboard","Watcher","Thinker","Fixer","Data Management","Audit Log"],
        label_visibility="collapsed"
    )

    # Quick stats in sidebar
    if api_ok:
        stats = api_get("/claims/stats")
        st.markdown("<hr style='border-color:#1E293B;margin:.8rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.7rem;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>Live stats</div>", unsafe_allow_html=True)
        for label, val, color in [
            ("Total claims",  stats.get("total_claims",0),   "#38BDF8"),
            ("Denied",        stats.get("denied",0),         "#F87171"),
            ("At risk",       stats.get("at_risk",0),        "#FBBF24"),
        ]:
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;padding:4px 0;
                        border-bottom:1px solid #1E293B;font-size:.8rem;'>
              <span style='color:#94A3B8;'>{label}</span>
              <span style='color:{color};font-weight:600;font-family:DM Mono,monospace;'>{val}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E293B;margin:.8rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:.7rem;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;'>AI Stack</div>", unsafe_allow_html=True)
    for name, desc, col in [
        ("Claude API","Anthropic","#38BDF8"),
        ("XGBoost","Risk Scorer","#F59E0B"),
        ("SHAP","Explainability","#A78BFA"),
        ("spaCy","NLP","#34D399"),
        ("FastAPI","Backend","#F87171"),
    ]:
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;padding:3px 0;font-size:.75rem;'>
          <span style='color:{col};font-weight:500;'>{name}</span>
          <span style='color:#475569;'>{desc}</span>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════
def show_dashboard():
    st.markdown("<div style='font-size:1.5rem;font-weight:700;color:#F1F5F9;margin-bottom:.3rem;'>Healthcare Compliance Agent</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:.88rem;color:#64748B;margin-bottom:1.5rem;'>Real-time policy monitoring · AI claim analysis · Autonomous fix generation</div>", unsafe_allow_html=True)

    stats  = api_get("/claims/stats")
    pstats = api_get("/policies/stats")

    # Metric row
    cols = st.columns(5)
    metrics = [
        (str(stats.get("total_claims",0)),   "Total Claims",       "#38BDF8"),
        (str(stats.get("denied",0)),          "Denied",             "#F87171"),
        (f"{stats.get('rejection_rate_pct',0):.1f}%", "Rejection Rate", "#FBBF24"),
        (str(pstats.get("high",0)),           "High-Risk Policies", "#F87171"),
        (f"${stats.get('total_at_risk_usd',0):,.0f}", "Revenue at Risk","#34D399"),
    ]
    for col, (val, lbl, color) in zip(cols, metrics):
        col.markdown(f"""
        <div class='metric-card'>
          <div class='metric-val' style='color:{color};'>{val}</div>
          <div class='metric-lbl'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)

    # Recent activity columns
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='sec-hdr'>Recent High-Risk Claims</div>", unsafe_allow_html=True)
        at_risk = api_get("/claims/at-risk", {"level":"HIGH","limit":5})
        if isinstance(at_risk, list):
            for c in at_risk[:5]:
                bc = color_map(c.get("risk_level","LOW"))
                st.markdown(f"""
                <div class='card' style='border-left:3px solid {bc};'>
                  <div style='display:flex;justify-content:space-between;'>
                    <span style='font-family:DM Mono,monospace;font-size:.8rem;color:#38BDF8;'>{c.get("claim_id")}</span>
                    {badge(c.get("risk_level","LOW"))}
                  </div>
                  <div style='font-size:.75rem;color:#64748B;margin-top:3px;'>
                    {c.get("cpt_code")} · {c.get("payer")} · ${c.get("billed_amount",0):,.2f}
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No high-risk claims found.")

    with c2:
        st.markdown("<div class='sec-hdr'>Recent Policies</div>", unsafe_allow_html=True)
        policies = api_get("/policies/", {"limit":5})
        if isinstance(policies, list):
            for p in policies[:5]:
                bc = color_map(p.get("impact_level","LOW"))
                st.markdown(f"""
                <div class='card' style='border-left:3px solid {bc};'>
                  <div style='display:flex;justify-content:space-between;'>
                    <span style='font-size:.85rem;font-weight:500;color:#E2E8F0;'>{p.get("title","")[:45]}</span>
                    {badge(p.get("impact_level","LOW"))}
                  </div>
                  <div style='font-size:.73rem;color:#64748B;margin-top:3px;'>
                    {p.get("policy_type","")} · {p.get("effective_date","")} · {p.get("issuer","")}
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No policies loaded yet.")

    # Denial breakdown
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-hdr'>Top Denial Reasons</div>", unsafe_allow_html=True)
    reasons = stats.get("denial_reasons", {})
    if reasons:
        import plotly.express as px
        df_r = pd.DataFrame({"Reason": list(reasons.keys()), "Count": list(reasons.values())})
        fig = px.bar(df_r, x="Count", y="Reason", orientation="h",
                     color_discrete_sequence=["#1A56DB"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#94A3B8", margin=dict(l=0,r=0,t=0,b=0), height=200)
        fig.update_xaxes(gridcolor="#1E293B")
        fig.update_yaxes(gridcolor="#1E293B")
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# WATCHER
# ════════════════════════════════════════════════════════════════
def show_watcher():
    st.markdown("<div style='font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;'>Agent 1 — Watcher</div>", unsafe_allow_html=True)

    tab_news, tab_url, tab_upload, tab_text = st.tabs([
        "  Live CMS News  ",
        "  Scan URL  ",
        "  Upload PDF/TXT  ",
        "  Paste Text  ",
    ])

    # ── CMS News feed ─────────────────────────────────────────────
    with tab_news:
        st.markdown("<div class='sec-hdr'>Live CMS Policy News</div>", unsafe_allow_html=True)
        if st.button("Fetch latest news", key="fetch_news"):
            with st.spinner("Fetching CMS news feed..."):
                news = api_get("/agents/watcher/news")
            articles = news.get("news", [])
            if articles:
                for a in articles:
                    st.markdown(f"""
                    <div class='card'>
                      <div style='font-size:.88rem;font-weight:500;color:#E2E8F0;margin-bottom:4px;'>{a.get("title","")}</div>
                      <div style='font-size:.75rem;color:#64748B;margin-bottom:6px;'>{a.get("date","")} · {a.get("source","")}</div>
                      <div style='font-size:.8rem;color:#94A3B8;line-height:1.5;'>{a.get("summary","")}</div>
                      <a href='{a.get("link","")}' target='_blank' style='font-size:.75rem;color:#38BDF8;'>Read full article →</a>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No news fetched yet. Check your internet connection.")

    # ── URL Scan ──────────────────────────────────────────────────
    with tab_url:
        st.markdown("<div class='sec-hdr'>Scan CMS Portal URL</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.82rem;color:#64748B;margin-bottom:.8rem;'>Paste any CMS page URL. Claude will read the page and extract policy changes.</div>", unsafe_allow_html=True)
        url = st.text_input("CMS URL",
            value="https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update",
            label_visibility="collapsed")
        if st.button("Scan URL with Claude AI", key="scan_url"):
            with st.spinner("Fetching page → sending to Claude AI..."):
                result = api_post("/agents/watcher/url", {"url": url})
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Policy extracted successfully!")
                _show_policy_result(result.get("policy", {}))

    # ── File Upload ───────────────────────────────────────────────
    with tab_upload:
        st.markdown("<div class='sec-hdr'>Upload Policy Document</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.82rem;color:#64748B;margin-bottom:.8rem;'>Upload a CMS PDF or TXT policy file. Claude will read and extract compliance data.</div>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf","txt"])
        if uploaded and st.button("Analyse with Claude AI", key="analyse_file"):
            with st.spinner("Reading file → Claude extracting policy..."):
                files = {"file": (uploaded.name, uploaded.read(),
                         "application/pdf" if uploaded.name.endswith(".pdf") else "text/plain")}
                result = api_post("/agents/watcher/upload", files=files)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Policy extracted successfully!")
                _show_policy_result(result.get("policy", {}))

    # ── Paste Text ────────────────────────────────────────────────
    with tab_text:
        st.markdown("<div class='sec-hdr'>Paste Raw Policy Text</div>", unsafe_allow_html=True)
        raw = st.text_area("Paste policy text here", height=200,
                           placeholder="Paste the text of a CMS policy document...")
        if st.button("Extract with Claude AI", key="extract_text") and raw:
            with st.spinner("Claude reading policy text..."):
                result = api_post("/agents/watcher/text", {"text": raw})
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Policy extracted!")
                _show_policy_result(result.get("policy", {}))


def _show_policy_result(policy: dict):
    if not policy:
        return
    impact = policy.get("impact_level","MEDIUM")
    bc = color_map(impact)
    st.markdown(f"""
    <div class='card' style='border-left:3px solid {bc};margin-top:.8rem;'>
      <div style='display:flex;justify-content:space-between;margin-bottom:.5rem;'>
        <span style='font-size:1rem;font-weight:600;color:#E2E8F0;'>{policy.get("title","")}</span>
        {badge(impact)}
      </div>
      <div style='font-size:.78rem;color:#94A3B8;line-height:1.6;margin-bottom:.6rem;'>
        {policy.get("summary","")}
      </div>
      <div style='display:flex;gap:2rem;font-size:.75rem;color:#64748B;'>
        <span>Type: {policy.get("policy_type","")}</span>
        <span>Effective: {policy.get("effective_date","")}</span>
        <span>Deadline: {policy.get("deadline_days",30)} days</span>
        <span style='color:#F87171;'>Impact: ${policy.get("financial_impact_usd",0):,.0f}</span>
      </div>
      <div style='margin-top:.6rem;'>
        {''.join(f"<span style='background:#1E293B;border-radius:4px;padding:2px 8px;font-family:DM Mono,monospace;font-size:.72rem;color:#38BDF8;margin-right:5px;'>{c}</span>" for c in json.loads(policy.get("affected_codes","[]")) if c)}
      </div>
    </div>""", unsafe_allow_html=True)
    with st.expander("View full extracted JSON"):
        st.json(policy)


# ════════════════════════════════════════════════════════════════
# THINKER
# ════════════════════════════════════════════════════════════════
def show_thinker():
    st.markdown("<div style='font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;'>Agent 2 — Thinker</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<div class='sec-hdr'>Select Policy to Scan Against</div>", unsafe_allow_html=True)
        policies = api_get("/policies/")
        if not isinstance(policies, list) or not policies:
            st.warning("No policies found. Run the Watcher first.")
            return

        pol_map = {p["title"]: p for p in policies}
        sel_title = st.selectbox("Policy", list(pol_map.keys()), label_visibility="collapsed")
        sel_pol = pol_map[sel_title]

        impact = sel_pol.get("impact_level","MEDIUM")
        bc = color_map(impact)
        codes = json.loads(sel_pol.get("affected_codes","[]"))
        st.markdown(f"""
        <div class='card' style='border-left:3px solid {bc};'>
          <div style='font-size:.72rem;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.4rem;'>Selected policy</div>
          <div style='font-size:.9rem;font-weight:500;color:#E2E8F0;margin-bottom:.3rem;'>{sel_pol.get("title","")}</div>
          <div style='font-size:.78rem;color:#94A3B8;'>{sel_pol.get("summary","")}</div>
          <div style='margin-top:.5rem;'>
            {''.join(f"<span style='background:#1E293B;border-radius:4px;padding:2px 8px;font-family:DM Mono,monospace;font-size:.72rem;color:#38BDF8;margin-right:5px;'>{c}</span>" for c in codes)}
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='sec-hdr' style='margin-top:1rem;'>Date Filter</div>", unsafe_allow_html=True)
        check_date = st.date_input("Scan claims up to date", value=date.today())
        st.caption(f"Claims with service date ≤ {check_date} will be scanned")

        scan_btn = st.button("Scan & Score with XGBoost + Claude", use_container_width=True)

    with col_r:
        st.markdown("<div class='sec-hdr'>Scan Results</div>", unsafe_allow_html=True)

        if scan_btn:
            with st.spinner("XGBoost scoring · Claude reasoning · Flagging claims..."):
                result = api_post("/agents/thinker/scan", {
                    "policy_id":  sel_pol.get("policy_id"),
                    "check_date": str(check_date),
                })

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["thinker_result"] = result

        res = st.session_state.get("thinker_result")
        if res:
            fc = res.get("flagged_count", 0)
            ts = res.get("total_scanned", 0)
            ta = res.get("total_at_risk", 0)

            m1, m2, m3 = st.columns(3)
            for col, val, lbl, color in [
                (m1, str(ts),      "Scanned",    "#38BDF8"),
                (m2, str(fc),      "Flagged",    "#F87171"),
                (m3, f"${ta:,.0f}","At Risk",    "#34D399"),
            ]:
                col.markdown(f"""
                <div class='metric-card' style='padding:.7rem;'>
                  <div class='metric-val' style='color:{color};font-size:1.4rem;'>{val}</div>
                  <div class='metric-lbl'>{lbl}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:.6rem;'></div>", unsafe_allow_html=True)

            for claim in res.get("flagged_claims", []):
                bc = color_map(claim.get("risk_level","LOW"))
                shap_text = ", ".join(claim.get("shap_explanation",[]))
                st.markdown(f"""
                <div class='card' style='border-left:3px solid {bc};'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:.3rem;'>
                    <span style='font-family:DM Mono,monospace;font-size:.8rem;color:#38BDF8;'>{claim.get("claim_id")}</span>
                    <div style='display:flex;gap:5px;'>
                      {badge(claim.get("risk_level","LOW"))}
                      {badge(claim.get("claim_status","PENDING"))}
                    </div>
                  </div>
                  <div style='font-size:.75rem;color:#64748B;margin-bottom:.3rem;'>
                    {claim.get("cpt_code")} · {claim.get("payer")} · ${claim.get("billed_amount",0):,.2f}
                    · Risk score: <span style='color:{bc};font-family:DM Mono,monospace;'>{claim.get("risk_score",0):.2f}</span>
                  </div>
                  <div style='font-size:.75rem;color:#94A3B8;line-height:1.4;margin-bottom:.3rem;'>
                    {claim.get("claude_reasoning","")}
                  </div>
                  {f"<div style='font-size:.7rem;color:#7C3AED;font-family:DM Mono,monospace;'>SHAP: {shap_text}</div>" if shap_text else ""}
                </div>""", unsafe_allow_html=True)

            if res.get("flagged_claims"):
                df_export = pd.DataFrame(res["flagged_claims"])
                st.download_button(
                    "Download flagged claims CSV",
                    df_export.to_csv(index=False),
                    file_name=f"flagged_{date.today()}.csv",
                    mime="text/csv",
                )
        else:
            st.markdown("""
            <div style='background:#0F172A;border:1px dashed #1E293B;border-radius:10px;
                        padding:2.5rem;text-align:center;color:#334155;'>
              <div style='font-size:.85rem;'>Select a policy and click Scan</div>
            </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# FIXER
# ════════════════════════════════════════════════════════════════
def show_fixer():
    st.markdown("<div style='font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;'>Agent 3 — Fixer</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<div class='sec-hdr'>Select Claim to Fix</div>", unsafe_allow_html=True)
        at_risk = api_get("/claims/at-risk")
        if not isinstance(at_risk, list) or not at_risk:
            st.info("No at-risk claims. Run the Thinker first.")
            return

        claim_labels = [f"{c['claim_id']}  ·  {c['cpt_code']}  ·  {c.get('risk_level','?')}" for c in at_risk]
        sel_label = st.radio("Claims", claim_labels, label_visibility="collapsed")
        sel_claim = at_risk[claim_labels.index(sel_label)]

        bc = color_map(sel_claim.get("risk_level","LOW"))
        st.markdown(f"""
        <div class='card' style='border-left:3px solid {bc};margin-top:.5rem;'>
          <div style='font-size:.72rem;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem;'>Claim details</div>
          <div style='display:grid;grid-template-columns:1fr 1fr;gap:.3rem;font-size:.8rem;'>
            <div style='color:#64748B;'>Claim ID</div><div style='color:#38BDF8;font-family:DM Mono,monospace;'>{sel_claim.get("claim_id")}</div>
            <div style='color:#64748B;'>Patient</div><div style='color:#E2E8F0;'>{sel_claim.get("patient_id")}</div>
            <div style='color:#64748B;'>CPT Code</div><div style='color:#38BDF8;font-family:DM Mono,monospace;'>{sel_claim.get("cpt_code")}</div>
            <div style='color:#64748B;'>Payer</div><div style='color:#E2E8F0;'>{sel_claim.get("payer")}</div>
            <div style='color:#64748B;'>Billed</div><div style='color:#34D399;font-weight:600;'>${sel_claim.get("billed_amount",0):,.2f}</div>
            <div style='color:#64748B;'>Status</div><div style='color:#F87171;'>{sel_claim.get("claim_status","PENDING")}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='sec-hdr' style='margin-top:.8rem;'>Select Policy</div>", unsafe_allow_html=True)
        policies = api_get("/policies/")
        pol_map  = {p["title"]: p for p in (policies if isinstance(policies,list) else [])}
        if not pol_map:
            st.warning("No policies found.")
            return
        sel_pol_title = st.selectbox("Policy", list(pol_map.keys()), label_visibility="collapsed", key="fixer_pol")
        sel_pol = pol_map[sel_pol_title]

        fix_btn = st.button("Generate fix with Claude AI", use_container_width=True)

    with col_r:
        st.markdown("<div class='sec-hdr'>Claude AI — Corrective Action Plan</div>", unsafe_allow_html=True)

        if fix_btn:
            with st.spinner("Claude generating corrective action plan..."):
                result = api_post("/agents/fixer/fix", {
                    "claim_id":  sel_claim.get("claim_id"),
                    "policy_id": sel_pol.get("policy_id"),
                })

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["fixer_result"] = result

        res = st.session_state.get("fixer_result")
        if res:
            priority = res.get("priority","HIGH")
            pc = {"URGENT":"#F87171","HIGH":"#FBBF24","MEDIUM":"#34D399"}.get(priority,"#94A3B8")
            st.markdown(f"""
            <div style='background:#0A2818;border:1px solid #166534;border-radius:8px;
                        padding:.6rem 1rem;font-size:.78rem;color:#86EFAC;
                        font-family:DM Mono,monospace;margin-bottom:.8rem;
                        display:flex;justify-content:space-between;'>
              <span>✓ Claude AI — corrective action plan generated</span>
              <span style='color:{pc};'>PRIORITY: {priority}</span>
            </div>""", unsafe_allow_html=True)

            fix_text = res.get("fix_plan","")
            steps = [l.strip() for l in fix_text.split("\n") if l.strip() and l.strip()[0].isdigit()]

            steps_html = "".join([f"""
            <div style='display:flex;gap:10px;align-items:flex-start;
                        padding:.55rem 0;border-bottom:1px solid #0A2818;'>
              <span style='min-width:22px;height:22px;background:#166534;border-radius:50%;
                           display:flex;align-items:center;justify-content:center;
                           font-size:.68rem;font-weight:700;color:#86EFAC;
                           font-family:DM Mono,monospace;flex-shrink:0;'>{i+1}</span>
              <span style='font-size:.82rem;color:#BBF7D0;line-height:1.5;'>{s[s.index('.')+1:].strip() if '.' in s[:3] else s}</span>
            </div>""" for i, s in enumerate(steps)] or f"<div style='color:#BBF7D0;font-size:.82rem;'>{fix_text}</div>")

            st.markdown(f"""
            <div style='background:#071A10;border:1px solid #166534;border-radius:12px;
                        padding:1rem 1.1rem;'>{steps_html}</div>""",
                unsafe_allow_html=True)

            # Outcome cards
            st.markdown("<div style='height:.7rem;'></div>", unsafe_allow_html=True)
            oc1, oc2, oc3 = st.columns(3)
            for col_o, val, lbl, color in [
                (oc1, f"{sel_pol.get('deadline_days',30)} days", "Fix deadline",     "#FBBF24"),
                (oc2, "Prevented",                               "Claim rejection",  "#34D399"),
                (oc3, f"${sel_claim.get('billed_amount',0):,.0f}","Revenue saved",   "#34D399"),
            ]:
                col_o.markdown(f"""
                <div class='metric-card' style='padding:.7rem;'>
                  <div class='metric-val' style='color:{color};font-size:1.2rem;'>{val}</div>
                  <div class='metric-lbl'>{lbl}</div>
                </div>""", unsafe_allow_html=True)

            # Download fix plan
            st.download_button(
                "Download fix plan TXT",
                fix_text,
                file_name=f"fix_{res.get('claim_id','claim')}.txt",
                mime="text/plain",
            )
        else:
            st.markdown("""
            <div style='background:#0F172A;border:1px dashed #1E293B;border-radius:10px;
                        padding:2.5rem;text-align:center;color:#334155;'>
              <div style='font-size:.85rem;'>Select a claim and click Generate Fix</div>
            </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# DATA MANAGEMENT (CRUD UI)
# ════════════════════════════════════════════════════════════════
def show_data_mgmt():
    st.markdown("<div style='font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;'>Data Management</div>", unsafe_allow_html=True)

    tab_claims, tab_patients, tab_policies, tab_import = st.tabs([
        "  Claims  ","  Patients  ","  Policies  ","  Bulk Import  "
    ])

    # ── Claims CRUD ───────────────────────────────────────────────
    with tab_claims:
        c_left, c_right = st.columns([1.5, 1])
        with c_left:
            st.markdown("<div class='sec-hdr'>All Claims</div>", unsafe_allow_html=True)
            filters = st.columns(3)
            status_f  = filters[0].selectbox("Status",["","APPROVED","DENIED","PENDING"],label_visibility="visible")
            risk_f    = filters[1].selectbox("Risk",["","HIGH","MEDIUM","LOW"],label_visibility="visible")
            payer_f   = filters[2].text_input("Payer",label_visibility="visible")
            claims = api_get("/claims/", {
                "status_filter": status_f or None,
                "risk_level": risk_f or None,
                "payer": payer_f or None,
                "limit": 50,
            })
            if isinstance(claims, list) and claims:
                df = pd.DataFrame(claims)[["claim_id","patient_id","cpt_code","payer",
                                           "billed_amount","claim_status","risk_level"]]
                st.dataframe(df, use_container_width=True, height=350)
            else:
                st.info("No claims match the filter.")

        with c_right:
            st.markdown("<div class='sec-hdr'>Add New Claim</div>", unsafe_allow_html=True)
            with st.form("add_claim"):
                claim_id  = st.text_input("Claim ID")
                patient_id= st.text_input("Patient ID")
                cpt       = st.text_input("CPT Code")
                icd       = st.text_input("ICD-10 Code")
                payer     = st.selectbox("Payer",["Medicare Part B","Medicare Part A",
                              "Medicaid","Aetna","Cigna","Humana","Blue Cross Blue Shield"])
                billed    = st.number_input("Billed Amount ($)", min_value=0.0)
                svc_date  = st.date_input("Service Date")
                submitted = st.form_submit_button("Add Claim")
                if submitted:
                    result = api_post("/claims/", {
                        "claim_id": claim_id, "patient_id": patient_id,
                        "cpt_code": cpt, "icd10_code": icd,
                        "payer": payer, "billed_amount": billed,
                        "service_date": str(svc_date),
                    })
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success(f"Claim {claim_id} added!")

            st.markdown("<div class='sec-hdr' style='margin-top:1rem;'>Delete Claim</div>", unsafe_allow_html=True)
            del_id = st.text_input("Claim ID to delete", key="del_claim")
            if st.button("Delete", key="del_claim_btn"):
                r = api_delete(f"/claims/{del_id}")
                st.success(r.get("deleted","Done")) if "deleted" in r else st.error(r.get("detail"))

    # ── Patients CRUD ─────────────────────────────────────────────
    with tab_patients:
        p_left, p_right = st.columns([1.5,1])
        with p_left:
            st.markdown("<div class='sec-hdr'>All Patients</div>", unsafe_allow_html=True)
            search = st.text_input("Search by name", key="pat_search")
            if search:
                patients = api_get("/patients/search", {"name": search})
            else:
                patients = api_get("/patients/", {"limit": 50})
            if isinstance(patients, list) and patients:
                df = pd.DataFrame(patients)[["patient_id","name","dob","payer","facility","provider_name"]]
                st.dataframe(df, use_container_width=True, height=350)
            else:
                st.info("No patients found.")

        with p_right:
            st.markdown("<div class='sec-hdr'>Add New Patient</div>", unsafe_allow_html=True)
            with st.form("add_patient"):
                pid   = st.text_input("Patient ID")
                name  = st.text_input("Full Name")
                dob   = st.date_input("Date of Birth")
                gender= st.selectbox("Gender",["M","F","Other"])
                prov  = st.text_input("Provider Name")
                fac   = st.text_input("Facility")
                pay   = st.selectbox("Payer",["Medicare Part B","Medicare Part A",
                          "Medicaid","Aetna","Cigna","Humana","Blue Cross Blue Shield"])
                submitted = st.form_submit_button("Add Patient")
                if submitted:
                    r = api_post("/patients/", {
                        "patient_id": pid,"name": name,"dob": str(dob),
                        "gender": gender,"provider_name": prov,
                        "facility": fac,"payer": pay,
                    })
                    st.success(f"Patient {pid} added!") if "error" not in r else st.error(r["error"])

    # ── Policies CRUD ─────────────────────────────────────────────
    with tab_policies:
        policies = api_get("/policies/")
        if isinstance(policies, list) and policies:
            df_p = pd.DataFrame(policies)[["policy_id","title","policy_type",
                                           "impact_level","effective_date","deadline_days"]]
            st.dataframe(df_p, use_container_width=True, height=300)
        else:
            st.info("No policies. Use the Watcher to add policies.")

        st.markdown("<div class='sec-hdr' style='margin-top:1rem;'>Delete Policy</div>", unsafe_allow_html=True)
        del_pol = st.text_input("Policy ID to delete", key="del_pol")
        if st.button("Delete Policy", key="del_pol_btn"):
            r = api_delete(f"/policies/{del_pol}")
            st.success(str(r)) if "error" not in r else st.error(r["error"])

    # ── Bulk Import ───────────────────────────────────────────────
    with tab_import:
        st.markdown("<div class='sec-hdr'>Bulk Import Claims from Excel/CSV</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.82rem;color:#64748B;margin-bottom:.8rem;'>Upload your cleaned dataset. All rows will be imported to the database.</div>", unsafe_allow_html=True)

        up = st.file_uploader("Upload Excel or CSV", type=["xlsx","csv"], key="bulk_up")
        if up and st.button("Import to Database", key="bulk_import"):
            with st.spinner("Reading file and importing..."):
                if up.name.endswith(".csv"):
                    df_imp = pd.read_csv(up)
                else:
                    df_imp = pd.read_excel(up)

                required = ["claim_id","patient_id"]
                missing  = [c for c in required if c not in df_imp.columns]
                if missing:
                    st.error(f"Missing required columns: {missing}")
                else:
                    records = df_imp.fillna("").to_dict("records")
                    clean   = []
                    for r in records:
                        clean.append({
                            "claim_id":               str(r.get("claim_id","")),
                            "patient_id":             str(r.get("patient_id","")),
                            "cpt_code":               str(r.get("cpt_code","")),
                            "icd10_code":             str(r.get("icd10_code","")),
                            "payer":                  str(r.get("payer","")),
                            "billed_amount":          float(r.get("billed_amount",0) or 0),
                            "claim_status":           str(r.get("claim_status","PENDING")),
                            "claim_denial_flag":      int(r.get("claim_denial_flag",0) or 0),
                            "prior_auth_required":    str(r.get("prior_auth_required","N")),
                            "documentation_required": str(r.get("documentation_required","N")),
                            "policy_impact_level":    str(r.get("policy_impact_level","LOW")),
                            "provider_compliance_score": float(r.get("provider_compliance_score",80) or 80),
                            "service_date":           str(r.get("service_date","")),
                            "denial_reason":          str(r.get("denial_reason","") or ""),
                        })
                    result = api_post("/claims/bulk", clean)
                    st.success(f"Imported: {result.get('added',0)} · Skipped: {result.get('skipped',0)}")


# ════════════════════════════════════════════════════════════════
# AUDIT LOG
# ════════════════════════════════════════════════════════════════
def show_audit():
    st.markdown("<div style='font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;'>Audit Log</div>", unsafe_allow_html=True)

    agent_filter = st.selectbox("Filter by agent",["All","Watcher","Thinker","Fixer","API"])
    logs = api_get("/agents/logs", {"agent": agent_filter if agent_filter != "All" else None, "limit": 100})

    if isinstance(logs, list) and logs:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs[["timestamp","agent","action","entity_id","details"]],
                     use_container_width=True, height=500)
        st.download_button("Download log CSV", df_logs.to_csv(index=False),
                           "audit_log.csv","text/csv")
    else:
        st.info("No audit log entries yet.")


# ── Router ────────────────────────────────────────────────────────
if   page == "Dashboard":        show_dashboard()
elif page == "Watcher":          show_watcher()
elif page == "Thinker":          show_thinker()
elif page == "Fixer":            show_fixer()
elif page == "Data Management":  show_data_mgmt()
elif page == "Audit Log":        show_audit()
