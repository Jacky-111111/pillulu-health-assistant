"""AI Q&A about medications."""
from fastapi import APIRouter, HTTPException

from app.schemas import AIAskRequest, AIAskResponse
from app.services.ai import ask_ai

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/ask", response_model=AIAskResponse)
async def ai_ask(req: AIAskRequest):
    """Ask AI about medication. Returns answer with disclaimer and suggested meds."""
    try:
        answer, disclaimer, suggested_medications = ask_ai(req.question, req.context_med_name)
        return AIAskResponse(answer=answer, disclaimer=disclaimer, suggested_medications=suggested_medications)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
