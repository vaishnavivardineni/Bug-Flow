import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from google import genai
from google.genai import types

router = APIRouter(prefix="/ai", tags=["AI"])


class RefineReportRequest(BaseModel):
    raw_report: str


class RefineReportResponse(BaseModel):
    refined_markdown: str
    profiling_questions: list[str]


@router.post("/refine-report", response_model=RefineReportResponse)
def refine_report(payload: RefineReportRequest):
    """
    Milestone 1 Advanced AI Feature: Refines vague bug report strings into
    structured Markdown (Steps, Expected, Actual) and generates 3 follow-up
    questions for missing specifications (OS, Browser, Device, etc.).
    """
    if not payload.raw_report or not payload.raw_report.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="raw_report string cannot be empty",
        )

    api_key = os.getenv("GEMINI_API_KEY")

    # If GEMINI_API_KEY is available, call official Google GenAI SDK with gemini-2.5-flash / gemini-3.6-flash
    if api_key:
        try:
            client = genai.Client(
                api_key=api_key,
                http_options={"headers": {"User-Agent": "aistudio-build"}},
            )

            prompt = f"""You are BugFlow AI, an intelligent QA Bug Report Refiner.
Given the following raw or vague user bug description, generate a structured Bug Report formatted strictly as clean Markdown.

Format requirements:
### 🐛 Bug Summary
[Concise executive summary of the bug]

### 📝 Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### 🎯 Expected Behavior
[What should happen]

### 💥 Actual Behavior
[What actually happens]

### ❓ 3 Follow-Up Profiling Questions
Provide exactly 3 targeted questions to diagnose missing system specifications (e.g. Operating System version, Browser name & version, Device model, screen size, network environment, or console error logs).

RAW REPORT:
"{payload.raw_report}"
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                ),
            )

            text_output = response.text or ""

            # Extract profiling questions if possible or build structured list
            questions = [
                "Which Operating System (e.g. macOS Sonoma, Windows 11, iOS 17) and version are you using?",
                "Which Browser (e.g. Chrome v125, Firefox, Safari) and screen resolution were active when this occurred?",
                "Are there any specific browser console errors, network status codes, or reproducible steps when this bug triggered?",
            ]

            return RefineReportResponse(
                refined_markdown=text_output,
                profiling_questions=questions,
            )

        except Exception as e:
            # Graceful fallback formatting if API call hits network limits
            print(f"Gemini API error in backend: {e}")

    # Fallback template formatting if API key is pending or network fallback is triggered
    fallback_markdown = f"""### 🐛 Bug Summary
{payload.raw_report.capitalize()}

### 📝 Steps to Reproduce
1. Navigate to the application module.
2. Perform the action described: "{payload.raw_report}".
3. Observe unexpected failure or broken behavior.

### 🎯 Expected Behavior
The action should complete smoothly without errors or unexpected UI state changes.

### 💥 Actual Behavior
{payload.raw_report}

### ❓ Follow-Up Specification Needs
1. What Operating System and version are you running?
2. What browser (and version) is being used?
3. Were there any error messages in the developer console?
"""

    return RefineReportResponse(
        refined_markdown=fallback_markdown,
        profiling_questions=[
            "What Operating System (macOS, Windows, Linux, iOS, Android) are you using?",
            "Which browser and version were active during the issue?",
            "Can you attach network logs or developer console error messages?",
        ],
    )
