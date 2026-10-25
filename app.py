from flask import Flask, render_template, request
import pickle
import pandas as pd
from urllib.parse import urlparse, urljoin
import ipaddress
import requests
from bs4 import BeautifulSoup
from rag_connector import get_security_answer
from flask_cors import CORS
from flask import jsonify

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://phishguard-ai-ecru.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


# Load model and feature order
model = pickle.load(open("model/model.pkl", "rb"))
feature_names = pickle.load(open("model/feature_names.pkl", "rb"))


# ============================================================
# URL VALIDATION
# ============================================================

def is_valid_url(url):
    """Basic syntax validation; does not prove a URL is safe or reachable."""
    if not url:
        return False

    try:
        parsed = urlparse(url.strip())

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Accept localhost, IP addresses, or dotted hostnames.
        if hostname.lower() == "localhost":
            return True

        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass

        if "." not in hostname:
            return False

        # Reject empty domain labels and whitespace in hostname.
        labels = hostname.rstrip(".").split(".")
        if any(not label for label in labels):
            return False
        if any(any(ch.isspace() for ch in label) for label in labels):
            return False

        return True

    except (ValueError, TypeError):
        return False


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def has_ip_address(url):
    try:
        hostname = urlparse(url).hostname

        if hostname:
            ipaddress.ip_address(hostname)
            return -1

        return 1

    except (ValueError, TypeError):
        return 1


def get_url_length(url):
    length = len(url)

    if length < 54:
        return 1
    elif length <= 75:
        return 0
    else:
        return -1


def is_shortened_url(url):
    shorteners = [
        "bit.ly", "tinyurl.com", "goo.gl", "t.co",
        "ow.ly", "is.gd", "buff.ly", "adf.ly",
        "bit.do", "cutt.ly"
    ]

    url_lower = url.lower()
    return -1 if any(s in url_lower for s in shorteners) else 1


def has_at_symbol(url):
    return -1 if "@" in url else 1


def has_double_slash(url):
    return -1 if "//" in url[8:] else 1


def has_prefix_suffix(url):
    try:
        hostname = urlparse(url).hostname

        if hostname and "-" in hostname:
            return -1

        return 1

    except Exception:
        return 1


def check_subdomain(url):
    try:
        hostname = urlparse(url).hostname

        if not hostname:
            return 1

        try:
            ipaddress.ip_address(hostname)
            return 1
        except ValueError:
            pass

        parts = hostname.split(".")

        if len(parts) <= 2:
            return 1
        elif len(parts) == 3:
            return 0
        else:
            return -1

    except Exception:
        return 1


def check_ssl_state(url):
    return 1 if urlparse(url).scheme == "https" else -1


def check_domain_registration(url):
    try:
        hostname = urlparse(url).hostname

        if not hostname:
            return 0

        # WHOIS information is not available locally.
        return 0

    except Exception:
        return 0


def check_favicon(url):
    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200:
            return 0

        soup = BeautifulSoup(response.text, "html.parser")

        favicon = soup.find(
            "link",
            rel=lambda value: value and any(
                "icon" in item.lower() for item in value
            )
        )

        if not favicon or not favicon.get("href"):
            return 0

        favicon_url = urljoin(url, favicon["href"])

        page_domain = urlparse(url).hostname
        favicon_domain = urlparse(favicon_url).hostname

        return 1 if favicon_domain == page_domain else -1

    except Exception:
        return 0


def check_port(url):
    try:
        port = urlparse(url).port

        if port is None or port in [80, 443]:
            return 1

        return -1

    except Exception:
        return 0


def check_https_token(url):
    try:
        hostname = urlparse(url).hostname

        if hostname and "https" in hostname.lower():
            return -1

        return 1

    except Exception:
        return 1


def check_request_url(url):
    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200:
            return 0

        soup = BeautifulSoup(response.text, "html.parser")
        page_domain = urlparse(url).hostname

        resources = []
        resources.extend(soup.find_all("img", src=True))
        resources.extend(soup.find_all("script", src=True))
        resources.extend(
            soup.find_all(
                "link",
                href=True,
                rel=lambda value:
                    value and "stylesheet" in value
            )
        )
        resources.extend(soup.find_all("audio", src=True))
        resources.extend(soup.find_all("video", src=True))

        if not resources:
            return 1

        external_count = 0

        for resource in resources:
            resource_url = resource.get("src") or resource.get("href")
            if not resource_url:
                continue

            absolute_url = urljoin(url, resource_url)
            resource_domain = urlparse(absolute_url).hostname

            if resource_domain and resource_domain != page_domain:
                external_count += 1

        ratio = external_count / len(resources)

        if ratio < 0.22:
            return 1
        elif ratio <= 0.61:
            return 0
        else:
            return -1

    except Exception:
        return 0


def check_url_of_anchor(url):
    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200:
            return 0

        soup = BeautifulSoup(response.text, "html.parser")
        page_domain = urlparse(url).hostname
        anchors = soup.find_all("a", href=True)

        if not anchors:
            return 1

        external_count = 0

        for anchor in anchors:
            href = anchor.get("href", "").strip()

            if not href or href.startswith("#"):
                continue

            if href.lower().startswith(("javascript:", "mailto:")):
                continue

            absolute_url = urljoin(url, href)
            anchor_domain = urlparse(absolute_url).hostname

            if anchor_domain and anchor_domain != page_domain:
                external_count += 1

        ratio = external_count / len(anchors)

        if ratio < 0.31:
            return 1
        elif ratio <= 0.67:
            return 0
        else:
            return -1

    except Exception:
        return 0


def check_links_in_tags(url):
    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200:
            return 0

        soup = BeautifulSoup(response.text, "html.parser")
        page_domain = urlparse(url).hostname
        tag_links = []

        for tag in soup.find_all("link", href=True):
            tag_links.append(tag["href"])

        for tag in soup.find_all("script", src=True):
            tag_links.append(tag["src"])

        for tag in soup.find_all("meta", content=True):
            content = tag.get("content", "")

            if content.startswith(("http://", "https://")):
                tag_links.append(content)

        if not tag_links:
            return 1

        external_count = 0

        for link in tag_links:
            absolute_url = urljoin(url, link)
            link_domain = urlparse(absolute_url).hostname

            if link_domain and link_domain != page_domain:
                external_count += 1

        ratio = external_count / len(tag_links)

        if ratio < 0.17:
            return 1
        elif ratio <= 0.81:
            return 0
        else:
            return -1

    except Exception:
        return 0


def check_sfh(url):
    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200:
            return 0

        soup = BeautifulSoup(response.text, "html.parser")
        page_domain = urlparse(url).hostname
        forms = soup.find_all("form")

        if not forms:
            return 1

        for form in forms:
            action = form.get("action", "").strip()

            if not action:
                continue

            action_url = urljoin(url, action)
            action_domain = urlparse(action_url).hostname

            if action_domain and action_domain != page_domain:
                return -1

        return 1

    except Exception:
        return 0


# ============================================================
# CREATE 16-FEATURE VECTOR
# ============================================================

def extract_features(url):
    features = [
        has_ip_address(url),
        get_url_length(url),
        is_shortened_url(url),
        has_at_symbol(url),
        has_double_slash(url),
        has_prefix_suffix(url),
        check_subdomain(url),
        check_ssl_state(url),
        check_domain_registration(url),
        check_favicon(url),
        check_port(url),
        check_https_token(url),
        check_request_url(url),
        check_url_of_anchor(url),
        check_links_in_tags(url),
        check_sfh(url)
    ]

    return features


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    url = request.form.get("url", "").strip()

    if not url:
        return render_template(
            "index.html",
            prediction_text="",
            confidence=None,
            reasons=[],
            submitted_url="",
            error="Please enter a URL."
        )

    # Validate before feature extraction and model prediction.
    if not is_valid_url(url):
        return render_template(
            "index.html",
            prediction_text="Invalid URL",
            confidence=None,
            reasons=[
                "Enter a URL starting with http:// or https://.",
                "Example: https://www.google.com"
            ],
            submitted_url=url
        )

    features = extract_features(url)

    print("URL:", url)
    print("FEATURES:", features)

    if len(features) != 16:
        return render_template(
            "index.html",
            prediction_text="Feature Extraction Error",
            confidence=0,
            reasons=[
                "The feature extractor did not generate exactly 16 features."
            ],
            submitted_url=url
        )

    # Rule-based explanation
    risk_score = 0
    reasons = []

    if features[0] == -1:
        risk_score += 1
        reasons.append("URL contains an IP address")

    if features[1] == -1:
        risk_score += 1
        reasons.append("URL is unusually long")

    if features[2] == -1:
        risk_score += 1
        reasons.append("Uses a URL shortening service")

    if features[3] == -1:
        risk_score += 1
        reasons.append("URL contains '@' symbol")

    if features[4] == -1:
        risk_score += 1
        reasons.append("Double slash redirection detected")

    if features[5] == -1:
        risk_score += 1
        reasons.append("Hyphenated domain detected")

    if features[6] == -1:
        risk_score += 1
        reasons.append("Multiple subdomains detected")

    # ML prediction
    final = pd.DataFrame([features], columns=feature_names)

    prediction = model.predict(final)
    probability = model.predict_proba(final)[0][1]
    confidence = round(probability * 100, 2)

    if prediction[0] == 0 or risk_score >= 1:
        result = "Phishing Website"
    else:
        result = "Legitimate Website"

    return render_template(
        "index.html",
        prediction_text=result,
        confidence=confidence,
        reasons=reasons,
        submitted_url=url
    )

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()

    if not url:
        return jsonify({"error": "Please enter a URL."}), 400

    if not is_valid_url(url):
        return jsonify({
            "error": "Invalid URL. Enter a valid HTTP or HTTPS URL."
        }), 400

    try:
        features = extract_features(url)

        if len(features) != 16:
            return jsonify({
                "error": "Feature extraction failed."
            }), 500

        final = pd.DataFrame([features], columns=feature_names)
        prediction = model.predict(final)
        probability = model.predict_proba(final)[0][1]
        confidence = round(float(probability) * 100, 2)

        risk_score = 0
        reasons = []

        if features[0] == -1:
            risk_score += 1
            reasons.append("URL contains an IP address")
        if features[1] == -1:
            risk_score += 1
            reasons.append("URL is unusually long")
        if features[2] == -1:
            risk_score += 1
            reasons.append("Uses a URL shortening service")
        if features[3] == -1:
            risk_score += 1
            reasons.append("URL contains '@' symbol")
        if features[4] == -1:
            risk_score += 1
            reasons.append("Double slash redirection detected")
        if features[5] == -1:
            risk_score += 1
            reasons.append("Hyphenated domain detected")
        if features[6] == -1:
            risk_score += 1
            reasons.append("Multiple subdomains detected")

        if prediction[0] == 0 or risk_score >= 1:
            result = "Phishing Website"
        else:
            result = "Legitimate Website"

        return jsonify({
            "prediction_text": result,
            "confidence": confidence,
            "risk_level": "High Risk" if "Phishing" in result else "Low Risk",
            "reasons": reasons,
            "submitted_url": url
        })

    except Exception:
        app.logger.exception("URL prediction API failed")
        return jsonify({
            "error": "URL analysis failed. Please try again."
        }), 500


@app.route("/chat", methods=["POST"])
def chat():
    question = request.form.get("question", "").strip()

    if not question:
        return render_template(
            "index.html",
            chat_answer="Please enter a cybersecurity question."
        )

    try:
        answer = get_security_answer(question)

        return render_template(
            "index.html",
            chat_question=question,
            chat_answer=answer
        )

    except Exception:
        app.logger.exception("RAG chatbot request failed")

        return render_template(
            "index.html",
            chat_question=question,
            chat_answer=(
                "The cybersecurity assistant is temporarily unavailable. "
                "Please try again."
            )
        )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()

    if not question:
        return jsonify({
            "error": "Please enter a cybersecurity question."
        }), 400

    if len(question) > 2000:
        return jsonify({
            "error": "Your question is too long."
        }), 400

    try:
        answer = get_security_answer(question)
        return jsonify({"answer": answer})

    except Exception:
        app.logger.exception("RAG chatbot API failed")
        return jsonify({
            "error": "The security assistant is temporarily unavailable. Please try again."
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
