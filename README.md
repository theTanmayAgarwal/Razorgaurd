# 🛡️ RazorGuard: Deterministic AI Dispute Sentinel

![RazorGuard Dashboard Preview](https://img.shields.io/badge/Status-Production_Ready-emerald?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-FastAPI-blue?style=for-the-badge&logo=python) ![Next.js](https://img.shields.io/badge/Next.js-React-black?style=for-the-badge&logo=next.js) ![Gemini](https://img.shields.io/badge/AI-Gemini_2.5_Flash-orange?style=for-the-badge)

RazorGuard is an autonomous, RAG-powered risk operations engine designed for commercial property management (specifically modeled for operations at Ganga Osian Square). It intercepts Razorpay dispute webhooks, extracts evidence from unstructured PDF leases and invoices, and drafts compliance-ready defense payloads. 

**The Core Philosophy:** LLMs are powerful, but they hallucinate. In FinTech, AI should never have unchecked autonomous control over money. RazorGuard bounds AI reasoning within strict, deterministic financial guardrails.

---

## ✨ Key Features & Architecture

### 1. The Deterministic Guardrail Engine
Before any API call is made to Razorpay's contest endpoints, the AI's decision must pass a strict deterministic gate:
* **Value Ceiling:** Any dispute over ₹50,000 bypasses autonomous action and requires human review.
* **Confidence Floor:** The AI must verify matching IDs, amounts, and 2FA logs to score $\ge$ 85% confidence.
* **Hallucination Detection:** The Python backend actively parses the AI output. If the AI claims 100% confidence but the system detects empty evidence arrays or critical risk flags, it overrides the score, flags the hallucination, and locks the payload.

### 2. Human-in-the-Loop Dashboard
Built with Next.js and Tailwind, the dashboard serves as a real-time risk operations center. High-confidence, low-value disputes are auto-contested. Edge cases are routed to the **Manual Review Gate**, where supervisors can inspect the AI-generated verification dossier and one-click authorize the exact `PATCH` API payload.

### 3. RAG Document Pipeline
Utilizes `google-genai` (Gemini 2.5 Flash) and `PyPDF` to parse synthetic invoice PDFs, cross-referencing line items against Razorpay's incoming `payment.dispute.under_review` JSON payload.

---

## ⚠️ The 2 AM Failure Story (And How We Survived)

**The Crash:** 
During batch ingestion stress testing, feeding multiple complex PDFs into the Gemini API concurrently triggered a `429 RESOURCE_EXHAUSTED` rate-limit error. This crashed the FastAPI webhook listener entirely. In a live payment environment, dropping a webhook means missing a dispute window and losing money.

**The Fix:** 
We engineered a highly resilient fallback mechanism. We refactored the ingestion architecture into a throttled queue with strict `time.sleep` intervals to respect API quotas. More importantly, we wrapped the LLM calls in deep `try/except` handlers. If the AI API fails or times out, the backend gracefully degrades: it logs the failure, assigns an automatic 0% confidence score with a rate-limit risk flag, and safely routes the dispute to the Next.js manual review queue. **The server never drops a webhook.**

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14, React, Tailwind CSS, Lucide Icons |
| **Backend** | Python 3, FastAPI, Uvicorn, Pydantic |
| **AI / RAG** | Google GenAI SDK (Gemini 2.5 Flash), PyPDF |
| **Data Pipeline** | Custom synthetic data generation scripts (Webhooks + PDFs) |

---

## ⚙️ Local Setup & Installation

### 1. Run the FastAPI Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic python-dotenv google-genai pypdf
```
#### Create a .env file and add: GEMINI_API_KEY=your_key_here

```bash
uvicorn main:app --reload
```
### 2. Run the Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
Navigate to http://localhost:3000 to access the Risk Operations Dashboard. Click "Simulate Incoming Webhook Batch" to trigger the AI ingestion pipeline.

Built by Tanmay Agarwal
