# Healthcare Compliance Agent
**Datathon 2K26 · CIT Coimbatore · Round 2**

Autonomous 3-agent AI system for US healthcare reimbursement compliance.

---

## Tech Stack
| Layer | Tool |
|-------|------|
| LLM reasoning | Claude Sonnet (Anthropic) |
| Risk scoring | XGBoost + SHAP |
| Text extraction | pdfplumber + spaCy |
| Web scraping | requests + BeautifulSoup |
| Backend API | FastAPI + SQLite |
| Frontend | Streamlit |

---

## First-Time Setup (Run on ALL 3 laptops)

### 1. Clone the repo
```bash
git clone https://github.com/yourteam/healthcare-compliance-agent.git
cd healthcare-compliance-agent
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install packages
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Create .env file
Copy `.env.example` to `.env` and fill in your API keys:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 5. Generate & seed dataset
```bash
python data/generate_dataset.py   # creates 5000+ row dataset
python data/seed_db.py            # imports into SQLite
```

### 6. Train the ML model
```bash
python ml/train_model.py
```

---

## Daily Running Order

**Terminal 1 — API backend:**
```bash
venv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 — Streamlit frontend:**
```bash
venv\Scripts\activate
streamlit run app.py
```

- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

---

## Project Structure
```
healthcare-compliance-agent/
├── app.py                    ← Streamlit frontend
├── requirements.txt
├── .env                      ← API keys (never commit)
├── api/
│   ├── main.py               ← FastAPI entry point
│   ├── database.py           ← SQLite models
│   ├── models.py             ← Pydantic schemas
│   └── routes/
│       ├── policies.py       ← Policy CRUD
│       ├── claims.py         ← Claims CRUD
│       ├── patients.py       ← Patients CRUD
│       └── agents.py         ← Agent trigger endpoints
├── agents/
│   ├── watcher.py            ← Agent 1: Claude NLP
│   ├── thinker.py            ← Agent 2: XGBoost + Claude
│   └── fixer.py              ← Agent 3: Claude fix plan
├── ml/
│   ├── train_model.py        ← Train XGBoost
│   └── predict.py            ← Risk prediction
├── data/
│   ├── generate_dataset.py   ← Synthetic data generator
│   └── seed_db.py            ← Import Excel → SQLite
└── utils/
    ├── cms_scraper.py        ← CMS news + page fetch
    └── pdf_reader.py         ← PDF/TXT extraction
```

---

## Team Split
| Person | Owns |
|--------|------|
| Person 1 | agents/watcher.py, utils/, api/routes/policies.py |
| Person 2 | agents/thinker.py, ml/, api/routes/claims.py |
| Person 3 | agents/fixer.py, app.py, api/main.py, api/database.py |

---

## Git Workflow
```bash
git pull origin main          # always pull first
# ... make your changes ...
git add agents/watcher.py     # add only your files
git commit -m "clear message"
git push origin main
```
