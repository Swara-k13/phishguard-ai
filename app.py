from flask import Flask, render_template, request
import pickle
import numpy as np
import re

app = Flask(__name__)

model = pickle.load(open("model/model.pkl", "rb"))

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    url = request.form['url']
    url_lower = url.lower()

    features = [1] * 30
    risk_score = 0
    reasons = []


    if "@" in url:
        features[0] = -1
        risk_score += 1
        reasons.append("URL contains '@' symbol")

    if len(url) > 50:
        features[1] = -1
        risk_score += 1
        reasons.append("URL length is unusually long")

    if any(short in url_lower for short in ["bit.ly", "tinyurl", "goo.gl"]):
        features[2] = -1
        risk_score += 1
        reasons.append("Uses URL shortening service")

    if "//" in url[8:]:
        features[3] = -1
        risk_score += 1
        reasons.append("Double slash redirection detected")

    if url.count('.') > 4:
        features[4] = -1
        risk_score += 1
        reasons.append("Too many subdomains in URL")

 
    suspicious_keywords = [
        "login", "verify", "secure", "account",
        "update", "banking", "signin", "confirm"
    ]

    if any(kw in url_lower for kw in suspicious_keywords):
        features[5] = -1
        risk_score += 1
        reasons.append("Suspicious keyword detected")


    if url.startswith("http://"):
        features[6] = -1
        risk_score += 1
        reasons.append("Not using HTTPS (insecure connection)")



    brands = ["paypal", "google", "facebook", "amazon", "bank", "apple"]

    for brand in brands:
        if brand in url_lower and f"{brand}.com" not in url_lower:
            risk_score += 2   
            reasons.append(f"Possible impersonation of {brand}")
            break




    domain_match = re.findall(r"https?://([^/]+)", url_lower)
    if domain_match:
        domain = domain_match[0]
        if "-" in domain:
            risk_score += 1
            reasons.append("Hyphenated domain detected")

 

    final = np.array(features).reshape(1, -1)

    prediction = model.predict(final)
    prob = model.predict_proba(final)[0][1]
    confidence = round(prob * 100, 2)


    if prediction[0] == 0 or risk_score >= 2:
        result = "Phishing Website"
    else:
        result = "Legitimate Website"

    return render_template(
        'index.html',
        prediction_text=result,
        reasons=reasons,
        confidence=confidence,
        submitted_url=url
    )


if __name__ == "__main__":
    app.run(debug=True)