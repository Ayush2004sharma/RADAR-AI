# 🚨 RADAR-AI  
**Agent-Based AI Platform for Production Incident Debugging**

RADAR-AI is a **privacy-first, agent-driven debugging system** that detects production incidents from logs, prioritizes them, identifies the most relevant source files, and generates **AI-assisted diagnoses and fixes** — without direct backend access to user code.

> Built to solve real-world constraints where the backend **cannot access user localhost or filesystem**.

---

## ✨ Why RADAR-AI?

Modern production debugging is slow, manual, and noisy. RADAR-AI automates the entire flow:

- Detects recurring errors automatically  
- Groups them into incidents  
- Identifies the most likely source files  
- Generates grounded AI fixes using logs + code  
- Preserves **code privacy by design**

---

## 🧠 Core Features

### 🔍 Real-Time Incident Detection
- Continuous log ingestion
- Error fingerprinting & incident grouping
- Tracks frequency, severity, and recency

---

### 🤖 Secure Local Watcher (Agent)
- Runs **locally on the user’s machine**
- Streams logs in real time
- Periodically sends **file structure metadata only**
- Sends actual file content **only when explicitly requested**

> Backend never accesses `localhost` or filesystem directly.

---

### 📂 Deterministic File Ranking
- Ranks **300+ source files** using:
  - Incident logs
  - File paths & heuristics
  - Service context
- Reduces AI hallucination before LLM usage

---

### 🧠 AI-Assisted Diagnosis & Fixes
- Uses LLMs (Groq / LLaMA)
- Generates:
  - Clear root-cause explanations
  - Minimal, grounded code fixes
- Strictly bounded by logs + requested file content
- Includes verification and fallback logic

---

### 🔐 Privacy-First Architecture
- No persistent code storage
- No full source uploads
- Poll-based agent communication
- File content shared only on demand

---

## 🏗️ Architecture Overview

User Application
│
│ logs
▼
RADAR Watcher (Local Agent)
├── streams logs
├── pushes file structure
└── waits for backend file requests
│
▼
RADAR Backend (FastAPI)
├── Incident detection & prioritization
├── Deterministic file ranking
├── Requests specific files
└── AI diagnosis & fix generation

markdown
Copy code

---

## 🔁 End-to-End Debugging Flow

1. Logs are streamed to RADAR-AI
2. Errors are grouped into incidents
3. Incidents are prioritized automatically
4. File structure is used to rank likely files
5. Backend requests a specific file from watcher
6. Watcher sends file content
7. AI generates diagnosis & fix
8. User reviews and resolves incident

---

## 🛠 Tech Stack

**Backend**
- Python
- FastAPI
- MongoDB

**AI**
- Groq (LLaMA models)
- Deterministic scoring + verification layer

**Frontend**
- React
- Next.js
- Tailwind CSS

**Agent**
- Python
- Threaded log watcher
- Poll-based communication model

---

## 📡 API Overview

RADAR-AI exposes APIs for:

- Authentication (`/auth`)
- Log ingestion (`/logs/ingest`)
- Agent communication (`/agent/*`)
- Project management (`/projects`)
- Incident analysis (`/incidents/*`)

📄 Interactive API docs available at:

/docs

yaml
Copy code

---

## 🚫 Why Not LangChain / LangGraph?

RADAR-AI intentionally avoids orchestration frameworks.

Instead, it implements:
- Explicit agent state
- Deterministic control flow
- Manual verification and retries

> The system follows a **LangGraph-style agent architecture**, implemented from scratch for production safety, observability, and control.

---

## 📈 Performance & Scale

- Handles **100+ logs/min**
- Ranks **300+ files per project**
- File request latency: **<3 seconds**
- Designed for multi-project, multi-user usage

---

## 🔐 Security Model

- Backend never accesses user filesystem
- Project secrets validated per request
- No code stored permanently
- No hidden data transfer

---

## 🚀 Future Improvements

- Diff-based file updates
- WebSocket-based agent communication
- VS Code plugin
- Advanced incident correlation

---

## 👤 Author

**Ayush Sharma**  
Full-Stack / Backend Engineer  
Focused on **AI systems, debugging platforms, and production-grade architectures**

---

## ⭐ Support

If you find this project useful:

- ⭐ Star the repo
- 🐞 Open issues
- 💡 Suggest improvements

---

> RADAR-AI is built as a **real-world production system**, not a demo.  
> Every design choice prioritizes **safety, determinism, and developer trust**.