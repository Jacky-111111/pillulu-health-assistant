"""AI Q&A about medications."""
from datetime import date
import re

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, CaseRecord
from app.schemas import AIAskRequest, AIAskResponse, AIRelatedCase
from app.services.ai import ask_ai
from app.services.auth import decode_token

router = APIRouter(prefix="/api/ai", tags=["ai"])
ALLOWED_BODY_PARTS = {"head", "chest", "abdomen", "left_arm", "right_arm", "left_leg", "right_leg"}


def _is_history_query(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    # English + simple Chinese cues for "past case / history" style questions
    patterns = [
        r"\bpast\b.*\b(case|cases|history|record|records)\b",
        r"\b(case|cases|history|record|records)\b",
        r"\bmy\b.*\b(case|history|records)\b",
        r"\bwhat\b.*\b(case|history|records)\b",
        r"病史",
        r"往期病例",
        r"病例",
        r"历史记录",
    ]
    return any(re.search(p, q) for p in patterns)


def _history_answer(case_records: list[CaseRecord]) -> str:
    if not case_records:
        return (
            "I don't see any past cases in your current history yet. "
            "You can add one in Past Cases and I can use it in future medication discussions."
        )
    lines = ["Based on your Past Cases, here is what I found:"]
    for idx, r in enumerate(case_records[:8], start=1):
        occurred = r.occurred_on.isoformat() if r.occurred_on else "date not set"
        diagnosis = f", diagnosis: {r.diagnosis}" if r.diagnosis else ""
        lines.append(
            f"{idx}. {r.title} ({r.body_part}, severity {r.severity}, status: {r.status}, {occurred}{diagnosis})"
        )
    if len(case_records) > 8:
        lines.append(f"...and {len(case_records) - 8} more record(s).")
    lines.append("If you want, I can explain medication considerations for any specific case above.")
    return "\n".join(lines)


def _try_get_user(
    authorization: str | None,
    db: Session,
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.post("/ask", response_model=AIAskResponse)
async def ai_ask(
    req: AIAskRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """Ask AI about medication. Returns answer with disclaimer and suggested meds."""
    try:
        user = _try_get_user(authorization, db)
        case_records: list[CaseRecord] = []
        if user:
            case_records = (
                db.query(CaseRecord)
                .filter(CaseRecord.user_id == user.id)
                .order_by(CaseRecord.occurred_on.desc().nullslast(), CaseRecord.created_at.desc())
                .limit(40)
                .all()
            )

        if _is_history_query(req.question):
            answer = _history_answer(case_records)
            related_cases = [
                AIRelatedCase(
                    id=record.id,
                    title=record.title,
                    body_part=record.body_part,
                    status=record.status,
                    severity=record.severity,
                    occurred_on=record.occurred_on,
                )
                for record in case_records[:8]
            ]
            return AIAskResponse(
                answer=answer,
                disclaimer="This summary is based on your stored in-app case history and is for educational purposes only.",
                suggested_medications=[],
                related_cases=related_cases,
                history_context_used=bool(case_records),
                auto_case_created=False,
                auto_case=None,
            )

        history_for_ai = [
            {
                "id": record.id,
                "title": record.title,
                "diagnosis": record.diagnosis,
                "body_part": record.body_part,
                "severity": record.severity,
                "status": record.status,
                "occurred_on": record.occurred_on.isoformat() if record.occurred_on else None,
                "notes": record.notes,
            }
            for record in case_records
        ]
        answer, disclaimer, suggested_medications, related_case_ids, suggested_case_record = ask_ai(
            req.question,
            req.context_med_name,
            history_for_ai,
        )

        records_by_id = {record.id: record for record in case_records}
        related_cases: list[AIRelatedCase] = []
        for case_id in related_case_ids:
            record = records_by_id.get(case_id)
            if not record:
                continue
            related_cases.append(
                AIRelatedCase(
                    id=record.id,
                    title=record.title,
                    body_part=record.body_part,
                    status=record.status,
                    severity=record.severity,
                    occurred_on=record.occurred_on,
                )
            )

        auto_case_created = False
        auto_case = None
        if user and isinstance(suggested_case_record, dict):
            should_add = bool(suggested_case_record.get("should_add"))
            title = (str(suggested_case_record.get("title") or "")).strip()
            diagnosis = (str(suggested_case_record.get("diagnosis") or "")).strip() or None
            body_part = (str(suggested_case_record.get("body_part") or "")).strip().lower()
            severity_raw = suggested_case_record.get("severity", 3)
            status = (str(suggested_case_record.get("status") or "active")).strip().lower()
            notes = (str(suggested_case_record.get("notes") or "")).strip() or None
            try:
                severity = int(severity_raw)
            except (TypeError, ValueError):
                severity = 3
            severity = max(1, min(10, severity))
            if status not in {"active", "resolved", "chronic"}:
                status = "active"

            if should_add and title and body_part in ALLOWED_BODY_PARTS:
                existing = (
                    db.query(CaseRecord)
                    .filter(
                        CaseRecord.user_id == user.id,
                        CaseRecord.title == title,
                        CaseRecord.body_part == body_part,
                        CaseRecord.occurred_on == date.today(),
                    )
                    .first()
                )
                record = existing
                if not record:
                    record = CaseRecord(
                        user_id=user.id,
                        title=title,
                        diagnosis=diagnosis,
                        body_part=body_part,
                        severity=severity,
                        status=status,
                        occurred_on=date.today(),
                        notes=notes,
                    )
                    db.add(record)
                    db.commit()
                    db.refresh(record)
                    auto_case_created = True

                if record:
                    auto_case = AIRelatedCase(
                        id=record.id,
                        title=record.title,
                        body_part=record.body_part,
                        status=record.status,
                        severity=record.severity,
                        occurred_on=record.occurred_on,
                    )

        return AIAskResponse(
            answer=answer,
            disclaimer=disclaimer,
            suggested_medications=suggested_medications,
            related_cases=related_cases,
            history_context_used=bool(case_records),
            auto_case_created=auto_case_created,
            auto_case=auto_case,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
