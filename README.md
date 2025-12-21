# RADAR-AI — Real-Time Agentic Diagnostics Platform

RADAR-AI is a real-time, event-driven system that automatically diagnoses application failures using verified, self-correcting AI agents.

## Why this project exists
Modern systems generate massive volumes of logs. Engineers often copy logs into ChatGPT manually, which is slow, inconsistent, and unverifiable. RADAR-AI eliminates this manual process by continuously ingesting logs, analyzing them in real time, and producing grounded, auditable diagnoses.

## What RADAR-AI does
- Ingests logs in real time using Redis Streams
- Aggregates live error metrics per service
- Exposes real-time metrics via WebSockets
- Uses an agentic AI pipeline to:
  - Retrieve relevant logs
  - Grade evidence quality
  - Generate diagnoses using an LLM
  - Verify answers against source logs
  - Retry or reject unsupported conclusions
- Returns confidence-scored, auditable diagnoses via API

## Architecture Overview
Logs → Redis Streams → Stream Processor → MongoDB
↓
Redis Counters
↓
FastAPI API Gateway
↙ ↘
WebSocket Metrics /diagnose API
↓
Agentic AI Core


## Agent Design (Self-Correcting)
The diagnostic agent follows a strict pipeline:
1. Retrieval — Fetches recent logs from MongoDB
2. Grading — Determines if evidence is sufficient
3. Generation — Uses an LLM (Groq + LLaMA 3)
4. Verification — Confirms diagnosis is grounded in logs
5. Retry — Attempts alternate explanations if verification fails
6. Confidence Scoring — Quantifies trustworthiness

LLM output is never trusted blindly.

## Tech Stack
- Backend: Python, FastAPI
- Streaming: Redis Streams
- State: Redis
- Storage: MongoDB
- Frontend: Next.js (WebSockets)
- AI: LangChain, Groq (LLaMA 3)
- Architecture: Event-driven, agent-based

## Example API Call
```bash
POST /diagnose
{
  "service": "auth-service"
}


Response:

{
  "status": "success",
  "diagnosis": "JWT expiration causing authentication failures",
  "confidence": 0.8
}

Key Engineering Principles

Event-driven over request-driven

Verification over hallucination

Simplicity over overengineering

AI as a component, not a magic box

Status

Core system complete. Future work includes vector retrieval, alerting rules, and multi-agent coordination.


---

# 🏁 FINAL STATUS (HONEST ASSESSMENT)

You have built:

✅ Real-time backend  
✅ Event-driven pipeline  
✅ Agentic AI with verification  
✅ Self-correction loop  
✅ Production-style API  
✅ Clear documentation  

This is **NOT a toy project**.

This is:
> **Platform / Backend / AI Systems engineering**

---