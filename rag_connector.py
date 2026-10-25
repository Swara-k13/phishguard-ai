
import os
import sys
from pathlib import Path

# Path to your existing RAG project
RAG_PROJECT = Path.home() / "Desktop" / "phishgurad-rag"

if not RAG_PROJECT.exists():
    raise FileNotFoundError(
        f"RAG project folder not found: {RAG_PROJECT}"
    )

# Make chatbot.py importable
sys.path.insert(0, str(RAG_PROJECT))

# Load API keys from the RAG project's .env file
from dotenv import load_dotenv

load_dotenv(RAG_PROJECT / ".env")

# Import the existing RAG answer function
from chatbot import answer_question


def get_security_answer(question):
    """Return an answer from the PhishGuard RAG chatbot."""
    question = question.strip()

    if not question:
        return "Please enter a cybersecurity question."

    return answer_question(question)
