import csv
from redact import tokenize_text, detokenize_text

text = "Reach me at diego.garcia@example.com or (425) 555-0163. Again: diego.garcia@example.com"
tokenized, table = tokenize_text(text)

# 1. Same value gets the same token; different kinds are numbered separately.
assert tokenized == "Reach me at [EMAIL_1] or [PHONE_1]. Again: [EMAIL_1]"
assert table == {"[EMAIL_1]": "diego.garcia@example.com", "[PHONE_1]": "(425) 555-0163"}

# 2. Round trip: tokenize then detokenize gives back the exact original.
assert detokenize_text(tokenized, table) == text

# 3. The Iowa story: the LLM answers using tokens, we put the real values back.
llm_answer = "Please email [EMAIL_1] to confirm, or call [PHONE_1]."
assert detokenize_text(llm_answer, table) == \
    "Please email diego.garcia@example.com to confirm, or call (425) 555-0163."

# 4. Every one of the 400 cases survives the round trip.
with open("data/cases.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    t, tab = tokenize_text(row["text"])
    assert detokenize_text(t, tab) == row["text"], row["case_id"]

print("all passed")