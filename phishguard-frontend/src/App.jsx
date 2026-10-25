
import { useState } from "react";
import {
  ShieldCheck, ScanSearch, MessageSquareText, LayoutDashboard,
  ShieldAlert, LockKeyhole, ArrowUpRight, ArrowRight, Activity,
  Globe, Send, LoaderCircle, CheckCircle2, CircleHelp, Menu, X,
  ExternalLink, Sparkles
} from "lucide-react";
import "./App.css";
import ReactMarkdown from "react-markdown";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

export default function App() {
  const [activeTab, setActiveTab] = useState("scanner");
  const [url, setUrl] = useState("");
  const [scan, setScan] = useState(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [scanError, setScanError] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

  async function analyzeUrl(event) {
    event.preventDefault();
    setScan(null);
    setScanError("");

    if (!url.trim()) {
      setScanError("Enter a URL to begin your security analysis.");
      return;
    }

    setScanLoading(true);

    try {
      const response = await fetch(`${API}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed.");
      }

      setScan(data);
    } catch (error) {
      setScanError(
        error.message.includes("Failed to fetch")
          ? "Cannot connect to Flask. Check that the backend is running."
          : error.message
      );
    } finally {
      setScanLoading(false);
    }
  }

  async function sendQuestion(event, suggestedQuestion) {
    event?.preventDefault();

    const text = (suggestedQuestion || question).trim();

    if (!text || chatLoading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", content: text },
    ]);

    setQuestion("");
    setChatLoading(true);

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Assistant request failed.");
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            data.answer ||
            data.response ||
            "No answer returned.",
        },
      ]);
    } catch (error) {
      const message = error.message.includes("Failed to fetch")
        ? "I can't reach the Flask API. Check that the backend is running."
        : error.message;

      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: message },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  const navItems = [
    { id: "scanner", label: "URL Scanner", icon: ScanSearch },
    { id: "assistant", label: "AI Assistant", icon: MessageSquareText },
  ];

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <ShieldCheck size={25} strokeWidth={2.2} />
          </div>

          <div>
            <div className="brand-name">
              PhishGuard<span>AI</span>
            </div>
            <div className="brand-caption">
              THREAT INTELLIGENCE
            </div>
          </div>

          <button
            className="mobile-close"
            onClick={() => setMobileMenu(false)}
            aria-label="Close menu"
          >
            <X />
          </button>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav className="nav-list">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${
                activeTab === id ? "active" : ""
              }`}
              onClick={() => {
                setActiveTab(id);
                setMobileMenu(false);
              }}
            >
              <Icon size={19} />
              <span>{label}</span>
              {activeTab === id && (
                <span className="nav-active-dot" />
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-spacer" />

        <div className="sidebar-security">
          <div className="security-icon">
            <LockKeyhole size={19} />
          </div>
          <div className="security-title">Security first</div>
          <p>
            AI-assisted analysis. Always verify before taking action.
          </p>
          <div className="security-status">
            <span /> Local workspace
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="footer-dot" /> PHISHGUARD BUILD 1.0
        </div>
      </aside>

      {mobileMenu && (
        <button
          className="mobile-overlay"
          onClick={() => setMobileMenu(false)}
          aria-label="Close menu"
        />
      )}

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu-button"
              onClick={() => setMobileMenu(true)}
              aria-label="Open menu"
            >
              <Menu />
            </button>

            <LayoutDashboard size={16} />
            <span>Workspace</span>
            <span className="crumb-slash">/</span>
            <strong>
              {activeTab === "scanner"
                ? "URL Scanner"
                : "AI Security Assistant"}
            </strong>
          </div>

          <div className="topbar-right">
            <span className="environment">
              <span /> DEVELOPMENT
            </span>
            <div className="avatar">PG</div>
          </div>
        </header>

        <div className="page-content">
          {activeTab === "scanner" ? (
            <>
              <section className="page-heading">
                <div>
                  <div className="eyebrow">
                    <span /> THREAT DETECTION
                  </div>

                  <h1>
                    Know what’s <span>behind the link.</span>
                  </h1>

                  <p className="page-subtitle">
                    Analyze suspicious URLs with machine learning and
                    surface potential phishing indicators before you click.
                  </p>
                </div>

                <div className="heading-icon">
                  <ShieldCheck size={34} />
                </div>
              </section>

              <section className="scanner-card">
                <div className="card-topline">
                  <div className="card-icon">
                    <ScanSearch size={20} />
                  </div>

                  <div>
                    <h2>URL security analysis</h2>
                    <p>
                      Submit a URL for a machine-learning assessment.
                    </p>
                  </div>

                  <span className="model-tag">
                    <Activity size={13} /> RANDOM FOREST
                  </span>
                </div>

                <form onSubmit={analyzeUrl}>
                  <label htmlFor="url-input">Website URL</label>

                  <div className="url-input-wrap">
                    <Globe size={19} />

                    <input
                      id="url-input"
                      type="text"
                      value={url}
                      onChange={(event) => setUrl(event.target.value)}
                      placeholder="https://example.com"
                      autoComplete="url"
                    />

                    {url && (
                      <button
                        type="button"
                        className="clear-input"
                        onClick={() => {
                          setUrl("");
                          setScan(null);
                          setScanError("");
                        }}
                        aria-label="Clear URL"
                      >
                        <X size={17} />
                      </button>
                    )}
                  </div>

                  <div className="form-bottom">
                    <span className="input-hint">
                      <LockKeyhole size={13} />
                      Enter the full URL, including https://
                    </span>

                    <button
                      className="primary-button"
                      type="submit"
                      disabled={scanLoading}
                    >
                      {scanLoading ? (
                        <LoaderCircle className="spin" size={17} />
                      ) : (
                        <ScanSearch size={17} />
                      )}

                      {scanLoading ? "Analyzing..." : "Analyze URL"}

                      {!scanLoading && <ArrowRight size={16} />}
                    </button>
                  </div>
                </form>

                {scanError && (
                  <div className="inline-alert">
                    <CircleHelp size={17} />
                    <span>{scanError}</span>
                  </div>
                )}
              </section>

              {scan && (
                <section className="result-card">
                  <div className="result-heading">
                    <div>
                      <div className="eyebrow">ANALYSIS RESULT</div>
                      <h2>Scan summary</h2>
                    </div>

                    <span
                      className={`result-pill ${
                        String(
                          scan.prediction_text || scan.prediction || ""
                        )
                          .toLowerCase()
                          .includes("phishing")
                          ? "danger"
                          : "safe"
                      }`}
                    >
                      <span />
                      {scan.prediction_text ||
                        scan.prediction ||
                        "Analysis complete"}
                    </span>
                  </div>

                  <div className="result-url">
                    <Globe size={16} />
                    <span>{scan.submitted_url || url}</span>
                  </div>

                  <div className="result-metrics">
                    <div className="metric-box">
                      <span>Model confidence</span>
                      <strong>
                        {scan.confidence == null
                          ? "—"
                          : `${scan.confidence}%`}
                      </strong>
                    </div>

                    <div className="metric-box">
                      <span>Assessment</span>
                      <strong>
                        {scan.risk_level || scan.risk || "Completed"}
                      </strong>
                    </div>
                  </div>

                  {/* FIX: Always render the explanation section */}
                  <div className="reasons">
                    <h3>
                      <ShieldAlert size={17} />
                      Analysis Explanation
                    </h3>

                    {Array.isArray(scan.reasons) &&
                    scan.reasons.length > 0 ? (
                      <ul>
                        {scan.reasons.map((reason, index) => (
                          <li key={index}>
                            {typeof reason === "string"
                              ? reason
                              : JSON.stringify(reason)}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="no-indicators">
                        No rule-based suspicious URL indicators were
                        detected. This does not guarantee that the
                        website is safe.
                      </p>
                    )}
                  </div>

                  <p className="result-disclaimer">
                    Machine-learning output is an estimate, not a
                    guarantee that a website is safe or malicious.
                  </p>
                </section>
              )}

              {!scan && (
                <section className="below-grid">
                  <div className="info-card">
                    <div className="info-icon purple">
                      <Activity size={20} />
                    </div>
                    <h3>ML-powered detection</h3>
                    <p>
                      Evaluates URL characteristics using your trained
                      Random Forest classifier.
                    </p>
                    <button
                      onClick={() =>
                        document.getElementById("url-input")?.focus()
                      }
                    >
                      Scan a URL <ArrowUpRight size={15} />
                    </button>
                  </div>

                  <div className="info-card">
                    <div className="info-icon green">
                      <ShieldCheck size={20} />
                    </div>
                    <h3>Understand the risk</h3>
                    <p>
                      Review the prediction, confidence estimate, and
                      available detection indicators.
                    </p>
                    <span className="info-footnote">
                      <CheckCircle2 size={14} /> Explainable results
                    </span>
                  </div>

                  <div className="info-card">
                    <div className="info-icon blue">
                      <Sparkles size={20} />
                    </div>
                    <h3>Need security guidance?</h3>
                    <p>
                      Ask the AI assistant about phishing, prompt
                      injection, or web application security.
                    </p>
                    <button onClick={() => setActiveTab("assistant")}>
                      Ask PhishGuard <ArrowUpRight size={15} />
                    </button>
                  </div>
                </section>
              )}

              <div className="page-note">
                <LockKeyhole size={14} />
                Never enter passwords, access tokens, or other secrets
                into the scanner.
              </div>
            </>
          ) : (
            <>
              <section className="page-heading assistant-heading">
                <div>
                  <div className="eyebrow">
                    <span /> KNOWLEDGE ASSISTANT
                  </div>

                  <h1>
                    Your AI <span>security partner.</span>
                  </h1>

                  <p className="page-subtitle">
                    Explore cybersecurity concepts with answers grounded
                    in your security knowledge base.
                  </p>
                </div>

                <div className="heading-icon">
                  <MessageSquareText size={32} />
                </div>
              </section>

              <section className="chat-card">
                <div className="chat-card-header">
                  <div className="assistant-avatar">
                    <ShieldCheck size={22} />
                  </div>

                  <div className="chat-agent-info">
                    <h2>PhishGuard Assistant</h2>
                    <p>
                      <span /> Retrieval-augmented security guidance
                    </p>
                  </div>

                  <span className="powered-by">GROQ + PINECONE</span>
                </div>

                <div className="chat-body">
                  {messages.length === 0 ? (
                    <div className="chat-welcome">
                      <div className="welcome-symbol">
                        <Sparkles size={25} />
                      </div>

                      <h2>What would you like to understand?</h2>
                      <p>Ask a cybersecurity question to get started.</p>

                      <div className="suggestions">
                        {[
                          "How can I prevent prompt injection?",
                          "What is sensitive information disclosure?",
                          "Explain authentication vs authorization.",
                        ].map((item) => (
                          <button
                            key={item}
                            onClick={() => sendQuestion(null, item)}
                          >
                            {item}
                            <ArrowUpRight size={15} />
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="message-list">
                      {messages.map((message, index) => (
                        <div
                          key={index}
                          className={`message-row ${message.role}`}
                        >
                          {message.role === "assistant" && (
                            <div className="message-avatar">
                              <ShieldCheck size={16} />
                            </div>
                          )}

                          <div className="message-bubble">
                            <span className="message-label">
                              {message.role === "user"
                                ? "YOU"
                                : "PHISHGUARD AI"}
                            </span>
                            <div className="markdown-answer">
  <ReactMarkdown>
    {message.content
      .replace(/&#x20;/gi, " ")
      .replace(/\\\*/g, "*")
      .replace(/\\-/g, "-")}
  </ReactMarkdown>
</div>
                          </div>
                        </div>
                      ))}

                      {chatLoading && (
                        <div className="typing">
                          <LoaderCircle className="spin" size={16} />
                          Searching security references...
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <form
                  className="chat-composer"
                  onSubmit={(event) => sendQuestion(event)}
                >
                  <input
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask a cybersecurity question..."
                    maxLength={2000}
                  />

                  <button
                    type="submit"
                    disabled={chatLoading || !question.trim()}
                    aria-label="Send question"
                  >
                    {chatLoading ? (
                      <LoaderCircle className="spin" size={18} />
                    ) : (
                      <Send size={18} />
                    )}
                  </button>
                </form>

                <p className="chat-disclaimer">
                  AI-generated guidance may be incomplete. Verify
                  important security decisions against authoritative
                  documentation.
                </p>
              </section>
            </>
          )}

          <footer className="page-footer">
            <span>
              PHISHGUARD <span className="footer-separator">/</span>
              AI-ASSISTED SECURITY
            </span>

            <span>
              Built for safer browsing <ShieldCheck size={14} />
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}
