# RazorGuard: AI Risk Manager (Razorpay Buildathon 2026)

## The Project
We are building a highly secure, enterprise-grade chargeback evidence auto-responder. 
The system intercepts Razorpay dispute webhooks, uses AI (Gemini 1.5 Pro) to read unstructured evidence (PDFs, logs) against merchant policies, and determines if we can win the dispute. 

## The Core Philosophy (STRICT GUARDRAILS)
1. **Safety First:** The AI NEVER executes API calls or makes database writes directly. 
2. **Deterministic Gating:** The AI only outputs a structured JSON assessment (Confidence Score + Summary). A strict Java backend reads this JSON and executes the API call *only* if the confidence score is >= 85%.
3. **Auditability:** Every action, AI score, and human override is logged in PostgreSQL.

## Tech Stack
*   **Backend:** Java (Spring Boot) - Handles webhooks, rules engine, database connections, and Razorpay API calls.
*   **Frontend:** React / Next.js - A dashboard for the merchant (Ganga Osian Square Property Management) to review AI-drafted dispute responses.
*   **Database:** PostgreSQL.
*   **AI:** Gemini 1.5 Pro API for the RAG pipeline.

## Razorpay API Integration (Test Mode Only)
*   **Ingest:** Listen to `payment.dispute.under_review` webhook.
*   **Evidence:** Upload generated PDFs via Razorpay Documents API (`purpose: dispute_evidence`).
*   **Action:** Call `PATCH /v1/disputes/:id/contest` with the `doc_` IDs.

## Instructions for AI Assistant (Codex/Copilot/Cursor)
When generating code for this project:
1. Do not use overly complex microservices. Keep it a clean, modular monolith.
2. Use standard Razorpay API payload structures (e.g., amounts in paise).
3. Ensure all Java code has strict error handling and logging. 
4. Never generate unconstrained AI agent loops. The flow is strictly: Webhook -> Java -> AI -> Java -> Razorpay API.