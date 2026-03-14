"""
Patient CRUD routes.
GET  /patients/        — list all
GET  /patients/{id}    — get one
POST /patients/        — create
PUT  /patients/{id}    — update
DELETE /patients/{id}  — delete
GET  /patients/search?name=... — search by name
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db, Patient, AuditLog
from api.models import PatientCreate, PatientOut

router = APIRouter()


def _log(db, action, eid, details):
    db.add(AuditLog(action=action, agent="API", entity_id=str(eid), details=details))
    db.commit()


@router.get("/", response_model=List[PatientOut])
def list_patients(
    payer: Optional[str] = None,
    facility: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Patient)
    if payer:
        q = q.filter(Patient.payer == payer)
    if facility:
        q = q.filter(Patient.facility == facility)
    return q.offset(skip).limit(limit).all()


@router.get("/count")
def count_patients(db: Session = Depends(get_db)):
    return {"total_patients": db.query(Patient).count()}


@router.get("/search", response_model=List[PatientOut])
def search_patients(name: str, db: Session = Depends(get_db)):
    return db.query(Patient).filter(Patient.name.ilike(f"%{name}%")).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return p


@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.patient_id == data.patient_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Patient {data.patient_id} already exists")
    p = Patient(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    _log(db, "PATIENT_CREATED", p.patient_id, f"Added: {p.name}")
    return p


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: str, data: dict, db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    for k, v in data.items():
        if hasattr(p, k):
            setattr(p, k, v)
    db.commit()
    db.refresh(p)
    _log(db, "PATIENT_UPDATED", patient_id, str(data))
    return p


@router.delete("/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    db.delete(p)
    db.commit()
    _log(db, "PATIENT_DELETED", patient_id, f"Deleted: {p.name}")
    return {"deleted": patient_id}
