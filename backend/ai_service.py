import os
import json
from google import genai
from pypdf import PdfReader
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Initialize the modern genai client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class DisputeAssessment(BaseModel):
    is_contestable: bool = Field(description="True if evidence strongly counters the dispute reason")
    confidence_score: int = Field(description="Confidence score between 0 and 100")
    defense_summary: str = Field(description="Structured 2-3 sentence legal defense summary for the acquiring bank")
    evidence_matches: list[str] = Field(description="Key matched evidence points, e.g., 2FA verified, signed lease")
    risk_factors: list[str] = Field(description="Any discrepancies, missing fields, or potential fraud flags")

def extract_pdf_text(pdf_path: str) -> str:
    """Extracts text content from local evidence PDF."""
    if not os.path.exists(pdf_path):
        return ""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def analyze_dispute_with_ai(dispute_id: str, payment_id: str, reason_code: str, amount: int, pdf_path: str) -> dict:
    """
    Sends dispute context + invoice evidence to Gemini for structured evaluation 
    with built-in hallucination guardrails and self-correction checks.
    """
    evidence_text = extract_pdf_text(pdf_path)
    if not evidence_text:
        return {
            "is_contestable": False,
            "confidence_score": 0,
            "defense_summary": "Evidence PDF not found on disk.",
            "evidence_matches": [],
            "risk_factors": ["Missing primary evidence document"],
            "guardrail_passed": False,
            "hallucination_detected": True
        }

    prompt = f"""
    You are an expert FinTech Risk & Dispute Analyst for an Indian merchant using Razorpay.
    
    DISPUTE DETAILS:
    - Dispute ID: {dispute_id}
    - Payment ID: {payment_id}
    - Reason Code: {reason_code}
    - Amount (Paise): {amount} (INR {amount/100:.2f})
    
    PRIMARY EVIDENCE DOCUMENT (EXTRACTED PDF):
    \"\"\"
    {evidence_text}
    \"\"\"
    
    TASK:
    1. Cross-reference the payment ID, dispute reason, and invoice line items.
    2. Determine whether the evidence conclusively disputes the buyer's claim.
    3. Generate a strict JSON object adhering exactly to this schema:
    {{
      "is_contestable": true/false,
      "confidence_score": <integer 0-100>,
      "defense_summary": "<concise 2-3 sentence statement for bank dispute response>",
      "evidence_matches": ["<evidence 1>", "<evidence 2>"],
      "risk_factors": ["<risk 1 if any>"]
    }}
    
    Output ONLY valid JSON. Do not include markdown formatting like ```json.
    """

    # Use the stable SDK implementation
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    # Strip any potential markdown formatting from the response
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        parsed_result = json.loads(clean_text)
        
        # --- ADD-ON 2: DETERMINISTIC HALLUCINATION GUARDRAIL ---
        # Programmatically inspect AI output for common hallucination vectors
        confidence = parsed_result.get("confidence_score", 0)
        matches = parsed_result.get("evidence_matches", [])
        risk_flags = parsed_result.get("risk_factors", [])
        
        # Hallucination check rules:
        # 1. If confidence is 100% but there are no evidence matches, it's a hallucination.
        # 2. If risk factors indicate mismatched payment IDs.
        has_empty_matches_at_high_conf = (confidence > 90 and len(matches) == 0)
        has_critical_risks = any("mismatch" in rf.lower() or "fraud" in rf.lower() for rf in risk_flags)
        
        if has_empty_matches_at_high_conf or has_critical_risks:
            parsed_result["guardrail_passed"] = False
            parsed_result["hallucination_detected"] = True
            parsed_result["confidence_score"] = min(confidence, 40) # Force downgrade confidence
            parsed_result["risk_factors"].append("Guardrail Triggered: Potential AI hallucination or data discrepancy neutralized.")
        else:
            parsed_result["guardrail_passed"] = True
            parsed_result["hallucination_detected"] = False

        return parsed_result

    except Exception as e:
        print(f"Failed to parse AI output: {str(e)}")
        return {
            "is_contestable": False,
            "confidence_score": 0,
            "defense_summary": "Failed to parse structured AI output safely.",
            "evidence_matches": [],
            "risk_factors": ["AI JSON formatting failure"],
            "guardrail_passed": False,
            "hallucination_detected": True
        }