import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle


df = pd.read_csv("data/dataset.csv")

df = df.drop("index", axis=1)
df['Result'] = df['Result'].map({-1: 0, 1: 1})
X = df.drop("Result", axis=1)
y = df["Result"]

print("Data prepared successfully!")
print("Shape:", X.shape)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# MODEL 1: Logistic Regression

lr = LogisticRegression(max_iter=1000)
lr.fit(X_train, y_train)
lr_pred = lr.predict(X_test)
lr_acc = accuracy_score(y_test, lr_pred)
print("Logistic Regression Accuracy:", lr_acc)


# MODEL 2: Decision Tree

dt = DecisionTreeClassifier()
dt.fit(X_train, y_train)
dt_pred = dt.predict(X_test)
dt_acc = accuracy_score(y_test, dt_pred)
print("Decision Tree Accuracy:", dt_acc)


# MODEL 3: Random Forest

rf = RandomForestClassifier()
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_acc = accuracy_score(y_test, rf_pred)
print("Random Forest Accuracy:", rf_acc)

best_model = rf
print("\nBest Model Selected: Random Forest")


pickle.dump(best_model, open("model/model.pkl", "wb"))

print("Model saved successfully!")