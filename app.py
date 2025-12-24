"""
AFTC Front Door - Test Request Intake Demo
FastAPI backend with Claude API integration
Supports structured output parsing and SOC readiness assessment
"""

import os
import re
from typing import Optional
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

# System prompt for AFTC intake
SYSTEM_PROMPT = """You are an Air Force Test Center (AFTC) front-door intake assistant. Your role is to perform initial Tier 1 validation of incoming test and evaluation requests.

TIER 1 GATING RULES:
1. Request must be for AFTC test capability (flight test, ground test, modeling/simulation, data analysis)
2. Request must identify requestor organization and POC
3. Request must have a clear test objective or question

RESPONSE MODES:

MODE 1 - Clarifications Required (fails Tier 1):
If the request does NOT meet all three gating rules, respond with:
---
Priority Clarifications Required

[List the specific missing information needed to proceed]

Status: Tier 1 Incomplete
---

MODE 2 - Initial Validated Intake (passes Tier 1):
If the request PASSES all three gating rules, provide:

1. Summary of Request (SOR):
[Create a concise, professional summary of the request including:
- Requestor and organization
- Test objective or capability needed
- Key technical requirements or constraints
- Timeline if mentioned]

2. SOC Readiness Status: [RED/AMBER/GREEN]

SOC Readiness Assessment:
[Provide assessment with rationale:
- RED: Significant gaps in technical definition, scope unclear, or major feasibility concerns
- AMBER: Request is valid but needs refinement on technical details, timeline, or resource requirements
- GREEN: Well-defined request ready for SOC review with minimal additional information needed]

Status: Initial Validated Intake
---

Always maintain a professional, helpful tone appropriate for military/government requestors."""


class IntakeRequest(BaseModel):
    """Request model for intake endpoint"""
    request_text: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


class IntakeResponse(BaseModel):
    """Structured response from intake processing"""
    mode: str  # "clarifications_only" or "sor_and_readiness"
    soc_readiness: str  # "RED", "AMBER", "GREEN", or "UNKNOWN"
    clarifications_text: str
    sor_text: str
    readiness_text: str
    raw_text: str


def parse_claude_response(output: str) -> IntakeResponse:
    """
    Parse Claude's response into structured sections.
    Implements robust, tolerant parsing for real-world variation.

    Args:
        output: Raw text output from Claude

    Returns:
        IntakeResponse with parsed sections
    """
    raw_text = output.strip()

    # Initialize response fields
    mode = "clarifications_only"
    soc_readiness = "UNKNOWN"
    clarifications_text = ""
    sor_text = ""
    readiness_text = ""

    # Determine mode by looking for SOR indicators
    sor_indicators = [
        "Summary of Request",
        "SOR:",
        "Status: Initial Validated Intake",
        "SOC Readiness Status:",
        "SOC Readiness Assessment:"
    ]

    has_sor = any(indicator.lower() in raw_text.lower() for indicator in sor_indicators)
    if has_sor:
        mode = "sor_and_readiness"

    # Extract SOC Readiness Status
    readiness_patterns = [
        r'SOC Readiness Status:\s*(RED|AMBER|GREEN)',
        r'Readiness Status:\s*(RED|AMBER|GREEN)',
        r'Status:\s*(RED|AMBER|GREEN)',
        r'\b(RED|AMBER|GREEN)\b(?=\s*SOC|\s*Readiness)',
    ]

    for pattern in readiness_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            soc_readiness = match.group(1).upper()
            break

    # If no explicit status found, look for standalone RED/AMBER/GREEN near readiness section
    if soc_readiness == "UNKNOWN":
        lines = raw_text.split('\n')
        for i, line in enumerate(lines):
            if 'readiness' in line.lower():
                # Check next few lines for status
                for j in range(i, min(i+5, len(lines))):
                    if re.search(r'\b(RED|AMBER|GREEN)\b', lines[j], re.IGNORECASE):
                        match = re.search(r'\b(RED|AMBER|GREEN)\b', lines[j], re.IGNORECASE)
                        soc_readiness = match.group(1).upper()
                        break
                break

    # Parse sections based on mode
    if mode == "clarifications_only":
        # Extract clarification content
        clarification_patterns = [
            r'Priority Clarifications Required\s*\n+(.*?)(?=\n\s*Status:|$)',
            r'Clarification Request\s*\n+(.*?)(?=\n\s*Status:|$)',
            r'Clarifications Required\s*\n+(.*?)(?=\n\s*Status:|$)',
        ]

        for pattern in clarification_patterns:
            match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                clarifications_text = match.group(1).strip()
                break

        # If no specific section found, use full text (minus headers)
        if not clarifications_text:
            clarifications_text = raw_text

    else:  # mode == "sor_and_readiness"
        # Extract SOR section
        sor_patterns = [
            r'(?:Summary of Request|SOR:?)\s*\n+(.*?)(?=\n\s*(?:\d+\.?\s*)?SOC Readiness|$)',
            r'(?:Summary of Request|SOR)[\s:]*\n+(.*?)(?=SOC Readiness|Status:|$)',
        ]

        for pattern in sor_patterns:
            match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                sor_text = match.group(1).strip()
                break

        # Extract SOC Readiness section
        readiness_patterns_section = [
            r'(?:SOC Readiness Status|SOC Readiness Assessment)[\s:]*\n+(.*?)(?=\n\s*Status:|$)',
            r'SOC Readiness[\s:]*[A-Z]+\s*\n+(.*?)(?=\n\s*Status:|$)',
        ]

        for pattern in readiness_patterns_section:
            match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                readiness_text = match.group(1).strip()
                break

        # Fallback: if sections not clearly delineated, try splitting by common headers
        if not sor_text and not readiness_text:
            # Look for numbered sections or clear breaks
            parts = re.split(r'\n\s*\d+\.\s+', raw_text)
            if len(parts) >= 2:
                sor_text = parts[1].strip() if len(parts) > 1 else ""
                readiness_text = parts[2].strip() if len(parts) > 2 else ""

    return IntakeResponse(
        mode=mode,
        soc_readiness=soc_readiness,
        clarifications_text=clarifications_text,
        sor_text=sor_text,
        readiness_text=readiness_text,
        raw_text=raw_text
    )


@app.post("/api/intake", response_model=IntakeResponse)
async def process_intake(request: IntakeRequest):
    """
    Process an AFTC test request intake.

    Calls Claude API with AFTC system prompt and parses the response
    into structured sections for display and PDF export.

    Args:
        request: IntakeRequest with request_text and optional parameters

    Returns:
        IntakeResponse with parsed sections and metadata
    """
    try:
        # Call Anthropic Messages API
        # Using Claude 3 Haiku (fastest, most compatible model)
        message = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": request.request_text
                }
            ]
        )

        # Extract text from response
        output_text = ""
        for block in message.content:
            if block.type == "text":
                output_text += block.text

        # Parse the response into structured format
        parsed_response = parse_claude_response(output_text)

        return parsed_response

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
