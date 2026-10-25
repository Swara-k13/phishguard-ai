
import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("PINECONE_API_KEY is missing from .env")

pc = Pinecone(api_key=api_key)
index = pc.Index("phishguard-rag")

ROOT = Path(__file__).parent
WSTG_DIR = (
    ROOT / "wstg-source" / "stable"
    / "4-Web_Application_Security_Testing"
    / "04-Authentication_Testing"
)
GENAI_DIR = ROOT / "genai-source" / "2026" / "final"

NAMESPACE = "cybersecurity"
MAX_CHARS = 1800


def split_into_chunks(text, max_chars=MAX_CHARS):
    paragraphs = [
        p.strip() for p in text.split("\n\n") if p.strip()
    ]
    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start:start + max_chars])

        elif len(current) + len(paragraph) + 2 <= max_chars:
            current = (
                f"{current}\n\n{paragraph}" if current else paragraph
            )
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def collect_documents(folder, source_name, base_url, excluded=None):
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    excluded = excluded or set()
    documents = []

    for file_path in sorted(folder.rglob("*.md")):
        if file_path.name.lower() in excluded:
            continue

        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = file_path.relative_to(folder).as_posix()
        source_path = f"{source_name}/{relative_path}"
        source_url = f"{base_url}/{relative_path}"

        for number, chunk in enumerate(split_into_chunks(content)):
            unique_text = f"{source_path}:{number}"
            stable_id = hashlib.sha256(
                unique_text.encode("utf-8")
            ).hexdigest()[:32]

            documents.append({
                "_id": f"pg-{stable_id}",
                "chunk_text": chunk,
                "title": file_path.stem.replace("_", " "),
                "source": file_path.name,
                "source_url": source_url,
            })

    return documents


wstg_documents = collect_documents(
    WSTG_DIR,
    "OWASP-WSTG",
    "https://github.com/OWASP/www-project-web-security-testing-guide/blob/master/stable/4-Web_Application_Security_Testing/04-Authentication_Testing",
    excluded={"readme.md", "index.md", "info.md"},
)

genai_documents = collect_documents(
    GENAI_DIR,
    "OWASP-GenAI-2026",
    "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final",
    excluded={"llm00_preface.md"},
)

documents = wstg_documents + genai_documents

if not documents:
    raise RuntimeError("No Markdown chunks were found.")

print(f"OWASP WSTG chunks: {len(wstg_documents)}")
print(f"GenAI 2026 chunks: {len(genai_documents)}")
print(f"Total chunks to upload: {len(documents)}")

for start in range(0, len(documents), 50):
    batch = documents[start:start + 50]
    index.documents.upsert(
        namespace=NAMESPACE,
        documents=batch,
    )
    print(f"Uploaded batch: {min(start + 50, len(documents))}/{len(documents)}")

print(f"\nIngestion complete. Namespace: {NAMESPACE}")
