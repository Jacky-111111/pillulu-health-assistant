"""Case records CRUD for body-map visualization."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CaseRecord, User
from app.routers.auth import get_current_user
from app.schemas import CaseRecordCreate, CaseRecordUpdate, CaseRecordResponse

router = APIRouter(prefix="/api", tags=["cases"])


@router.get("/cases", response_model=list[CaseRecordResponse])
def list_cases(
    body_part: str | None = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(CaseRecord).filter(CaseRecord.user_id == user.id)
    if body_part:
        query = query.filter(CaseRecord.body_part == body_part)
    records = query.order_by(CaseRecord.occurred_on.desc().nullslast(), CaseRecord.created_at.desc()).all()
    return [CaseRecordResponse.model_validate(r) for r in records]


@router.post("/cases", response_model=CaseRecordResponse)
def create_case(
    body: CaseRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = CaseRecord(
        user_id=user.id,
        title=body.title,
        diagnosis=body.diagnosis,
        body_part=body.body_part.strip().lower(),
        severity=body.severity,
        status=body.status,
        occurred_on=body.occurred_on,
        resolved_on=body.resolved_on,
        notes=body.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return CaseRecordResponse.model_validate(record)


@router.put("/cases/{case_id}", response_model=CaseRecordResponse)
def update_case(
    case_id: int,
    body: CaseRecordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(CaseRecord).filter(CaseRecord.id == case_id, CaseRecord.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Case record not found")

    data = body.model_dump(exclude_unset=True)
    if "body_part" in data and data["body_part"]:
        data["body_part"] = data["body_part"].strip().lower()
    for key, value in data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return CaseRecordResponse.model_validate(record)


@router.delete("/cases/{case_id}")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(CaseRecord).filter(CaseRecord.id == case_id, CaseRecord.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Case record not found")

    db.delete(record)
    db.commit()
    return {"ok": True}
