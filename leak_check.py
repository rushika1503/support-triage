import csv, json
from collections import Counter
from redact import redact_text

with open("data/cases.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

planted_count = Counter()   # a dictionary that starts every count at 0
leaked_count = Counter()
cases_leaking = 0   

for row in rows:
    redacted = redact_text(row["text"])
    leaked_here = False
    for p in json.loads(row["planted_pii"]):
        planted_count[p["type"]] += 1
        if p["value"] in redacted:
            leaked_count[p["type"]] += 1
            if p["type"] != "NAME":
                leaked_here = True
    if leaked_here:
        cases_leaking += 1

for kind in planted_count:
    leaked = leaked_count[kind]
    print(f"{kind:<14} planted {planted_count[kind]:>3}  leaked {leaked:>3}  leak rate {leaked / planted_count[kind]:.0%}")
print()
print(f"Cases leaking something other than a name: {cases_leaking} of {len(rows)}")