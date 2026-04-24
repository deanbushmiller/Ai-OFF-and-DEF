# Ai-OFF-and-DEF
for OReilly class tentative setup

💻 1. Hardware & Environment
Because we lack AI-optimized CPUs, we will use Python as the glue and APIs (OpenAI, Groq, or Anthropic) for the "intelligence" layer.

RAM: Minimum 8GB (16GB preferred to run local vector databases and IDEs simultaneously).

IDE: VS Code (highly recommended) with the Jupyter Extension installed.

Python: Version 3.10 or higher.

📦 2. Required Libraries (The "Cyber-AI" Stack)
Learners should create a dedicated virtual environment (python -m venv ai_cyber_env) and run the following installations before arrival:

The Offensive Toolkit
openai: For interacting with the LLM "brain."

garak: The standard LLM vulnerability scanner.

langchain & langchain-community: For building the RAG and Agent pipelines we will attack.

beautifulsoup4: For web-scraping exercises in the orchestration module.

The Defensive Toolkit
faiss-cpu: A library for efficient similarity search (crucial for RAG defense). Note: Ensure they install the -cpu version.

guardrails-ai or nemoguardrails: For the defense modules.

pyrit: Microsoft's Python Risk Identification Tool for the Red Teaming hour.

python-dotenv: To manage API keys securely.

Quick Install Command:

Bash
pip install openai garak langchain langchain-community beautifulsoup4 faiss-cpu guardrails-ai pyrit python-dotenv fastapi uvicorn
🔑 3. API & Access Setup
Since local inference is off the table, learners must have an API key.

Recommended: A Groq API Key (it is currently the fastest for live demos and offers a generous free tier for developers) or an OpenAI API Key with at least $5 of credit.

Task: Create a .env file in their project root:

Plaintext
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
📂 4. Pre-Loaded Datasets & Assets
To make the "Supply Chain" and "RAG" modules work, they need mock data to "poison."

The "Corporate Wiki" (RAG Exercise): A folder containing 5-10 PDF/Text files describing fake internal company policies (e.g., Travel_Policy.pdf, IT_Access_Rules.txt).

The "Malicious Model" (Supply Chain Exercise): A provided Python script that demonstrates a pickle.load() exploit (demonstrating why loading .pth or .bin files from untrusted sources is a critical risk).

The "Target Database": A simple SQLite database file or a CSV containing mock employee data for the "Agent Hijacking" module.

✅ 5. The "Smoke Test" (Pre-Class Verification)
Ask learners to run this snippet to ensure their environment is ready. If this works, they are ready for Hour 1.

Python
import openai
import faiss
import os
from dotenv import load_dotenv

load_dotenv()

# Test API Connection
try:
    # Example using OpenAI or Groq
    print("Checking API Connectivity...")
    # (Insert simple test call here)
    print("✅ API Connectivity: Success")
except Exception as e:
    print(f"❌ API Connectivity: Failed - {e}")

# Test Local Cyber Libraries
print(f"✅ FAISS version: {faiss.__version__} (CPU)")
Pro-Tip for the Instructor:
Since they aren't using AI CPUs, they might struggle with Docker. If any of your exercises require a database (like Vector DBs), recommend they use ChromaDB or FAISS in "In-Memory" mode. This keeps the local overhead extremely low while still providing a realistic "Enterprise" experience.
