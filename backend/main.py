import os
import json
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai_service import analyze_dispute_with_ai

app = FastAPI(title="RazorGuard API", description="AI Risk Manager Backend")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WebhookEvent(BaseModel):
    event: str
    payload: dict

audit_log_db = []

def process_dispute_payload(dispute_data: dict) -> dict:
    dispute_id = dispute_data.get("id")
    payment_id = dispute_data.get("payment_id")
    reason_code = dispute_data.get("reason_code", "unrecognized")
    amount = dispute_data.get("amount", 0)
    customer_name = dispute_data.get("metadata", {}).get("customer_name", "Tenant")
    description = dispute_data.get("metadata", {}).get("description", "Commercial maintenance")

    pdf_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "data_pipeline", "evidence_docs", f"{dispute_id}_invoice.pdf"
    ))

    try:
        ai_result = analyze_dispute_with_ai(
            dispute_id=dispute_id,
            payment_id=payment_id,
            reason_code=reason_code,
            amount=amount,
            pdf_path=pdf_path
        )
    except Exception as e:
        # Fallback if an individual AI call fails
        ai_result = {
            "is_contestable": False,
            "confidence_score": 0,
            "defense_summary": f"AI evaluation paused due to rate limiting: {str(e)}",
            "evidence_matches": [],
            "risk_factors": ["Rate limit encountered"]
        }

    confidence = ai_result.get("confidence_score", 0)
    is_contestable = ai_result.get("is_contestable", False)
    is_high_value = amount > 5000000  # Amounts > ₹50,000 require human review

    if is_contestable and confidence >= 85 and not is_high_value:
        action = "AUTO_CONTESTED"
        status_label = "Auto-Contested via API"
    else:
        action = "QUEUED_FOR_MANUAL_REVIEW"
        status_label = "Pending Human Approval"

    entry = {
        "dispute_id": dispute_id,
        "payment_id": payment_id,
        "customer_name": customer_name,
        "description": description,
        "amount_inr": amount / 100,
        "reason_code": reason_code,
        "ai_confidence": confidence,
        "action_taken": action,
        "status_label": status_label,
        "defense_summary": ai_result.get("defense_summary"),
        "evidence_matches": ai_result.get("evidence_matches", []),
        "risk_factors": ai_result.get("risk_factors", [])
    }
    
    # Avoid duplicates in demo memory store
    existing_idx = next((i for i, item in enumerate(audit_log_db) if item["dispute_id"] == dispute_id), None)
    if existing_idx is not None:
        audit_log_db[existing_idx] = entry
    else:
        audit_log_db.insert(0, entry)
        
    return entry

@app.post("/api/v1/webhooks/razorpay")
async def handle_razorpay_webhook(event: WebhookEvent):
    if event.event != "payment.dispute.under_review":
        return {"status": "ignored", "message": "Not a dispute event"}
    
    dispute = event.payload.get("dispute", {}).get("entity", {})
    entry = process_dispute_payload(dispute)
    return {"status": "success", "decision": entry["action_taken"], "audit_entry": entry}

@app.post("/api/v1/simulate/batch-ingest")
async def run_batch_simulation():
    """Processes 3 records with a small pause to stay strictly within API quotas."""
    disputes_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_pipeline", "synthetic_disputes.json"))
    if not os.path.exists(disputes_file):
        raise HTTPException(status_code=404, detail="Synthetic data not found")
        
    with open(disputes_file, "r") as f:
        data = json.load(f)

    processed = []
    # Process 3 records to respect free tier rate limits
    for item in data[:3]:
        entity = item.get("payload", {}).get("dispute", {}).get("entity", {})
        res = process_dispute_payload(entity)
        processed.append(res)
        time.sleep(1)  # 1-second pause between calls

    return {"status": "success", "processed_count": len(processed), "records": processed}

@app.get("/api/v1/disputes/audit-log")
def get_audit_logs():
    return {"total_records": len(audit_log_db), "logs": audit_log_db}

@app.post("/api/v1/disputes/{dispute_id}/approve")
def approve_dispute(dispute_id: str):
    for entry in audit_log_db:
        if entry["dispute_id"] == dispute_id:
            entry["action_taken"] = "MANUALLY_APPROVED_AND_SUBMITTED"
            entry["status_label"] = "Contested (Human Approved)"
            return {"status": "success", "updated": entry}
    raise HTTPException(status_code=404, detail="Dispute not found")