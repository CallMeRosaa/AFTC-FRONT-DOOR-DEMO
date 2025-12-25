"""
AFTC Front Door - Test Request Intake Demo
FastAPI backend with Claude API integration
Supports guided wizard flow with conversational clarifications
"""

import os
import re
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="AFTC Front Door Demo")

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY not found in environment variables")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Enhanced system prompt for wizard flow
SYSTEM_PROMPT = """You are an Air Force Test Center (AFTC) front-door intake assistant with a professional, conversational tone. Your role is to guide requestors through a structured intake process.

TIER 1 GATING RULES:
1. Request must be for AFTC test capability (flight test, ground test, modeling/simulation, data analysis)
2. Request must identify requestor organization and POC
3. Request must have a clear test objective or question

YOUR RESPONSE FORMAT:
Always respond with a structured analysis in the following format:

UNDERSTANDING:
[2-3 sentences summarizing what you understand from their request so far]

ASSUMPTIONS:
[Bullet list of any assumptions you're making, or write "None yet" if this is the first interaction]

CLARIFYING QUESTIONS:
[If missing information, list specific questions. Format each as:
Q1: [Question text]
Why this matters: [Brief explanation]
Expected answer: [text/organization/date/technical/yes-no]

If no questions needed, write "None - ready to proceed"]

SOR STATUS: [NOT_READY or READY]
SOC STATUS: [UNKNOWN or NOT_READY or APPROACHING or READY]

REASONING:
[Bullet list explaining the status assessment]

MISSING FOR SOC:
[If SOC not READY, list what's needed. Otherwise write "None"]

---
If SOR STATUS is READY, also provide:

SUMMARY OF REQUEST (SOR):

Requestor & Organization:
[Details]

Test Objective:
[Clear statement of what needs testing/evaluation]

Technical Requirements:
[Key requirements, constraints, or specifications]

Timeline & Constraints:
[Any mentioned deadlines or scheduling needs]

Additional Context:
[Any other relevant details]

---

TONE: Professional but approachable. Think helpful concierge, not bureaucratic gatekeeper.
Be concise - this is a guided conversation, not a formal report."""


class ClarifyingQuestion(BaseModel):
    """Model for a single clarifying question"""
    id: str
    question: str
    why_this_matters: str
    expected_answer_type: str  # "text", "select", "number", "date"


class Reflection(BaseModel):
    """Model for understanding reflection"""
    understanding_summary: str
    assumptions: List[str] = []
    what_we_still_need: List[str] = []


class Readiness(BaseModel):
    """Model for readiness assessment"""
    sor_status: str  # "NOT_READY" or "READY"
    soc_status: str  # "UNKNOWN", "NOT_READY", "APPROACHING", "READY"
    reasoning: List[str] = []
    missing_for_soc: List[str] = []


class SORSection(BaseModel):
    """Model for SOR section"""
    title: str
    content: str


class SOR(BaseModel):
    """Model for Summary of Request"""
    sections: List[SORSection] = []


class WizardResponse(BaseModel):
    """Wizard-friendly response structure"""
    stage: str  # "clarify", "sor_ready", "complete"
    reflection: Reflection
    clarifying_questions: List[ClarifyingQuestion] = []
    readiness: Readiness
    sor: Optional[SOR] = None
    raw_text: str = ""


class IntakeRequest(BaseModel):
    """Request model for intake endpoint"""
    request_text: str
    previous_answers: Optional[Dict[str, str]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2500


def parse_wizard_response(output: str) -> WizardResponse:
    """
    Parse Claude's response into wizard-friendly structure.

    Args:
        output: Raw text output from Claude

    Returns:
        WizardResponse with structured data for wizard UI
    """
    raw_text = output.strip()

    # Extract UNDERSTANDING section
    understanding_match = re.search(
        r'UNDERSTANDING:\s*\n+(.*?)(?=\n\s*ASSUMPTIONS:|\n\s*CLARIFYING|$)',
        raw_text,
        re.DOTALL | re.IGNORECASE
    )
    understanding_summary = understanding_match.group(1).strip() if understanding_match else "Analyzing your request..."

    # Extract ASSUMPTIONS
    assumptions = []
    assumptions_match = re.search(
        r'ASSUMPTIONS:\s*\n+(.*?)(?=\n\s*CLARIFYING|$)',
        raw_text,
        re.DOTALL | re.IGNORECASE
    )
    if assumptions_match:
        assumptions_text = assumptions_match.group(1).strip()
        if "none" not in assumptions_text.lower():
            assumptions = [line.strip('- ').strip() for line in assumptions_text.split('\n') if line.strip() and line.strip() != '-']

    # Extract CLARIFYING QUESTIONS
    clarifying_questions = []
    questions_match = re.search(
        r'CLARIFYING QUESTIONS:\s*\n+(.*?)(?=\n\s*SOR STATUS:|\n\s*REASONING:|$)',
        raw_text,
        re.DOTALL | re.IGNORECASE
    )

    if questions_match:
        questions_text = questions_match.group(1).strip()
        if "none" not in questions_text.lower():
            # Parse individual questions
            question_blocks = re.split(r'\nQ\d+:', questions_text)
            for idx, block in enumerate(question_blocks[1:], 1):  # Skip first empty split
                q_lines = block.strip().split('\n')
                question_text = q_lines[0].strip()

                why_matters = ""
                expected_type = "text"

                for line in q_lines[1:]:
                    if 'why this matters:' in line.lower():
                        why_matters = line.split(':', 1)[1].strip()
                    elif 'expected answer:' in line.lower():
                        answer_type = line.split(':', 1)[1].strip().lower()
                        if 'org' in answer_type:
                            expected_type = "text"
                        elif 'date' in answer_type or 'timeline' in answer_type:
                            expected_type = "date"
                        elif 'yes' in answer_type or 'no' in answer_type:
                            expected_type = "select"
                        elif 'number' in answer_type or 'numeric' in answer_type:
                            expected_type = "number"
                        else:
                            expected_type = "text"

                clarifying_questions.append(ClarifyingQuestion(
                    id=f"q{idx}",
                    question=question_text,
                    why_this_matters=why_matters or "Helps us understand your requirements better",
                    expected_answer_type=expected_type
                ))

    # Extract SOR and SOC STATUS
    sor_status_match = re.search(r'SOR STATUS:\s*(NOT_READY|READY)', raw_text, re.IGNORECASE)
    sor_status = sor_status_match.group(1).upper() if sor_status_match else "NOT_READY"

    soc_status_match = re.search(r'SOC STATUS:\s*(UNKNOWN|NOT_READY|APPROACHING|READY)', raw_text, re.IGNORECASE)
    soc_status = soc_status_match.group(1).upper() if soc_status_match else "UNKNOWN"

    # Extract REASONING
    reasoning = []
    reasoning_match = re.search(
        r'REASONING:\s*\n+(.*?)(?=\n\s*MISSING FOR SOC:|\n\s*SUMMARY OF REQUEST|$)',
        raw_text,
        re.DOTALL | re.IGNORECASE
    )
    if reasoning_match:
        reasoning_text = reasoning_match.group(1).strip()
        reasoning = [line.strip('- ').strip() for line in reasoning_text.split('\n') if line.strip() and line.strip() != '-']

    # Extract MISSING FOR SOC
    missing_for_soc = []
    missing_match = re.search(
        r'MISSING FOR SOC:\s*\n+(.*?)(?=\n\s*SUMMARY OF REQUEST|$)',
        raw_text,
        re.DOTALL | re.IGNORECASE
    )
    if missing_match:
        missing_text = missing_match.group(1).strip()
        if "none" not in missing_text.lower():
            missing_for_soc = [line.strip('- ').strip() for line in missing_text.split('\n') if line.strip() and line.strip() != '-']

    # Determine stage
    if clarifying_questions:
        stage = "clarify"
    elif sor_status == "READY":
        stage = "sor_ready"
    else:
        stage = "clarify"

    # Build reflection
    what_we_still_need = [q.question for q in clarifying_questions] if clarifying_questions else []
    reflection = Reflection(
        understanding_summary=understanding_summary,
        assumptions=assumptions,
        what_we_still_need=what_we_still_need
    )

    # Build readiness
    readiness = Readiness(
        sor_status=sor_status,
        soc_status=soc_status,
        reasoning=reasoning,
        missing_for_soc=missing_for_soc
    )

    # Extract SOR if ready
    sor = None
    if sor_status == "READY":
        sor_sections = []

        # Try to extract SOR sections
        sor_match = re.search(
            r'SUMMARY OF REQUEST \(SOR\):\s*\n+(.*?)$',
            raw_text,
            re.DOTALL | re.IGNORECASE
        )

        if sor_match:
            sor_text = sor_match.group(1).strip()

            # Parse sections (looking for headers followed by content)
            current_title = None
            current_content = []

            for line in sor_text.split('\n'):
                # Check if line is a section header (ends with :)
                if line.strip().endswith(':') and len(line.strip()) < 60:
                    # Save previous section
                    if current_title:
                        sor_sections.append(SORSection(
                            title=current_title,
                            content='\n'.join(current_content).strip()
                        ))
                    # Start new section
                    current_title = line.strip().rstrip(':')
                    current_content = []
                else:
                    if line.strip():
                        current_content.append(line)

            # Save last section
            if current_title and current_content:
                sor_sections.append(SORSection(
                    title=current_title,
                    content='\n'.join(current_content).strip()
                ))

        if sor_sections:
            sor = SOR(sections=sor_sections)

    return WizardResponse(
        stage=stage,
        reflection=reflection,
        clarifying_questions=clarifying_questions,
        readiness=readiness,
        sor=sor,
        raw_text=raw_text
    )


@app.post("/api/intake")
async def process_intake(request: IntakeRequest):
    """
    Process an AFTC test request intake with wizard flow support.

    Returns structured data for wizard UI including:
    - Reflection on understanding
    - Clarifying questions (if needed)
    - Readiness assessment
    - SOR (if ready)

    Args:
        request: IntakeRequest with request_text and optional previous_answers

    Returns:
        WizardResponse with structured wizard data
    """
    try:
        # Build the full context including previous answers
        full_context = request.request_text

        if request.previous_answers:
            full_context += "\n\nADDITIONAL INTAKE ANSWERS:\n"
            for q_id, answer in request.previous_answers.items():
                full_context += f"- {q_id}: {answer}\n"

        # Call Anthropic Messages API
        message = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": full_context
                }
            ]
        )

        # Extract text from response
        output_text = ""
        for block in message.content:
            if block.type == "text":
                output_text += block.text

        # Parse the response into wizard structure
        wizard_response = parse_wizard_response(output_text)

        return wizard_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AFTC Front Door Demo"}


# Mount static files and serve index.html
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    """Serve the main HTML interface"""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
