# 🛡️ PhishGuard AI

**AI-Powered Phishing Detection & RAG-Based Cybersecurity Assistant**

PhishGuard AI is a cybersecurity web application that combines machine learning-based phishing URL detection with a Retrieval-Augmented Generation (RAG) chatbot. It helps users identify potentially malicious URLs and explore cybersecurity concepts through an AI-powered assistant grounded in cybersecurity documentation.

## 📌 Overview

Phishing attacks remain a major cybersecurity threat. PhishGuard AI analyzes URL-based features to classify potentially malicious websites and provides a conversational assistant for cybersecurity-related questions.

The application combines a **React frontend**, a **Flask backend**, a trained machine learning model, and a RAG pipeline using **Pinecone** for vector retrieval and **Groq API** for answer generation.

## 🚀 Features

### 🔍 Phishing URL Detection
- Analyzes URLs using 16 selected URL-based features.
- Uses a trained machine learning classifier to predict whether a website may be phishing or legitimate.
- Displays prediction results and confidence information.
- Performs basic URL validation before analysis.

### 🤖 RAG-Based Cybersecurity Chatbot
- Answers cybersecurity-related questions using a retrieval-augmented approach.
- Uses Pinecone as the vector database for retrieving relevant knowledge.
- Uses Groq API to generate natural-language responses.
- Uses cybersecurity knowledge sources, including OWASP documentation.
- Supports questions about web security and LLM security topics.

### 🌐 Modern Web Application
- React-based frontend.
- Flask backend with JSON API endpoints.
- Separate interfaces for phishing detection and cybersecurity assistance.

## 🧠 Tech Stack

| Component | Technologies |
|---|---|
| Frontend | React, JavaScript, CSS |
| Backend | Python, Flask, Flask-CORS |
| Machine Learning | Scikit-learn, Pandas |
| URL Analysis | Requests, Beautiful Soup |
| RAG Pipeline | Retrieval-Augmented Generation |
| Vector Database | Pinecone |
| LLM API | Groq API |
| Embeddings | Sentence Transformers, where used |
| Version Control | Git, GitHub |

## 🏗️ Architecture

```text
                 ┌────────────────────────┐
                 │     React Frontend     │
                 └────────────┬───────────┘
                              │ HTTP / JSON
                 ┌────────────▼───────────┐
                 │      Flask Backend     │
                 │        app.py          │
                 └────────┬────────┬─────┘
                          │        │
                 ┌────────▼───┐  ┌─▼────────────────┐
                 │ Phishing   │  │ RAG Connector    │
                 │ Detection  │  │ rag_connector.py │
                 └────────────┘  └────────┬─────────┘
                                          │
                               ┌──────────▼─────────┐
                               │ Cybersecurity      │
                               │ Knowledge Retrieval│
                               └──────────┬─────────┘
                                          │
                               ┌──────────▼─────────┐
                               │ Pinecone + Groq API│
                               └────────────────────┘
```

## 📂 Project Structure

```text
phishguard-ai/
├── app.py
├── rag_connector.py
├── requirements.txt
├── .gitignore
├── model/
│   ├── model.pkl
│   └── feature_names.pkl
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── phishguard-frontend/
│   ├── package.json
│   ├── package-lock.json
│   └── src/
└── phishgurad-rag/
    ├── chatbot.py
    ├── ingest.py
    └── data/
        ├── llm_security.txt
        └── web_security.txt
```

*The structure above highlights the main application components. Additional frontend and documentation files may be present in the repository.*

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Swara-k13/phishguard-ai.git
cd phishguard-ai
```

### 2. Create and activate a Python virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the location expected by your RAG code and configure the required credentials:

```dotenv
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

Use the environment-variable names expected by your implementation. Never commit real API keys or secrets to GitHub.

### 5. Configure Pinecone

- Create or select your Pinecone index.
- Ensure its dimensions match the embedding model used by the ingestion pipeline.
- Run the ingestion script when you need to populate or refresh the knowledge base.

For example, if your setup uses the existing `phishguard-rag` index:

```bash
python phishgurad-rag/ingest.py
```

Run ingestion only after configuring the credentials and verifying that the script uses the intended index and schema.

### 6. Start the Flask backend

From the repository root:

```bash
python app.py
```

The backend runs at:

```text
http://127.0.0.1:5000
```

### 7. Start the React frontend

Open a second terminal:

```bash
cd phishguard-frontend
npm install
npm run dev
```

Open the local URL printed by the frontend development server, commonly:

```text
http://localhost:5173
```

Keep both the Flask backend and React development server running while testing the application.

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/predict` | POST | Analyze a submitted URL and return a prediction |
| `/api/chat` | POST | Answer a cybersecurity question using the RAG pipeline |
| `/predict` | POST | Legacy Flask form-based phishing detection |
| `/chat` | POST | Legacy Flask form-based cybersecurity chat |

### Example: Phishing Detection Request

```json
{
  "url": "https://example.com"
}
```

Send this JSON body to `/api/predict` using an HTTP POST request.

### Example: Chatbot Request

```json
{
  "question": "What is prompt injection?"
}
```

Send this JSON body to `/api/chat` using an HTTP POST request.

## 🔐 Security Considerations

- Keep API keys in environment variables; never expose them in frontend code.
- Do not commit `.env`, virtual environments, or unnecessary local files.
- Treat model predictions as indicators of risk, not guarantees of safety.
- Validate inputs and handle API errors appropriately.
- Verify the sources and retrieved context used by the RAG assistant.
- Review access controls, rate limits, and production deployment settings before exposing the application publicly.

## 📸 Screenshots

Add screenshots of the current React interface, phishing prediction results, and RAG chatbot responses here.

## 🔮 Future Enhancements

- Deploy the application with secure configuration and monitoring.
- Improve phishing detection using additional datasets and evaluation.
- Add richer source attribution to RAG responses.
- Expand the cybersecurity knowledge base.
- Add automated tests for the prediction API and RAG pipeline.
- Improve error handling, logging, and performance evaluation.

## ⚠️ Disclaimer

PhishGuard AI is an educational cybersecurity project. Its predictions and generated answers may be incomplete or inaccurate. Do not rely on this application as the sole means of determining whether a website is safe or making security-critical decisions.

## 👩‍💻 Author

**Swara K**

GitHub: [@Swara-k13](https://github.com/Swara-k13)

---

⭐ If you find this project interesting, consider giving the repository a star!
