# AFTC Front Door – Guided Request Wizard

A conversational, wizard-based web application for Air Force Test Center (AFTC) test request intake and Tier 1 validation, powered by Anthropic's Claude AI.

## 🎯 Overview

The AFTC Front Door provides a guided, step-by-step wizard that transforms plain-language test requests into structured Summary of Request (SOR) documents. The system uses a conversational approach with progressive disclosure, asking clarifying questions one at a time and providing continuous feedback.

### Key Features

- **🎭 Guided Wizard Flow**: Step-by-step process from welcome to completion
- **💬 Conversational Clarifications**: Ask questions one at a time with context
- **🔄 Understanding Reflection**: Show what the system understands before proceeding
- **📊 Readiness Assessment**: Visual SOR/SOC status indicators
- **📋 Structured SOR Output**: Clean, collapsible sections for easy review
- **🎨 Modern Dark UI**: Professional Air Force tech aesthetic
- **📱 Responsive Design**: Works on desktop and tablet

## ✨ User Journey

### Step 0: Welcome
- Friendly introduction with reassurance bullets
- Sets expectations: "You can be high-level. We'll guide you."
- Single action: "Start my request"

### Step 1: Initial Intake
- Large textarea for plain-language request
- Placeholder example for guidance
- Optional advanced settings (temperature, max tokens) hidden by default
- Submit with "Continue" button

### Step 2: Reflection
- Shows understanding summary in conversational language
- Lists any assumptions being made
- Two clear choices:
  - "Yes, that's accurate" → proceed
  - "Let me clarify" → edit request

### Step 3: Clarifying Questions (if needed)
- **One question at a time** (not overwhelming)
- Each question includes:
  - Clear question text
  - "Why this matters" explanation
  - Appropriate input control (text, date, select, number)
- Navigate forward/backward through questions
- Submit all answers together

### Step 4: Readiness Snapshot
- Visual status badges:
  - **SOR Status**: NOT_READY or READY
  - **SOC Status**: UNKNOWN, NOT_READY, APPROACHING, or READY
- Bulleted assessment reasoning
- Guidance on what's missing for SOC readiness
- Context-aware next action button

### Step 5: SOR Output
- Professional structured summary with collapsible sections:
  - Requestor & Organization
  - Test Objective
  - Technical Requirements
  - Timeline & Constraints
  - Additional Context
- Copy to clipboard functionality
- Continue to next steps

### Step 6: Next Steps & Guidance
- Cards for future actions:
  - Notional lifecycle roadmap
  - Geographic considerations
  - Platform/aircraft considerations
  - Team introduction
- SOC improvement guidance (if applicable)
- Start another request

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Anthropic API key

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AFTC-FRONT-DOOR-DEMO
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` and add your Anthropic API key**
   ```bash
   ANTHROPIC_API_KEY=your_api_key_here
   ```

5. **Start the server**
   ```bash
   python app.py
   ```

   Or with uvicorn:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Open your browser**
   Navigate to: `http://localhost:8000`

## ☁️ Railway Deployment

### Environment Variables

In your Railway dashboard:

1. Go to your service → **Variables** tab
2. Add the following variable:
   - **Key**: `ANTHROPIC_API_KEY`
   - **Value**: Your Anthropic API key

### Deployment Configuration

The app is configured for Railway with:
- **Procfile**: Specifies the start command
- **railway.toml**: Deployment settings and health checks
- **Health check**: `/health` endpoint
- **Auto-scaling**: Supports Railway's scaling features

### Verify Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.railway.app/health

# API documentation
https://your-app.railway.app/docs
```

## 🏗️ Architecture

### Backend (FastAPI + Python)

**File**: `app.py`

Key components:
- **Wizard Response Model**: Structured JSON for UI consumption
  - `stage`: Current workflow stage (clarify/sor_ready/complete)
  - `reflection`: Understanding summary and assumptions
  - `clarifying_questions`: Structured questions with context
  - `readiness`: SOR/SOC status with reasoning
  - `sor`: Structured sections when ready

- **Enhanced System Prompt**: Guides Claude to generate conversational, structured responses

- **Parsing Logic**: Robust extraction of sections from Claude's output

- **API Endpoints**:
  - `POST /api/intake`: Main wizard endpoint
  - `GET /health`: Health check
  - `GET /docs`: Interactive API documentation

### Frontend (Single HTML)

**File**: `static/index.html`

Architecture:
- **Vanilla JavaScript**: No frameworks, simple state machine
- **Embedded CSS**: Dark theme with Air Force tech aesthetic
- **Progressive Disclosure**: Show one primary focus per step
- **Responsive Layout**: Mobile-friendly design

State management:
```javascript
{
  currentStep: 0-6,
  wizardData: { ... },  // Latest backend response
  questions: [...],     // Clarifying questions
  answers: {...}        // User responses
}
```

### API Request/Response

**Request**:
```json
{
  "request_text": "string",
  "previous_answers": {
    "q1": "answer",
    "q2": "answer"
  },
  "temperature": 0.7,
  "max_tokens": 2500
}
```

**Response**:
```json
{
  "stage": "clarify",
  "reflection": {
    "understanding_summary": "...",
    "assumptions": ["..."],
    "what_we_still_need": ["..."]
  },
  "clarifying_questions": [
    {
      "id": "q1",
      "question": "...",
      "why_this_matters": "...",
      "expected_answer_type": "text"
    }
  ],
  "readiness": {
    "sor_status": "NOT_READY",
    "soc_status": "UNKNOWN",
    "reasoning": ["..."],
    "missing_for_soc": ["..."]
  },
  "sor": null
}
```

## 🔒 Security

- **API Key Protection**: Keys stored in `.env` (server-side only)
- **No Client Exposure**: Frontend never sees credentials
- **HTTPS Ready**: Deploy behind reverse proxy for production
- **Input Validation**: Server-side validation of all inputs
- **Error Handling**: Friendly messages, no stack traces to users

## 🎨 Design Principles

### Conversational Tone
- Professional but approachable (concierge, not gatekeeper)
- Plain language, not bureaucratic jargon
- Helpful explanations ("Why this matters")

### Progressive Disclosure
- One primary focus per step
- No overwhelming walls of text
- Clear next actions at each stage

### Visual Hierarchy
- Large, readable typography
- High contrast for accessibility
- Generous spacing
- Subtle animations (professional, not flashy)

### Color System
- **Primary**: Blues (#64b5f6, #42a5f5) - Trust, clarity
- **Success**: Greens - Ready status
- **Warning**: Orange/Amber - Needs attention
- **Error**: Red - Not ready, needs work
- **Background**: Dark gradients - Reduce eye strain

## 📝 Customization

### Adjusting System Behavior

**Temperature** (0.0 - 1.0):
- **0.7** (default): Balanced creativity and consistency
- Lower: More deterministic, formal
- Higher: More creative, conversational

**Max Tokens** (500 - 4000):
- **2500** (default): Standard for most requests
- Increase for complex, detailed requests
- Decrease for quicker responses

### Modifying the System Prompt

Edit `SYSTEM_PROMPT` in `app.py` to:
- Adjust tone (formal vs conversational)
- Change gating rules
- Modify output format
- Add domain-specific guidance

### Styling the UI

All styles are in `static/index.html`:
- Colors: Search for hex values (#64b5f6, etc.)
- Spacing: Adjust padding/margin values
- Typography: Change font-family, font-size
- Animations: Modify @keyframes and transitions

## 🛠️ Troubleshooting

### Server Issues

**Server won't start:**
- Check Python version (3.8+)
- Verify all dependencies: `pip install -r requirements.txt`
- Ensure port 8000 is available

**API key errors:**
- Verify `.env` file exists with `ANTHROPIC_API_KEY`
- Check API key is valid and has credits
- Restart server after changing `.env`

### API Issues

**"We hit a snag" errors:**
- Check network connectivity
- Verify API key is valid
- Check Railway logs for backend errors

**Parsing errors:**
- System is designed to be tolerant of variations
- Check `raw_text` field in response for debugging
- Parser looks for multiple header variations

### UI Issues

**Wizard doesn't progress:**
- Check browser console for JavaScript errors
- Verify `/api/intake` endpoint is accessible
- Try clearing browser cache

**Questions not showing:**
- Check that backend returned `clarifying_questions` array
- Verify question format matches expected schema
- Check console for parsing errors

## 📚 API Documentation

### Interactive Docs

Visit `/docs` when server is running:
- **Local**: http://localhost:8000/docs
- **Railway**: https://your-app.railway.app/docs

Features:
- Try API endpoints directly
- See request/response schemas
- View all available operations

### Health Check

```bash
GET /health

Response:
{
  "status": "healthy",
  "service": "AFTC Front Door Demo"
}
```

### Main Intake Endpoint

```bash
POST /api/intake
Content-Type: application/json

{
  "request_text": "We need flight testing...",
  "previous_answers": {"q1": "412th Test Wing"},
  "temperature": 0.7,
  "max_tokens": 2500
}
```

## 🤝 Development

### Project Structure

```
AFTC-FRONT-DOOR-DEMO/
├── app.py                  # FastAPI backend
├── static/
│   └── index.html         # Wizard UI (HTML + CSS + JS)
├── requirements.txt        # Python dependencies
├── Procfile               # Railway start command
├── railway.toml           # Railway configuration
├── .env                   # Environment variables (gitignored)
├── .env.example           # Template for .env
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

### Making Changes

**Backend changes:**
1. Edit `app.py`
2. Test with: `uvicorn app:app --reload`
3. Check `/docs` for API changes

**Frontend changes:**
1. Edit `static/index.html`
2. Refresh browser (hard refresh: Cmd/Ctrl + Shift + R)
3. Test wizard flow end-to-end

**Deploy changes:**
```bash
git add .
git commit -m "Description of changes"
git push
```

Railway auto-deploys on push.

## 🎯 Future Enhancements

Potential additions:
- **Authentication**: User login and request history
- **Database**: Persist requests and track status
- **Email Notifications**: Auto-notify team when SOR ready
- **PDF Export**: Generate formatted PDF of SOR
- **Multi-language**: Support for other languages
- **Admin Dashboard**: View all requests, analytics

## 📄 License

This is a demonstration project for AFTC evaluation purposes.

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review `/docs` for API details
3. Check Railway logs for deployment issues
4. Contact your system administrator

---

**Version**: 2.0.0 (Wizard Flow)
**Last Updated**: December 2024
**Powered by**: Anthropic Claude 3 Haiku
