import csv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import make_pipeline
from redact import redact_text

with open("data/cases.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

texts = [redact_text(r["text"]) for r in rows]
assigned = [r["assigned_team"] for r in rows]          # what we actually have in real life (noisy)
is_misrouted = [r["is_misrouted"] == "1" for r in rows]  # the answer key (only exists because the data is synthetic)

# Train on the noisy assigned_team labels. For each case, predict it with a model
# that did NOT see that case (5-fold cross-validation).
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
probs = cross_val_predict(model, texts, assigned, cv=5, method="predict_proba")
teams = np.array(sorted(set(assigned)))
guess = teams[probs.argmax(axis=1)]
confidence = probs.max(axis=1)

print("real misroutes in the data:", sum(is_misrouted))
print("confidence cutoff  flagged  caught  false alarms  recall  precision")
for cutoff in [0.3, 0.4, 0.5, 0.6, 0.7]:
    tp = fp = fn = 0
    for a, g, c, bad in zip(assigned, guess, confidence, is_misrouted):
        flagged = (g != a) and (c >= cutoff)
        if flagged and bad:
            tp += 1
        elif flagged and not bad:
            fp += 1
        elif bad and not flagged:
            fn += 1
    recall = tp / (tp + fn) if (tp + fn) else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    print(f"{cutoff:<18} {tp + fp:>7} {tp:>7} {fp:>13}  {recall:>6.2f}  {precision:>9.2f}")