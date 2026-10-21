import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

app = FastAPI(
    title="Skill Mind AI API",
    description="AI-powered learning assistant API",
    version="1.0.0",
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

@app.get("/")
def home():
    return {
        "status": "success",
        "app": "Skill Mind AI",
        "message": "Skill Mind API is running!"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="AI configuration is missing."
        )

    try:
        client = genai.Client(api_key=api_key)

        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        response = client.models.generate_content(
            model=model,
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are Skill Mind AI, a helpful learning assistant. "
                    "Explain concepts clearly and respectfully. "
                    "When appropriate, answer in the user's language."
                )
            )
        )

        answer = response.text

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="The AI returned an empty response."
            )

        return {
            "app": "Skill Mind AI",
            "reply": answer
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI request failed. Check the server configuration and logs."
        )
