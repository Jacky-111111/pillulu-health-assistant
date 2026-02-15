"""OpenAI Chat Completions for medication Q&A with safety prompts."""
import json
import re

from openai import OpenAI

from app.config import OPENAI_API_KEY

SYSTEM_PROMPT = """You are Pillulu, an AI-powered health assistant. Your role is to provide general, educational information about medications only. You must NEVER:
- Provide medical advice or prescribe
- Claim certainty about dosages or treatments
- Replace consultation with a licensed clinician or pharmacist

When discussing medications:
- Frame all information as educational only
- When the user asks about symptoms (e.g. sore throat, headache, fever), suggest SPECIFIC medication names (generic or common brand names) that are commonly used for that symptom—e.g. acetaminophen, ibuprofen, throat lozenges (Cepacol, Chloraseptic), etc. This is educational information, not a prescription.
- If asked about dosage, provide general typical adult dosage ranges only when confident from reliable sources; otherwise recommend consulting a doctor or pharmacist
- Always mention that individual factors (age, kidney function, pregnancy, other medications, allergies) matter and require professional assessment
- Encourage the user to consult their doctor or pharmacist for personalized advice

Respond in the same language as the user's question. Be concise and helpful while staying within these boundaries.

You must respond with valid JSON in this exact format:
{"answer": "your full answer text here", "suggested_medications": ["med1", "med2", ...]}
- "answer": Your complete response including disclaimers
- "suggested_medications": List of specific medication names (generic or brand) you mentioned, for the user to add to their pillbox. Use 2-6 items. Empty array [] if none apply."""

DISCLAIMER = "This information is for educational purposes only and does not constitute medical advice. Please consult a doctor or pharmacist for personalized guidance."


def _parse_ai_response(raw: str) -> tuple[str, list[str]]:
    """Parse AI response. Expects JSON with answer and suggested_medications."""
    raw = raw.strip()
    # Try to extract JSON (model might wrap in markdown code block)
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if json_match:
        try:
            data = json.loads(json_match.group())
            answer = data.get("answer", raw)
            meds = data.get("suggested_medications", [])
            if isinstance(meds, list):
                meds = [str(m).strip() for m in meds if m]
            return answer.strip(), meds
        except json.JSONDecodeError:
            pass
    return raw, []


def ask_ai(question: str, context_med_name: str | None = None) -> tuple[str, str, list[str]]:
    """
    Call OpenAI Chat Completions. Returns (answer, disclaimer, suggested_medications).
    Raises Exception on API errors.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    user_content = question
    if context_med_name:
        user_content = f"Regarding medication: {context_med_name}\n\nUser question: {question}"

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=800,
    )
    raw = response.choices[0].message.content or ""
    answer, suggested_medications = _parse_ai_response(raw)
    return answer, DISCLAIMER, suggested_medications
