import sys
from pathlib import Path
from dotenv import load_dotenv

# Locate the RAG project relative to this file
RAG_PROJECT = Path(__file__).resolve().parent / "phishgurad-rag"

if not (RAG_PROJECT / "chatbot.py").exists():
    raise FileNotFoundError(
        f"chatbot.py not found at: {RAG_PROJECT / 'chatbot.py'}"
    )

# Make chatbot.py importable
sys.path.insert(0, str(RAG_PROJECT))

# Load environment variables if available
load_dotenv(RAG_PROJECT / ".env")

from chatbot import answer_question


def get_security_answer(question):
    """Return an answer from the PhishGuard RAG chatbot."""
    question = question.strip()

    if not question:
        return "Please enter a cybersecurity question."

    return answer_question(question)