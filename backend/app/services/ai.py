"""OpenAI Chat Completions for medication Q&A with safety prompts."""
from openai import OpenAI

from app.config import OPENAI_API_KEY

SYSTEM_PROMPT = """You are an educational health assistant. Your role is to provide general, educational information about medications only. You must NEVER:
- Provide medical advice or prescribe
- Claim certainty about dosages or treatments
- Replace consultation with a licensed clinician or pharmacist

When discussing medications:
- Frame all information as educational only
- If asked about dosage, provide general typical adult dosage ranges only when confident from reliable sources; otherwise recommend consulting a doctor or pharmacist
- Always mention that individual factors (age, kidney function, pregnancy, other medications, allergies) matter and require professional assessment
- Encourage the user to consult their doctor or pharmacist for personalized advice

Respond in the same language as the user's question. Be concise and helpful while staying within these boundaries."""

DISCLAIMER = "This information is for educational purposes only and does not constitute medical advice. Please consult a doctor or pharmacist for personalized guidance."


def ask_ai(question: str, context_med_name: str | None = None) -> tuple[str, str]:
    """
    Call OpenAI Chat Completions. Returns (answer, disclaimer).
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
    answer = response.choices[0].message.content or ""
    return answer.strip(), DISCLAIMER
