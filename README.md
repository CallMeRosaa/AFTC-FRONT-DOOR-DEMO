# AFTC Front Door – Test Request Intake Demo

A professional web application for Air Force Test Center (AFTC) test request intake and Tier 1 validation, powered by Anthropic's Claude AI.

## 🎯 Overview

This demo application provides:
- **Tier 1 Validation**: Automated initial gating of test requests
- **Structured Output**: Clarifications, Summary of Request (SOR), and SOC Readiness assessment
- **Visual Readiness Indicators**: RED/AMBER/GREEN badges for quick status assessment
- **PDF Export**: Professional, leadership-ready SOR documents
- **Dark Theme UI**: Modern, easy-to-read interface for extended use

## ✨ Features

### Three-Panel Output Display
1. **Clarifications Panel**: Lists required information for incomplete requests
2. **Summary of Request (SOR) Panel**: Professional summary for validated requests
3. **SOC Readiness Assessment Panel**: Detailed readiness evaluation

### SOC Readiness Status Badges
- 🟢 **GREEN**: Well-defined request ready for SOC review
- 🟡 **AMBER**: Valid request needing refinement
- 🔴 **RED**: Significant gaps requiring clarification
- ⚪ **UNKNOWN**: Status could not be determined

### PDF Export Capability
- One-click export of SOR content
- Professional formatting for leadership briefings
- Includes header, footer, and generation timestamp
- Clean, printable layout (black text on white background)

### Example Requests
- **Example 1**: Incomplete request → Shows clarifications needed, RED status
- **Example 2**: Complete request → Full SOR with GREEN status
- **Example 3**: Partial request → SOR with AMBER status for refinement

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Anthropic API key

### Installation

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

### Running the Application

1. **Start the server**
   ```bash
   python app.py
   ```

   Or use uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open your browser**
   Navigate to: `http://localhost:8000`

3. **Start testing**
   - Select an example request from the dropdown, or
   - Enter your own test request
   - Click "Run Intake" to process
   - Review the three-panel output
   - Export SOR to PDF if needed

## 📋 Run + Demo Checklist

Follow this checklist to demonstrate all features:

### ✅ Step 1: Start Server
```bash
python app.py
```
Expected output: Server running on `http://0.0.0.0:8000`

### ✅ Step 2: Open Browser
- Navigate to `http://localhost:8000`
- Verify the dark-themed UI loads correctly
- Confirm you see the input panel (left) and output panel (right)

### ✅ Step 3: Run Example 1 (Incomplete Request - RED)
1. Select "Example 1: Incomplete Request (RED)" from dropdown
2. Click "Run Intake"
3. **Verify**:
   - 🔴 RED readiness badge appears
   - Clarifications panel shows required information
   - SOR panel shows "No SOR available"
   - Export button is hidden (no SOR to export)

### ✅ Step 4: Run Example 2 (Complete Request - GREEN)
1. Select "Example 2: Complete Request (GREEN)" from dropdown
2. Click "Run Intake"
3. **Verify**:
   - 🟢 GREEN readiness badge appears
   - Clarifications panel shows "No clarifications required"
   - SOR panel displays professional summary
   - SOC Readiness Assessment panel shows detailed evaluation
   - Export SOR to PDF button is visible

### ✅ Step 5: Export SOR to PDF
1. Click "Export SOR to PDF" button
2. **Verify**:
   - Browser print dialog opens
   - Print preview shows ONLY the SOR content
   - Header: "AFTC Front Door – Summary of Request (SOR)"
   - Footer: Generation timestamp and disclaimer
   - Clean white background, black text (no dark theme)
   - Professional formatting suitable for leadership
3. Save as PDF or cancel

### ✅ Step 6: Run Example 3 (Partial Request - AMBER)
1. Select "Example 3: Partial Request (AMBER)" from dropdown
2. Click "Run Intake"
3. **Verify**:
   - 🟡 AMBER readiness badge appears
   - SOR panel shows summary
   - Readiness assessment explains what needs refinement

### ✅ Step 7: Test Clear Function
1. Click "Clear" button
2. **Verify**:
   - Input text area is cleared
   - All output panels reset to empty state
   - Readiness badge disappears
   - Export button disappears

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **app.py**: Main application server
  - `/api/intake`: POST endpoint for request processing
  - `/health`: Health check endpoint
  - Structured JSON response parsing
  - Robust section extraction with fallback logic

### Frontend (Single HTML File)
- **static/index.html**: Complete single-page application
  - Embedded CSS for dark theme and print styles
  - Embedded JavaScript for API calls and UI updates
  - Responsive three-panel layout
  - Client-side PDF export using `window.print()`

### API Response Structure
```json
{
  "mode": "sor_and_readiness",
  "soc_readiness": "GREEN",
  "clarifications_text": "",
  "sor_text": "Requestor: Capt Sarah Mitchell...",
  "readiness_text": "This request is well-defined...",
  "raw_text": "Full output from Claude..."
}
```

## 🔒 Security

- **API Key Protection**: Keys stored in `.env` (server-side only)
- **No Client Exposure**: Frontend never sees API credentials
- **HTTPS Ready**: Can be deployed behind reverse proxy for production
- **Input Validation**: Server-side validation of all inputs

## 📝 API Parameters

### Temperature (0.0 - 1.0)
Controls response randomness:
- **0.7** (default): Balanced creativity and consistency
- Lower: More deterministic, suitable for formal documents
- Higher: More creative, suitable for brainstorming

### Max Tokens (100 - 4000)
Controls response length:
- **2000** (default): Standard for most requests
- Increase for complex, detailed requests
- Decrease for quick summaries

## 🎨 UI Customization

### Print CSS
Print styles are automatically applied when exporting to PDF:
- SOR panel only (other content hidden)
- Professional header and footer
- Black text on white background
- Readable fonts and margins

### Screen Theme
Dark gradient theme optimized for:
- Reduced eye strain during extended use
- Professional military/government aesthetic
- High contrast for readability

## 🛠️ Troubleshooting

### Server won't start
- **Check**: Python version (3.8+)
- **Check**: All dependencies installed (`pip install -r requirements.txt`)
- **Check**: Port 8000 is not in use

### API errors
- **Check**: `.env` file exists with valid `ANTHROPIC_API_KEY`
- **Check**: API key has sufficient credits
- **Check**: Network connectivity

### Parsing issues
- The parser is designed to be tolerant of variations
- Check `raw_text` in the response for full Claude output
- Parser looks for multiple header variations
- Falls back to full text if sections can't be identified

### PDF export issues
- **Chrome/Edge**: Print to PDF works natively
- **Firefox**: Select "Save to PDF" as printer
- **Safari**: Use "Save as PDF" from print dialog

## 📚 Additional Information

### Tier 1 Gating Rules
Requests must include:
1. AFTC test capability identification
2. Requestor organization and POC
3. Clear test objective or question

### SOC Readiness Criteria

**RED**: Significant gaps
- Unclear scope or test objectives
- Missing critical technical details
- Major feasibility concerns

**AMBER**: Needs refinement
- Valid request with minor gaps
- Timeline or resource details needed
- Technical specifications need clarity

**GREEN**: Ready for SOC
- Well-defined scope and objectives
- Sufficient technical detail
- Minimal additional information needed

## 🤝 Contributing

This is a demonstration application. For production use:
1. Add authentication and authorization
2. Implement request logging and audit trails
3. Add database storage for request history
4. Enhance error handling and monitoring
5. Deploy behind HTTPS with proper security headers

## 📄 License

This is a demonstration project for AFTC evaluation purposes.

## 📞 Support

For issues or questions about this demo:
1. Check the troubleshooting section
2. Review the Anthropic API documentation
3. Contact your system administrator

---

**Version**: 1.0.0
**Last Updated**: 2024
**Powered by**: Anthropic Claude API (claude-3-5-sonnet-20241022)
