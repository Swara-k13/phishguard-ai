from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
from urllib.parse import urlparse, urljoin
import ipaddress
import requests
from bs4 import BeautifulSoup
from rag_connector import get_security_answer
from flask_cors import CORS

import socket
from contextlib import contextmanager


def is_public_hostname(hostname):
    """Allow only hostnames resolving exclusively to public IP addresses."""
    if not hostname:
        return False

    normalized_hostname = hostname.rstrip(".").lower()
    if normalized_hostname == "localhost" or normalized_hostname.endswith(".localhost"):
        return False

    try:
        # If the input is already an IP address, validate it directly.
        addresses = [ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    hostname, None, type=socket.SOCK_STREAM
                )
            ]
        except (socket.gaierror, ValueError, OSError):
            return False

    return bool(addresses) and all(
        address.is_global for address in addresses
    )


@contextmanager
def safe_fetch(url):
    """
    Fetch a URL only when its hostname resolves to public IP addresses.
    Redirects are disabled so each destination must be validated separately.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing embedded credentials are not allowed.")

    try:
        port = parsed.port  # Validates malformed/out-of-range port syntax.
    except ValueError as exc:
        raise ValueError("URL contains an invalid port.") from exc

    if not is_public_hostname(parsed.hostname):
        raise ValueError("URL destination is not allowed.")

    response = requests.get(
        url,
        timeout=(3, 5),
        headers={"User-Agent": "Mozilla/5.0"},
        allow_redirects=False,
    )

    try:
        yield response
    finally:
        response.close()

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


# Load model and feature order.
# Only load pickle files that you created and trust.
with open("model/model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

with open("model/feature_names.pkl", "rb") as feature_file:
    feature_names = pickle.load(feature_file)

EXPECTED_FEATURE_NAMES = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "double_slash_redirecting",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "SSLfinal_State",
    "Domain_registeration_length",
    "Favicon",
    "port",
    "HTTPS_token",
    "Request_URL",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
]

if feature_names != EXPECTED_FEATURE_NAMES:
    raise ValueError(
        "feature_names.pkl does not match the expected 16-feature order. "
        "Regenerate it using the same order used to train the model."
    )

if not hasattr(model, "classes_") or 0 not in model.classes_ or 1 not in model.classes_:
    raise ValueError(
        "The model must contain classes 0 (phishing) and 1 (legitimate)."
    )


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
        if not hostname or parsed.username is not None or parsed.password is not None:
            return False

        # Only permit destinations that resolve exclusively to public IPs.
        # safe_fetch() repeats this check immediately before the HTTP request.
        if not is_public_hostname(hostname):
            return False

        # Reject malformed dotted hostnames / empty labels.
        if "." not in hostname:
            try:
                ipaddress.ip_address(hostname)
            except ValueError:
                return False

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
    """Check whether the URL hostname is a known URL shortener."""
    shorteners = {
        "bit.ly",
        "tinyurl.com",
        "goo.gl",
        "t.co",
        "ow.ly",
        "is.gd",
        "buff.ly",
        "adf.ly",
        "bit.do",
        "cutt.ly",
    }

    try:
        hostname = (urlparse(url).hostname or "").lower().rstrip(".")
        return -1 if hostname in shorteners else 1
    except (ValueError, TypeError):
        return 1


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
    # WHOIS registration age is not currently checked.
    # The training dataset only contains -1 and 1 for this feature.
    # This is a neutral fallback, not a verified registration result.
    return 1


def check_favicon(url):
    try:
        with safe_fetch(url) as response:
            if 300 <= response.status_code < 400:
                response.close()
                return 0

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

            page_domain = normalize_domain(urlparse(url).hostname)
            favicon_domain = normalize_domain(urlparse(favicon_url).hostname)

            if not favicon_domain:
                return 0
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


def normalize_domain(host):
    """Normalize hostnames by lowercasing and removing a leading www.

    Note: this is not a full registrable-domain comparison; subdomains such
    as cdn.example.com and example.com remain different hosts.
    """
    host = (host or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host

def check_request_url(url):
    try:
        with safe_fetch(url) as response:
            if 300 <= response.status_code < 400:
                response.close()
                return 0

            if response.status_code != 200:
                return 0

            soup = BeautifulSoup(response.text, "html.parser")
            page_domain = normalize_domain(urlparse(url).hostname)
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
                if resource_domain and normalize_domain(resource_domain) != page_domain:
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
        with safe_fetch(url) as response:
            if 300 <= response.status_code < 400:
                response.close()
                return 0

            soup = BeautifulSoup(response.text, "html.parser")
            page_domain = normalize_domain(urlparse(url).hostname)
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

                if anchor_domain and normalize_domain(anchor_domain) != page_domain:
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
        with safe_fetch(url) as response:
            if 300 <= response.status_code < 400:
                response.close()
                return 0

            if response.status_code != 200:
                return 0

            soup = BeautifulSoup(response.text, "html.parser")
            page_domain = normalize_domain(urlparse(url).hostname)
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

                if link_domain and normalize_domain(link_domain) != page_domain:
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
        with safe_fetch(url) as response:
            if 300 <= response.status_code < 400:
                response.close()
                return 0

            if response.status_code != 200:
                return 0

            soup = BeautifulSoup(response.text, "html.parser")
            page_domain = normalize_domain(urlparse(url).hostname)
            forms = soup.find_all("form")

            if not forms:
                return 1

            for form in forms:
                action = form.get("action", "").strip()

                if not action:
                    continue

                action_url = urljoin(url, action)
                action_domain = urlparse(action_url).hostname

                if action_domain and normalize_domain(action_domain) != page_domain:
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


INCONCLUSIVE_FEATURES = {
    "Domain_registeration_length": 8,
    "Favicon": 9,
    "Request_URL": 12,
    "URL_of_Anchor": 13,
    "Links_in_tags": 14,
    "SFH": 15,
}


def get_inconclusive_features(features):
    """
    Return feature names whose value is zero for further review.

    A zero does not always mean a check failed; feature meanings depend
    on the original dataset's encoding. Use this only as a diagnostic.
    """
    if len(features) != len(feature_names):
        return []

    return [
        name
        for name, index in INCONCLUSIVE_FEATURES.items()
        if features[index] == 0
    ]


def get_risk_indicators(features):
    reasons = []
    indicators = [
        (0, "URL contains an IP address"),
        (1, "URL is unusually long"),
        (2, "Uses a URL shortening service"),
        (3, "URL contains '@' symbol"),
        (4, "Double slash redirection detected"),
        (5, "Hyphenated domain detected"),
        (6, "Multiple subdomains detected"),
    ]

    for index, message in indicators:
        if features[index] == -1:
            reasons.append(message)

    return reasons


def analyze_url(url):
    """
    Extract features and classify a URL.

    Label mapping:
      0 = phishing
      1 = legitimate
    """
    # 1. Extract features
    features = extract_features(url)

    # 2. Validate feature count
    if len(features) != len(feature_names):
        raise ValueError(
            f"Expected {len(feature_names)} features, "
            f"but received {len(features)}."
        )

    # 3. Prepare features for the model
    final = pd.DataFrame([features], columns=feature_names)

    # 4. Get model prediction and probabilities
    predicted_class = int(model.predict(final)[0])
    probabilities = model.predict_proba(final)[0]
    classes = list(model.classes_)

    predicted_index = classes.index(predicted_class)
    phishing_index = classes.index(0)
    legitimate_index = classes.index(1)

    model_confidence = round(
        float(probabilities[predicted_index]) * 100, 2
    )
    phishing_probability = round(
        float(probabilities[phishing_index]) * 100, 2
    )
    legitimate_probability = round(
        float(probabilities[legitimate_index]) * 100, 2
    )

    # 5. Calculate heuristic risk indicators
    reasons = get_risk_indicators(features)
    risk_score = len(reasons)

    # 6. Final classification
    # The model determines the classification. Heuristic indicators are
    # reported separately as warnings so one indicator alone does not
    # automatically label a site as phishing.
    result = (
        "Phishing Website"
        if predicted_class == 0
        else "Legitimate Website"
    )
    decision_source = "model"

    # Risk level includes heuristic warnings but does not override the model.
    if predicted_class == 0:
        risk_level = "High Risk"
    elif risk_score > 0:
        risk_level = "Review Recommended"
    else:
        risk_level = "Low Risk"

    # 7. Return analysis
    return {
        "prediction_text": result,
        "confidence": model_confidence,
        "model_prediction": (
            "Phishing Website"
            if predicted_class == 0
            else "Legitimate Website"
        ),
        "phishing_probability": phishing_probability,
        "legitimate_probability": legitimate_probability,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "decision_source": decision_source,
        "reasons": reasons,
        "inconclusive_features": get_inconclusive_features(features),
        "features": features,
    }
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

    try:
        analysis = analyze_url(url)
        app.logger.info("URL analysis completed; extracted %s features.", len(analysis["features"]))

        return render_template(
            "index.html",
            prediction_text=analysis["prediction_text"],
            confidence=analysis["confidence"],
            phishing_probability=analysis["phishing_probability"],
            legitimate_probability=analysis["legitimate_probability"],
            model_prediction=analysis["model_prediction"],
            decision_source=analysis["decision_source"],
            risk_level=analysis["risk_level"],
            reasons=analysis["reasons"],
            inconclusive_features=analysis["inconclusive_features"],
            submitted_url=url
        )

    except Exception:
        app.logger.exception("HTML URL prediction failed")
        return render_template(
            "index.html",
            prediction_text="Analysis Error",
            confidence=None,
            reasons=["URL analysis failed. Please try again."],
            submitted_url=url
        ), 500


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
        analysis = analyze_url(url)

        # Do not expose the raw feature vector by default.
        analysis.pop("features", None)

        return jsonify({
            **analysis,
            "submitted_url": url,
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
    # Use debug=True only for local development, never for public deployment.
    app.run(debug=False)
