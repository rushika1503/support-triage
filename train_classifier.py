import csv
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from redact import redact_text

with open("data/cases.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

texts = [redact_text(r["text"]) for r in rows]
labels = [r["true_team"] for r in rows]

X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42, stratify=labels
)

# Learn the vocabulary from the TRAINING text only, then apply it to the test text.
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

pred = model.predict(X_test_vec)
print("accuracy:", round(accuracy_score(y_test, pred), 2))
print()
print(classification_report(y_test, pred, digits=2))
print("confusion matrix (rows = true team, columns = predicted team):")
print(model.classes_.tolist())
print(confusion_matrix(y_test, pred, labels=model.classes_))

# Which test cases did it get wrong, and how sure was it?
probs = model.predict_proba(X_test_vec)
print()
for text, true_team, guess, row_probs in zip(X_test, y_test, pred, probs):
    if true_team != guess:
        print("TRUE:", true_team, "| PREDICTED:", guess, "| confidence:", round(row_probs.max(), 2))
        print(text)

# What happens if we only trust the model above a confidence cutoff?
print()
print("threshold  answered  of 80  accuracy on answered")
for threshold in [0.0, 0.3, 0.4, 0.5, 0.6, 0.7]:
    answered = correct = 0
    for true_team, guess, row_probs in zip(y_test, pred, probs):
        if row_probs.max() >= threshold:
            answered += 1
            if true_team == guess:
                correct += 1
    accuracy = correct / answered if answered else 0
    print(f"{threshold:<10} {answered:>8} {len(y_test):>6}  {accuracy:.2f}")