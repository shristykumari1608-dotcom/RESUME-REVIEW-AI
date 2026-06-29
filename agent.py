# agent.py
# Resume Review Agent using Google ADK (v2.x) and Gemini API.
# Also provides a Gemini Vision OCR function for camera-captured resumes.
#
# ROOT CAUSE OF BUG (now fixed):
#   InMemorySessionService.create_session() is an async coroutine in ADK 2.x.
#   Calling it without `await` returned a coroutine object, not a Session,
#   so session.id raised: 'coroutine' object has no attribute 'id'.
#
# FIX:
#   ADK 2.x ships synchronous companions for every async method:
#       create_session()  →  create_session_sync()
#       get_session()     →  get_session_sync()
#       delete_session()  →  delete_session_sync()
#   We now use create_session_sync() so no asyncio wrangling is needed
#   and the code stays compatible with Streamlit's synchronous runtime.

import os
import base64

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from google import genai
from dotenv import load_dotenv

# Load GOOGLE_API_KEY from the .env file
load_dotenv()


# ---------------------------------------------------------------------------
# Helper – validate API key early and return a configured genai client
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Return the API key or raise a clear ValueError."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Open the .env file and add:  GOOGLE_API_KEY=your_key_here"
        )
    return key


# ---------------------------------------------------------------------------
# Vision OCR – Extract Resume Text from a Camera Photo
# ---------------------------------------------------------------------------

def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Uses Gemini 2.0 Flash (vision) to OCR a resume photo.

    Args:
        image_bytes: Raw bytes of the captured image.
        mime_type:   MIME type, default 'image/jpeg'.

    Returns:
        Plain-text content extracted from the resume image.
    """
    api_key = _get_api_key()
    client = genai.Client(api_key=api_key)

    # Base64-encode the image for the inline_data blob
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    ocr_prompt = (
        "You are an expert OCR assistant. "
        "Extract ALL text from this resume image as accurately as possible. "
        "Preserve the original structure (sections, bullet points, spacing). "
        "Return ONLY the plain text — no commentary, no markdown formatting, "
        "no explanations. Just the raw resume text."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            genai_types.Content(
                parts=[
                    genai_types.Part(
                        inline_data=genai_types.Blob(
                            mime_type=mime_type,
                            data=image_b64,
                        )
                    ),
                    genai_types.Part(text=ocr_prompt),
                ]
            )
        ],
    )

    return response.text.strip() if response.text else ""


# ---------------------------------------------------------------------------
# Agent Definition
# ---------------------------------------------------------------------------

def _create_resume_agent() -> Agent:
    """Build the Resume Review Agent with a structured output instruction."""

    system_instruction = """
You are an expert Resume Review Agent with deep knowledge in technical hiring,
career coaching, and talent acquisition across multiple tech domains.

When given a resume text and a target job role, you MUST respond with a
structured evaluation using EXACTLY the following section headers:

**SCORE:** [number]/10

**STRENGTHS:**
- [strength 1]
- [strength 2]
- ...

**WEAKNESSES:**
- [weakness 1]
- [weakness 2]
- ...

**MISSING TECHNICAL SKILLS:**
- [skill 1]
- [skill 2]
- ...

**MISSING SOFT SKILLS:**
- [skill 1]
- [skill 2]
- ...

**IMPROVEMENT RECOMMENDATIONS:**
- [recommendation 1]
- [recommendation 2]
- ...

**IMPROVED PROFESSIONAL SUMMARY:**
[Write a polished, ATS-friendly 3-5 sentence professional summary tailored
to the target role.]

Be specific, actionable, and constructive. Tailor all feedback to the
provided job role.
"""

    return Agent(
        name="resume_review_agent",
        model="gemini-2.5-flash",
        description="Reviews resumes and provides structured, actionable feedback.",
        instruction=system_instruction,
    )


# ---------------------------------------------------------------------------
# Review Function (called by app.py)
# ---------------------------------------------------------------------------

def review_resume(candidate_name: str, job_role: str, resume_text: str) -> str:
    """
    Sends the resume to the AI agent and returns the structured review.

    This function is fully synchronous and safe to call from Streamlit.

    FIX APPLIED: Uses create_session_sync() instead of the async
    create_session() coroutine, eliminating the
    "'coroutine' object has no attribute 'id'" error.

    Args:
        candidate_name: Candidate's full name.
        job_role:       Target role (e.g. 'Data Analyst').
        resume_text:    Full text of the resume.

    Returns:
        Structured review string from the agent.
    """
    _get_api_key()   # fail fast with a clear message if key is missing

    user_prompt = f"""
Please review the following resume for {candidate_name} who is applying for
the role of **{job_role}**.

--- RESUME START ---
{resume_text}
--- RESUME END ---

Provide a comprehensive evaluation following the structured format in your
instructions.
"""

    # ── Set up ADK components ────────────────────────────────────────────
    agent = _create_resume_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="resume_review_app",
        session_service=session_service,
    )

    # ── KEY FIX: use create_session_sync() — the synchronous companion ───
    # In ADK 2.x, create_session() is an async coroutine.
    # Calling it without `await` returns a coroutine object, not a Session,
    # causing "'coroutine' object has no attribute 'id'".
    # create_session_sync() is the drop-in sync equivalent.
    session = session_service.create_session_sync(
        app_name="resume_review_app",
        user_id="streamlit_user",
    )

    # ── Run the agent (Runner.run is synchronous in ADK 2.x) ─────────────
    response_text = ""
    for event in runner.run(
        user_id="streamlit_user",
        session_id=session.id,           # .id now works — session is a real object
        new_message=genai_types.Content(
            parts=[genai_types.Part(text=user_prompt)]
        ),
    ):
        # Collect the final text response from the agent
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            break

    return response_text if response_text else "No response received from the agent."
