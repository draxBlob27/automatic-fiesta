# Automatic-fiesta
🧠 Multi-Agent AI System for Smart Document & Message Processing
================================================================

✨ Overview
----------

This project is a modular **multi-agent AI system** designed to intelligently process unstructured and structured inputs like PDFs, JSON payloads, and Emails. It automatically classifies, routes, and extracts key data — all while maintaining shared context across a lightweight memory module.

From handling invoices to extracting urgent RFQs, this system gives structure to chaos — and context to content.

🎯 Objective
------------

Enable seamless and intelligent routing of inputs through specialized AI agents:

*   **Classify** file format and intent (e.g., Invoice, RFQ, Complaint)
    
*   **Route** the input to the correct AI agent
    
*   **Extract** structured, actionable data
    
*   **Persist** shared context and memory across interactions
    

🧩 System Architecture
----------------------

### 🔍 1. Classifier Agent

*   **Input**: Raw file (PDF), JSON payload, or plain-text Email
    
*   **Function**:
    
    *   Classifies **format** (PDF / JSON / Email)
        
    *   Determines **intent** (e.g., Invoice, Complaint, RFQ)
        
    *   **Routes** to the appropriate agent

### 📦 2. JSON Agent

*   Accepts structured JSON
    
*   Validates against expected schemas
    
*   Extracts and reformats data
    
*   Flags anomalies or missing fields
    

### ✉️ 3. Email Agent

*   Processes raw email content (text)
    
*   Extracts sender, urgency, and intent
    
*   Formats output for CRM-style usage
    

### 🧠 Shared Memory Module

A lightweight memory system using **Redis Cloud** to maintain:

*   Source metadata (origin, type, timestamp)
    
*   Extracted fields and values
    
*   Thread/Conversation ID for traceability

⚙️ Features & Highlights
------------------------

*   ✅ **Multi-agent orchestration** via a Classifier Agent
    
*   📄 **PDF Support**: Extracts text and tries to infer structure (email or JSON-like)
    
*   🔌 **Flexible CLI Input**: Accepts both file paths and literal strings
    
*   🧾 **Logging**: Logs every stage into separate log files for observability
    
*   ☁️ **Redis Cloud Integration**: Maintains state and shared memory across agents
    
*   🔐 **Environment Protection**: Uses .env to securely handle API keys and secrets
    
*   🤖 **Groq API Integration** with Instructor for structured output
    
    *   Easily switchable to **OpenAI API** with just 3-4 lines of code
        
*   🧠 **Structured LLM Responses** via Instructor (also compatible with latest OpenAI models)
    

## 🚀 Example Flow

**User sends PDF**  
⬇️  
**Classifier Agent** detects → **Format**: PDF, **Intent**: Invoice  
⬇️  
**Text is extracted** from the PDF  
⬇️  
**Routed to appropriate agent** → Either JSON Agent or Email Agent depending on structure  
⬇️  
**Relevant fields extracted** → e.g., Vendor, Total, Invoice Date, Due Date  
⬇️  
**Outcome logged** in respective agent’s log file (`classifier_agent.log`, etc.)  
⬇️  
**Results stored** in **Redis shared memory** for traceability


💡 Use Cases
------------

*   Automated RFQ routing
    
*   Invoice data extraction
    
*   Complaint triage for support systems
    
*   Regulation parsing and metadata tagging
    
*   CRM-style structured output from emails
    

🛠️ Tech Stack
--------------

| Component         | Technology              |
|------------------|--------------------------|
| Language          | Python                  |
| Agents            | LLM-powered             |
| LLM API           | Groq (OpenAI-compatible)|
| Memory Store      | Redis (Cloud)           |
| Logging           | Python logging          |
| PDF Extraction    | `PyMuPDF`               |
| Structured Output | `Instructor`            |
| Env Management    | `python-dotenv`         |


## 📦 Getting Started

```bash
git clone https://github.com/sanil27022003/automatic-fiesta.git
cd automatic-fiesta
```

```
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

```
# Install dependencies
pip install -r requirements.txt
```

```
# Set up environment variables
cp .env.example .env
# Fill in your Groq/OpenAI keys and Redis credentials
```

```
# Run via CLI
python main.py --input "example.pdf"
python main.py --input '{"type": "invoice", "vendor": "ABC Corp", ... }'
python main.py --input "Subject: RFQ Request\nBody: We need 500 units..."
```

📁 Project Structure
--------------------
```
multi_agent_ai_system/
├── agents/
│   ├── classifier_agent.py       # Classifies input type and intent, routes to agents
│   ├── email_agent.py            # Extracts info from email-like text
│   └── json_agent.py             # Parses and validates structured JSON inputs
├── logs/
│   ├── classifier_agent.log      # Logs for classifier agent activities
│   ├── email_agent.log           # Logs for email agent activities
│   └── json_agent.log            # Logs for JSON agent activities
├── memory/
│   └── memory_module.py          # Redis-based shared memory for all agents
├── samples/
│   ├── sample_email.txt          # Sample input for email agent
│   ├── sample_json.json          # Sample input for JSON agent
│   ├── sample_pdf.pdf            # Example PDF file
│   └── sanil.pdf                 # Another example PDF file
├── main.py                       # CLI entry point that orchestrates input flow
├── README.md                     # Project documentation
└── requirements.txt
```

🧪 Future Improvements
----------------------
    
*   📎 Email integration (IMAP/Gmail API)
    
*   🪄 Web interface for visualization and testing
    
*   💬 Agent-to-agent dialogue for more complex reasoning chains
    
*   🗃️ Schema learning and auto-adaptation

🔐 Disclaimer
-------------

Make sure to manage API keys and secrets securely. Do **not** commit .env or sensitive data.

**Smart documents need smart agents.Let your AI do the reading. 📄→🤖→📊**
