# RADAR-AI — Real-Time Agentic Diagnostics Platform

RADAR-AI is a real-time, event-driven system that automatically diagnoses application failures using **verified, self-correcting AI agents**.

---

## Why this project exists

Modern systems generate massive volumes of logs, but engineers still copy-paste logs into ChatGPT manually to debug issues. This is:

- Slow and repetitive  
- Hard to verify or audit  
- Easy to hallucinate or misinterpret

RADAR-AI eliminates this manual loop by continuously ingesting logs, analyzing them in real time, and producing **grounded, auditable diagnoses** via API and UI.

---

## What RADAR-AI does

- Ingests logs in real time using **Redis Streams** and a **Python stream processor**
- Stores structured logs in **MongoDB**, scoped by:
  - `project_id`
  - `project_secret`
  - `service`
- Aggregates live error metrics per service in **Redis**
- Exposes real-time metrics to the frontend via **WebSockets**
- Provides an agentic AI pipeline to:
  - Retrieve relevant logs for a project + service
  - Grade evidence quality (are logs good enough?)
  - Generate diagnoses using an LLM
  - Verify answers against source logs
  - Retry or reject unsupported conclusions
- Returns **confidence-scored, auditable diagnoses** via HTTP APIs
- Suggests **relevant source files** and **LLM-proposed fixes** for selected files

---

## Architecture overview

High-level data flow:

- **Logs** → `Redis Streams` → **Stream Processor (consumer)** → `MongoDB`
- **Error Counters** → `Redis` → `/metrics/errors` + WebSocket
- **FastAPI API Gateway**:
  - `/diagnose` – run agentic diagnosis
  - `/diagnose/files` – diagnosis + related file suggestions
  - `/diagnose/file/fix` – propose fix for a selected file
  - `/project/files`, `/project/file` – safe file listing / reading
  - `/ws/metrics` – real-time metrics over WebSocket
- **Agentic AI Core**:
  - Retrieval → Grading → Generation → Verification → Retry → Confidence scoring

---

## Agent design (self-correcting)

The diagnostic agent follows a strict, verifiable pipeline:

1. **Retrieval**  
   Fetch recent logs from MongoDB for a given `(project_id, project_secret, service)`.

2. **Grading**  
   Decide if logs are “good enough” to attempt an AI diagnosis:
   - Minimum count (`MIN_LOGS`)
   - Must contain at least one `ERROR` log
   - Optional noise filter when all messages are identical

3. **Generation**  
   Use an LLM (via LangChain + Groq / LLaMA 3, or other providers) to propose a root cause and explanation.

4. **Verification**  
   Check whether the LLM’s answer is grounded in the logs:
   - Extract non-trivial tokens from error messages
   - Require that the answer references at least one such token

5. **Retry / Reject**  
   If verification fails, retry with an alternate prompt or return a **failed** diagnosis with low confidence.

6. **Confidence scoring**  
   Attach a numeric confidence score to each diagnosis based on evidence quality and verification outcome.

LLM output is **never trusted blindly**; every diagnosis is grounded in logs.

---

## Tech stack

- **Backend:** Python, FastAPI  
- **Streaming:** Redis Streams  
- **State / Metrics:** Redis  
- **Storage:** MongoDB  
- **Frontend:** Next.js (React) with WebSockets  
- **AI / Agents:** LangChain, Groq (LLaMA 3) and pluggable LLMs  
- **Architecture:** Event-driven, agent-based, log-centric

---

## Example APIs

### Diagnose a service

POST /diagnose
Content-Type: application/json

{
"project_id": "proj_1",
"project_secret": "- - - - - - - - ",
"service": "my-ai-ide"
}

text

Example response:

{
"status": "success",
"project_id": "proj_1",
"service": "my-ai-ide",
"diagnosis": "Gemini model misconfiguration causing repeated chat failures (404 model not found).",
"confidence": 0.82
}

text

### Diagnose + suggest related files

POST /diagnose/files
Content-Type: application/json

{
"project_id": "proj_1",
"project_secret": "- - - - - - - - ",
"service": "my-ai-ide"
}

text

Returns:

- Diagnosis + attempt metadata  
- List of likely-related project files with basic metadata

### Propose a fix for a file

POST /diagnose/file/fix
Content-Type: application/json

{
"project_id": "proj_1",
"project_secret": "- - - - - - - - ",
"service": "my-ai-ide",
"path": "services/chat/llmClient.ts"
}

text

Example response (simplified):

{
"status": "success",
"project_id": "proj_1",
"service": "my-ai-ide",
"path": "services/chat/llmClient.ts",
"original": "// original file contents ...",
"fixed": "// suggested fixed code ...",
"explanation": "Switches from gemini-pro v1beta to a supported model and updates the endpoint."
}

text

---

## Key engineering principles

- **Event-driven over request-driven**  
  Logs flow through a stream and are processed asynchronously, rather than handled only on-demand.

- **Verification over hallucination**  
  Diagnoses are verified against logs; unsupported answers are rejected or retried.

- **Simplicity over overengineering**  
  Uses familiar components (Redis, Mongo, FastAPI, Next.js) in a clear, composable way.

- **AI as a component, not a magic box**  
  The agent is a module in a larger system: logs, storage, retrieval, verification, and UI all matter.

---

## Status

Core system implemented and working:

- ✅ Real-time log ingestion via Redis Streams  
- ✅ Stream processor writing logs to MongoDB  
- ✅ Error metrics via Redis and WebSocket metrics feed  
- ✅ Agentic AI pipeline with retrieval, grading, verification, retry, and confidence scoring  
- ✅ File suggestions + fix proposals for selected files  
- ✅ Next.js frontend dashboard and FastAPI backend

**Future work:**

- Vector-based retrieval over log windows  
- Alerting rules (e.g., Slack / email alerts on patterns)  
- Multi-agent coordination (e.g., separate agents for infra vs. app-level issues)  
- Per-tenant dashboards and multi-project UX

---

## Final assessment

This is **not** a toy CRUD app; it is a full **platform-style backend + AI system** with event-driven architecture, log ingestion, metrics, and grounded LLM diagnostics. It demonstrates skills in:

- Backend and systems design  
- Event-driven architectures  
- Observability/logging  
- Agentic AI and LLM integration  
- Full-stack integration with a real UI