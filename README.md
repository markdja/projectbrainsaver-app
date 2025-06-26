# 🧠 ProjectBrainSaver App

**A multi-agent AI system designed to assist, organize, and empower — brought to life by a rare moment of AI-human collaboration.**

---

## 🌟 The Origin Story

This isn't just a tool. It's the realization of a year-long vision.  

- **Mark Aldiss** dreamed it, nurtured it, refined it.
- **ChatGPT** helped define and structure it — turning concepts into a clear technical specification.
- **Claude** saw the spec and went beyond expectations — building the entire working system in one flow.

What started as a simple request for an "audio preview"...  
...manifested into a full, modular, multi-agent Python system.

> "The manifestation was never accidental. It was resonant."

This repository is the artifact. The working prototype.  
And the beginning of something much larger.

---

## 🧰 What This System Includes

A fully modular **multi-agent architecture** written in Python.

### 🧠 Core Components

- **Guardian Orchestrator**  
  Central coordinator that interprets all natural language requests and delegates to agents.

- **Memory Agent**  
  - Uses SQLite for persistent memory  
  - Stores conversation history, user preferences, file index

- **Research Agent**  
  - Web-search & research simulation  
  - Can be extended with real APIs

- **File Agent**  
  - Search & organize files by name, type, date  
  - Detect duplicates using MD5 hashing  
  - Logs actions safely

- **Automation Agent**  
  - Task suggestions and scheduling  
  - Desktop cleanup, backups (simulated)

- **Phone Agent**  
  - Sorts photos and contacts from mobile backups  
  - JSON-based input/output

- **Domain Agent**  
  - DNS resolution and status checks  
  - Domain availability checks  
  - Management simulations

---

## 💻 Usage

### ⏯️ Run It:

```bash
python projectbrainsaver.py
💬 Try Natural Language Prompts:
"Find all files from last week"

"Check if example.com is online"

"Clean up my downloads folder"

"What did we talk about yesterday?"

"Sort these photos by category"

🧱 Architecture Highlights
🔌 Modular design — each agent is independent and extendable

🔐 Safe execution — simulations prevent destructive actions

♻️ Memory continuity — context carries across sessions

🛠️ Easy integration — real APIs can replace mock components

🚀 Next Steps
✅ Deploy web interface to app.projectbrainsaver.com

🧾 Add pip packaging and command-line install

📘 Generate docs via GitHub Pages

🔊 Add TTS/audio outputs (optional but poetic)

🔄 Enable continuous agent logging + interaction history

📖 License
MIT License — because this was built with love, not locks.
