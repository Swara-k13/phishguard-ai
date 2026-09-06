import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle


# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv("data/dataset.csv")

# Remove index column
df = df.drop("index", axis=1)

# Convert Result:
# -1 = phishing → 0
#  1 = legitimate → 1
df["Result"] = df["Result"].map({-1: 0, 1: 1})

X = df.drop("Result", axis=1)
y = df["Result"]


# ============================================================
# SELECT 16 FEATURES FOR DEPLOYMENT
# ============================================================

selected_features = [
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
    "SFH"
]

X16 = df[selected_features]

print("16-feature dataset shape:", X16.shape)

print("Data prepared successfully!")
print("30-feature dataset shape:", X.shape)


# ============================================================
# 30-FEATURE MODEL EXPERIMENT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2
)


# ------------------------------------------------------------
# MODEL 1: LOGISTIC REGRESSION
# ------------------------------------------------------------

lr = LogisticRegression(max_iter=1000)

lr.fit(X_train, y_train)

lr_pred = lr.predict(X_test)

lr_acc = accuracy_score(y_test, lr_pred)

print("Logistic Regression Accuracy:", lr_acc)


# ------------------------------------------------------------
# MODEL 2: DECISION TREE
# ------------------------------------------------------------

dt = DecisionTreeClassifier()

dt.fit(X_train, y_train)

dt_pred = dt.predict(X_test)

dt_acc = accuracy_score(y_test, dt_pred)

print("Decision Tree Accuracy:", dt_acc)


# ------------------------------------------------------------
# MODEL 3: RANDOM FOREST
# ------------------------------------------------------------

rf = RandomForestClassifier()

rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)

rf_acc = accuracy_score(y_test, rf_pred)

print("Random Forest Accuracy:", rf_acc)


# ============================================================
# FEATURE IMPORTANCE OF 30-FEATURE MODEL
# ============================================================

feature_importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": rf.feature_importances_
})

feature_importance = feature_importance.sort_values(
    by="Importance",
    ascending=False
)

print("\n30-Feature Random Forest Feature Importance:")
print(feature_importance.to_string(index=False))


# ============================================================
# 16-FEATURE MODEL FOR DEPLOYMENT
# ============================================================

X16_train, X16_test, y16_train, y16_test = train_test_split(
    X16,
    y,
    test_size=0.2,
    random_state=42
)

rf16 = RandomForestClassifier(
    random_state=42
)

rf16.fit(X16_train, y16_train)

rf16_pred = rf16.predict(X16_test)

rf16_acc = accuracy_score(
    y16_test,
    rf16_pred
)


# ============================================================
# PRINT MODEL COMPARISON
# ============================================================

print("\n========================================")
print("MODEL COMPARISON")
print("========================================")

print("30-Feature Logistic Regression:",
      lr_acc)

print("30-Feature Decision Tree:",
      dt_acc)

print("30-Feature Random Forest:",
      rf_acc)

print("16-Feature Random Forest:",
      rf16_acc)


# ============================================================
# SAVE 16-FEATURE MODEL FOR FLASK
# ============================================================

pickle.dump(
    rf16,
    open("model/model.pkl", "wb")
)

# Save exact feature names and order
pickle.dump(
    selected_features,
    open("model/feature_names.pkl", "wb")
)

print("\n16-feature model saved successfully!")
print("Feature names saved successfully!")