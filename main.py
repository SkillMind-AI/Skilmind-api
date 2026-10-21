import os
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)

logger = logging.getLogger("skill_mind_ai")

app = FastAPI(
    title="Skill Mind AI API",
    description="AI-powered learning platform backend",
    version="1.0.1",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@app.get("/")
def home():
    return {
        "status": "success",
        "app": "Skill Mind AI",
        "message": "Skill Mind API is running!",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is missing.")
        raise HTTPException(
            status_code=500,
            detail="AI configuration is missing on the server.",
        )

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are Skill Mind AI, a helpful learning assistant. "
                    "Explain concepts clearly and respectfully. "
                    "Answer in the user's language whenever appropriate."
                )
            ),
        )

        answer = response.text

        if not answer:
            logger.error("Gemini returned an empty response.")
            raise HTTPException(
                status_code=502,
                detail="The AI returned an empty response.",
            )

        logger.info("Chat request completed successfully.")

        return {
            "app": "Skill Mind AI",
            "reply": answer,
        }

    except HTTPException:
        raise

    except Exception as exc:
        # Log the exception type and message for diagnosis.
        # Never log the API key.
        logger.exception(
            "Gemini request failed. Error type: %s; message: %s",
            type(exc).__name__,
            str(exc),
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "AI request failed. Check Render logs "
                "for the underlying error."
            ),
        )
