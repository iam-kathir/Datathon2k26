"""
FastAPI entry point.
Run with: uvicorn api.main:app --reload --port 8000
Docs at:  http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import init_db
from api.routes import policies, patients, claims, agents

app = FastAPI(
    title="Healthcare Compliance Agent API",
    description=(
        "CRUD API for the Healthcare Compliance Agent.\n"
        "Manages policies, patients, claims and triggers AI agents."
    ),
    version="2.0.0",
)

# Allow Streamlit to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    print("Database initialised.")


@app.get("/")
def root():
    return {
        "name":    "Healthcare Compliance Agent API",
        "version": "2.0.0",
        "docs":    "/docs",
        "routes": {
            "policies": "/policies",
            "patients": "/patients",
            "claims":   "/claims",
            "agents":   "/agents",
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(policies.router, prefix="/policies", tags=["Policies"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(claims.router,   prefix="/claims",   tags=["Claims"])
app.include_router(agents.router,   prefix="/agents",   tags=["Agents"])
