
import os
import pickle

import pandas as pd
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/dataset.csv"
MODEL_DIR = "model"
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Label mapping:
# -1 = Phishing -> 0
#  1 = Legitimate -> 1

SELECTED_FEATURES = [
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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_metrics(y_true, predictions, title):
    """Print classification metrics and confusion matrix."""
    print(f"\n{'=' * 55}")
    print(title)
    print("=" * 55)

    print(f"Accuracy: {accuracy_score(y_true, predictions):.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_true,
            predictions,
            labels=[0, 1],
            target_names=["Phishing", "Legitimate"],
            zero_division=0,
        )
    )

    print("Confusion matrix (rows = actual, columns = predicted):")
    print(confusion_matrix(y_true, predictions, labels=[0, 1]))


# ============================================================
# 1. LOAD AND VALIDATE DATASET
# ============================================================

df = pd.read_csv(DATASET_PATH)

if "index" in df.columns:
    df = df.drop(columns=["index"])

if "Result" not in df.columns:
    raise ValueError("Dataset must contain a 'Result' column.")

# Validate labels before mapping them.
original_labels = set(df["Result"].dropna().unique())
if not original_labels.issubset({-1, 1}):
    raise ValueError(
        f"Unexpected labels in Result: {original_labels}. "
        "Expected only -1 and 1."
    )

if df["Result"].isnull().any():
    raise ValueError("Dataset contains missing labels.")

df["Result"] = df["Result"].map({-1: 0, 1: 1})

if df.isnull().any().any():
    raise ValueError("Dataset contains missing values. Clean them first.")

X = df.drop(columns=["Result"])
y = df["Result"].astype(int)

missing_features = [
    feature for feature in SELECTED_FEATURES
    if feature not in X.columns
]

if missing_features:
    raise ValueError(f"Missing required features: {missing_features}")

X16 = X[SELECTED_FEATURES].copy()

print("=" * 55)
print("PHISHGUARD AI - MODEL TRAINING")
print("=" * 55)
print("Dataset shape:", df.shape)
print("Exact duplicate rows:", df.duplicated().sum())
print("Duplicate feature rows:", X.duplicated().sum())
print("Missing values:", df.isnull().sum().sum())
print("16-feature dataset shape:", X16.shape)

print("\nClass distribution:")
print(
    y.value_counts().rename(
        index={0: "Phishing", 1: "Legitimate"}
    )
)


# ============================================================
# 2. COMPARE MODELS USING ALL AVAILABLE FEATURES
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)

comparison_models = {
    "30-Feature Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=RANDOM_STATE,
    ),
    "30-Feature Decision Tree": DecisionTreeClassifier(
        random_state=RANDOM_STATE,
    ),
    "30-Feature Random Forest": RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}

print("\n" + "=" * 55)
print("30-FEATURE MODEL COMPARISON")
print("=" * 55)

for name, model in comparison_models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"{name}: {accuracy:.4f} ({accuracy:.2%})")


# Feature importance from the 30-feature Random Forest.
rf30 = comparison_models["30-Feature Random Forest"]

importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": rf30.feature_importances_,
}).sort_values("Importance", ascending=False)

print("\n30-feature Random Forest feature importance:")
print(importance.to_string(index=False))


# ============================================================
# 3. EVALUATE THE 16-FEATURE MODEL ON A RANDOM SPLIT
# ============================================================

X16_train, X16_test, y16_train, y16_test = train_test_split(
    X16,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)

rf16 = RandomForestClassifier(
    random_state=RANDOM_STATE,
    n_jobs=-1,
)

rf16.fit(X16_train, y16_train)
random_predictions = rf16.predict(X16_test)

print_metrics(
    y16_test,
    random_predictions,
    "16-FEATURE RANDOM-SPLIT EVALUATION",
)

print("Phishing precision:",
      f"{precision_score(y16_test, random_predictions, pos_label=0, zero_division=0):.4f}")

print("Phishing recall:",
      f"{recall_score(y16_test, random_predictions, pos_label=0, zero_division=0):.4f}")

print("Phishing F1-score:",
      f"{f1_score(y16_test, random_predictions, pos_label=0, zero_division=0):.4f}")


# ============================================================
# 4. GROUPED EVALUATION
# Keep identical 16-feature combinations in the same split.
# ============================================================

groups = X16.astype(str).agg("|".join, axis=1)

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
)

train_idx, test_idx = next(
    splitter.split(X16, y, groups=groups)
)

X_group_train = X16.iloc[train_idx]
X_group_test = X16.iloc[test_idx]
y_group_train = y.iloc[train_idx]
y_group_test = y.iloc[test_idx]

train_groups = set(groups.iloc[train_idx])
test_groups = set(groups.iloc[test_idx])
overlap = train_groups.intersection(test_groups)

print("\n" + "=" * 55)
print("GROUPED EVALUATION")
print("=" * 55)
print("Grouped training rows:", len(train_idx))
print("Grouped testing rows:", len(test_idx))
print("Overlapping feature groups:", len(overlap))

if overlap:
    raise RuntimeError("Feature groups overlap between train and test.")

rf16_grouped = RandomForestClassifier(
    random_state=RANDOM_STATE,
    n_jobs=-1,
)

rf16_grouped.fit(X_group_train, y_group_train)
grouped_predictions = rf16_grouped.predict(X_group_test)

print_metrics(
    y_group_test,
    grouped_predictions,
    "16-FEATURE GROUPED EVALUATION",
)


# ============================================================
# 5. TRAIN FINAL DEPLOYMENT MODEL ON ALL AVAILABLE DATA
# ============================================================

final_model = RandomForestClassifier(
    random_state=RANDOM_STATE,
    n_jobs=-1,
)

final_model.fit(X16, y)

os.makedirs(MODEL_DIR, exist_ok=True)

with open(os.path.join(MODEL_DIR, "model.pkl"), "wb") as file:
    pickle.dump(final_model, file)

with open(
    os.path.join(MODEL_DIR, "feature_names.pkl"), "wb"
) as file:
    pickle.dump(SELECTED_FEATURES, file)

print("\n" + "=" * 55)
print("TRAINING COMPLETED")
print("=" * 55)
print(f"Final model trained on {len(X16)} rows.")
print("Model saved to model/model.pkl")
print("Feature order saved to model/feature_names.pkl")
print("Evaluation metrics are based on held-out test sets.")
