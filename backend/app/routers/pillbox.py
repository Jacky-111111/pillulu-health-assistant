"""Pillbox CRUD: meds and schedules."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Med, Schedule, User
from app.routers.auth import get_current_user
from app.schemas import (
    MedCreate,
    MedUpdate,
    MedResponse,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleSchema,
    UserEmailUpdate,
)

router = APIRouter(prefix="/api", tags=["pillbox"])


# --- User / Email (for reminder notifications, requires auth) ---
@router.get("/user/email")
def get_user_email(db: Session = Depends(get_db)):
    """Get stored user email. Returns first auth user's email (legacy)."""
    user = db.query(User).filter(User.password_hash.isnot(None)).first()
    return {"email": user.email if user else ""}


@router.put("/user/email")
def set_user_email(body: UserEmailUpdate, db: Session = Depends(get_db)):
    """Set user email for reminders. Creates/updates first auth user (legacy)."""
    from app.services.auth import hash_password
    user = db.query(User).filter(User.password_hash.isnot(None)).first()
    if user:
        user.email = body.email
    else:
        user = User(email=body.email, password_hash=hash_password("changeme"))
        db.add(user)
    db.commit()
    db.refresh(user)
    return {"email": user.email}


# --- Meds CRUD ---
def med_to_response(med: Med) -> MedResponse:
    return MedResponse(
        id=med.id,
        name=med.name,
        purpose=med.purpose,
        dosage_notes=med.dosage_notes,
        adult_dosage_guidance=med.adult_dosage_guidance,
        stock_count=med.stock_count,
        low_stock_threshold=med.low_stock_threshold,
        created_at=med.created_at,
        schedules=[ScheduleSchema.model_validate(s) for s in med.schedules],
    )


@router.post("/pillbox/meds", response_model=MedResponse)
def create_med(body: MedCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = Med(
        user_id=user.id,
        name=body.name,
        purpose=body.purpose,
        dosage_notes=body.dosage_notes,
        stock_count=body.stock_count,
        low_stock_threshold=body.low_stock_threshold,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med_to_response(med)


@router.get("/pillbox/meds", response_model=list[MedResponse])
def list_meds(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meds = db.query(Med).filter(Med.user_id == user.id).order_by(Med.created_at.desc()).all()
    return [med_to_response(m) for m in meds]


@router.get("/pillbox/meds/{med_id}", response_model=MedResponse)
def get_med(med_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = db.query(Med).filter(Med.id == med_id, Med.user_id == user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    return med_to_response(med)


@router.put("/pillbox/meds/{med_id}", response_model=MedResponse)
def update_med(med_id: int, body: MedUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = db.query(Med).filter(Med.id == med_id, Med.user_id == user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(med, k, v)
    db.commit()
    db.refresh(med)
    return med_to_response(med)


@router.delete("/pillbox/meds/{med_id}")
def delete_med(med_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = db.query(Med).filter(Med.id == med_id, Med.user_id == user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    db.delete(med)
    db.commit()
    return {"ok": True}


# --- Schedules CRUD ---
@router.post("/pillbox/meds/{med_id}/schedules", response_model=ScheduleSchema)
def create_schedule(med_id: int, body: ScheduleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = db.query(Med).filter(Med.id == med_id, Med.user_id == user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    s = Schedule(
        med_id=med_id,
        time_of_day=body.time_of_day,
        timezone=body.timezone,
        days_of_week=body.days_of_week,
        enabled=body.enabled,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ScheduleSchema.model_validate(s)


@router.get("/pillbox/meds/{med_id}/schedules", response_model=list[ScheduleSchema])
def list_schedules(med_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    med = db.query(Med).filter(Med.id == med_id, Med.user_id == user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    return [ScheduleSchema.model_validate(s) for s in med.schedules]


@router.put("/schedules/{schedule_id}", response_model=ScheduleSchema)
def update_schedule(schedule_id: int, body: ScheduleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not s or s.med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return ScheduleSchema.model_validate(s)


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not s or s.med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(s)
    db.commit()
    return {"ok": True}
