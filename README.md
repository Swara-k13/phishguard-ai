# 🛡️ PhishGuard AI

**AI-Powered Phishing Detection & RAG-Based Cybersecurity Assistant**

PhishGuard AI is a cybersecurity web application that combines machine learning-based phishing URL detection with a Retrieval-Augmented Generation (RAG) chatbot. It helps users identify potentially malicious URLs and explore cybersecurity concepts through an AI-powered assistant grounded in cybersecurity documentation.

🔗 **Live Demo:** [PhishGuard AI](https://phishguard-ai-ecru.vercel.app)  
💻 **GitHub Repository:** [Swara-k13/phishguard-ai](https://github.com/Swara-k13/phishguard-ai)

---

## 📌 Overview

Phishing attacks remain a major cybersecurity threat. PhishGuard AI analyzes URL-based features to classify potentially malicious websites and provides a conversational assistant for cybersecurity-related questions.

The application combines a **React frontend**, a **Flask backend**, a trained machine learning model, and a RAG pipeline using **Pinecone** for vector retrieval and the **Groq API** for answer generation.

The project explores how traditional machine learning and generative AI can work together in a cybersecurity application.

## 🚀 Features

### 🔍 Phishing URL Detection

- Analyzes submitted URLs using 16 selected URL-based features.
- Uses a trained Random Forest classifier to predict whether a website may be phishing or legitimate.
- Displays prediction results and model probability information.
- Performs URL validation before analysis.
- Provides a web interface for submitting URLs and viewing results.

### 🤖 RAG-Based Cybersecurity Assistant

- Answers cybersecurity-related questions using a retrieval-augmented approach.
- Uses Pinecone as the vector database to retrieve relevant cybersecurity information.
- Uses the Groq API to generate natural-language responses.
- Uses cybersecurity knowledge sources, including OWASP documentation.
- Supports questions about web security, phishing, and LLM security concepts.

### 🌐 Web Application

- React-based frontend with separate interfaces for URL detection and AI assistance.
- Flask backend exposing JSON API endpoints.
- Integration between the frontend, machine learning model, and RAG pipeline.
- Deployed frontend on Vercel and backend on Render.

## 🧠 Tech Stack

| Component | Technologies |
|---|---|
| Frontend | React, JavaScript, CSS |
| Backend | Python, Flask, Flask-CORS |
| Machine Learning | Scikit-learn, Pandas, NumPy |
| URL Analysis | Requests, Beautiful Soup |
| RAG Pipeline | Retrieval-Augmented Generation |
| Vector Database | Pinecone |
| LLM API | Groq API |
| Embeddings | Sentence Transformers, where used in the pipeline |
| Deployment | Vercel, Render |
| Version Control | Git, GitHub |

## 🏗️ System Architecture

```text
                     ┌────────────────────────┐
                     │     React Frontend     │
                     └────────────┬───────────┘
                                  │
                             HTTP / JSON
                                  │
                     ┌────────────▼───────────┐
                     │      Flask Backend     │
                     │        app.py          │
                     └────────────┬───────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼──────────┐      ┌─────────▼──────────┐
          │ URL Feature        │      │ RAG Connector      │
          │ Extraction         │      │ rag_connector.py   │
          └─────────┬──────────┘      └─────────┬──────────┘
                    │                           │
          ┌─────────▼──────────┐      ┌─────────▼──────────┐
          │ Random Forest      │      │ Pinecone           │
          │ Classifier         │      │ Vector Retrieval   │
          └─────────┬──────────┘      └─────────┬──────────┘
                    │                           │
                    │                 Retrieved cybersecurity
                    │                         context
                    │                           │
                    │                 ┌─────────▼──────────┐
                    │                 │ Groq API            │
                    │                 │ Answer Generation   │
                    │                 └─────────┬──────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                     ┌────────────▼───────────┐
                     │ Results to Frontend    │
                     └────────────────────────┘
```

### URL Detection Workflow

1. The user submits a URL through the React frontend.
2. The frontend sends the URL to the Flask backend using an HTTP POST request.
3. The backend extracts the URL-based features required by the trained model.
4. The features are passed to the Random Forest classifier.
5. The classifier predicts whether the URL is potentially phishing or legitimate.
6. The backend returns the prediction and associated probability information to the frontend.
7. The frontend displays the result to the user.

### RAG Chatbot Workflow

1. Cybersecurity documents are processed during knowledge-base ingestion.
2. Text is divided into chunks and converted into vector embeddings using the configured embedding model.
3. The embeddings are stored in Pinecone.
4. A user submits a cybersecurity question through the frontend.
5. The RAG pipeline retrieves relevant information from the vector database.
6. The retrieved context and user question are provided to the Groq-hosted language model.
7. The generated answer is returned to the frontend.

The RAG assistant is separate from the Random Forest prediction pipeline. It provides cybersecurity information rather than independently determining whether a submitted URL is malicious.

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

*This tree shows the main application components. The exact files and subdirectories may vary depending on the current repository contents.*

## ⚙️ Installation & Setup

### Prerequisites

- Python and pip
- Node.js and npm
- A Pinecone account and API key
- A Groq API key

### 1. Clone the repository

```bash
git clone https://github.com/Swara-k13/phishguard-ai.git
cd phishguard-ai
```

### 2. Create and activate a Python virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
venv\Scripts\activate.bat
```

### 3. Install backend dependencies

From the repository root:

```bash
pip install -r requirements.txt
```

Ensure that `requirements.txt` includes the packages required by the Flask application and the RAG integration.

### 4. Configure environment variables

Create the required `.env` file in the location expected by the RAG implementation. For the current project structure, the RAG credentials are configured in the RAG project's environment file.

Example:

```dotenv
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

Use the actual environment-variable names expected by the code. Do not commit real API keys or secret values to GitHub.

### 5. Configure the Pinecone knowledge base

- Create or select the Pinecone index used by the chatbot.
- Ensure that the index dimension matches the configured embedding model.
- Verify the index configuration and namespace used by the ingestion and retrieval scripts.
- Populate or refresh the knowledge base when necessary.

For example, if your existing ingestion script is configured for the `phishguard-rag` index:

```bash
python phishgurad-rag/ingest.py
```

Run ingestion only after configuring credentials and confirming that the script uses the intended index and schema. You do not need to rerun ingestion every time you start the application if the knowledge base is already populated.

### 6. Start the Flask backend

From the repository root:

```bash
python app.py
```

The local backend is typically available at:

```text
http://127.0.0.1:5000
```

Keep the backend terminal running while testing the frontend.

### 7. Start the React frontend

Open a second terminal:

```bash
cd phishguard-frontend
npm install
npm run dev
```

Open the local development URL displayed by Vite, commonly:

```text
http://localhost:5173
```

Ensure the frontend's API configuration points to the running Flask backend.

## 🔌 API Endpoints

The following endpoints are used by the application. The legacy form-based routes should be retained in this table only if they are present in the current backend implementation.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/predict` | POST | Analyze a submitted URL and return a prediction |
| `/api/chat` | POST | Answer a cybersecurity question using the RAG pipeline |
| `/predict` | POST | Legacy form-based phishing detection, if enabled |
| `/chat` | POST | Legacy form-based chat, if enabled |

### Example: Phishing Detection Request

**Endpoint:** `POST /api/predict`

```json
{
  "url": "https://example.com"
}
```

The backend processes the submitted URL and returns a response containing the prediction information defined by the API implementation.

### Example: Cybersecurity Chat Request

**Endpoint:** `POST /api/chat`

```json
{
  "question": "What is prompt injection?"
}
```

The backend passes the question to the RAG pipeline and returns the generated response.

*These are example request bodies. The exact response fields and error formats depend on the current backend implementation.*

## 🔐 Security Considerations

PhishGuard AI explores several security concepts, but it is an educational project rather than a fully hardened production security service.

- **API key protection:** Store Groq and Pinecone credentials in environment variables and keep them out of frontend code and version control.
- **Input validation:** Validate URLs and chatbot questions before processing.
- **Model limitations:** Treat classification results as risk indicators rather than guarantees that a website is safe or malicious.
- **RAG prompt injection:** Retrieved documents and user prompts can contain malicious instructions. Prompt-level safeguards alone do not guarantee protection.
- **Server-Side Request Forgery (SSRF):** Fetching user-supplied URLs can expose a backend to requests targeting internal services or private network addresses. Public deployment requires strict URL and IP validation, redirect checks, network restrictions, and appropriate timeouts.
- **Data privacy:** Avoid sending sensitive information to external APIs without considering data-handling requirements.
- **Operational security:** Consider rate limiting, safe error handling, logging, dependency updates, and automated security testing before broader deployment.

## 📸 Screenshots

### PhishGuard AI Interface

<img width="731" height="426" alt="Screenshot 2026-10-25 110012" src="https://github.com/user-attachments/assets/8cf6da81-7581-4e71-ae18-553dbabe5fc7" />

### Phishing Detection Results

<img width="937" height="431" alt="Screenshot 2026-10-25 105947" src="https://github.com/user-attachments/assets/563b5539-815d-4a2f-8370-a9f49294e9c8" />

### RAG-Based Cybersecurity Assistant

<img width="731" height="426" alt="Screenshot 2026-10-25 110012" src="https://github.com/user-attachments/assets/0a48ee59-6ffb-4fd5-85bc-1538a77ac0c0" />

## 🔮 Future Enhancements

- Evaluate the classifier on additional datasets and unseen URLs.
- Add automated tests for the prediction API and RAG pipeline.
- Improve URL-fetching protections to mitigate SSRF and unsafe redirects.
- Strengthen defenses against prompt injection and malicious retrieved content.
- Add source attribution to RAG-generated answers.
- Improve monitoring, error handling, and API rate limiting.
- Expand the cybersecurity knowledge base and evaluate retrieval quality.
- Measure model performance using appropriate metrics such as precision, recall, F1-score, and a confusion matrix.

## ⚠️ Disclaimer

PhishGuard AI is an educational cybersecurity project intended for learning and demonstration. Its predictions and AI-generated answers may be incomplete or inaccurate. A legitimate classification does not guarantee that a website is safe, and a phishing classification is not definitive proof of malicious intent. Do not use this application as the sole basis for security-critical decisions.

## 👩‍💻 Author

**Swara K**

GitHub: [@Swara-k13](https://github.com/Swara-k13)

---

⭐ If you find this project interesting, consider giving the repository a star!
