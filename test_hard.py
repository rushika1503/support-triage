import re
from redact import PATTERNS

# Each case: the text, and what a perfect finder SHOULD find in it.
# expected is a list of (TYPE, exact text). Use [] when nothing should be found.
CASES = [
    {"text": "Please call me on 425.555.0163 after 3pm.",
     "expected": [("PHONE", "425.555.0163")]},
    {"text": "Send the log to priya.shah@contoso.com.",
     "expected": [("EMAIL", "priya.shah@contoso.com")]},
    {"text": "Agent version 2.58.0.1 is installed on the server.",
     "expected": []},
      {"text": "I emailed support@contoso.com",
          "expected": []},
]

tp = fn = fp = 0
for i, case in enumerate(CASES, 1):
    found = []
    for kind, pattern in PATTERNS.items():
        for value in re.findall(pattern, case["text"]):
            found.append((kind, value))

    expected = case["expected"]
    missed = [x for x in expected if x not in found]
    false_alarms = [x for x in found if x not in expected]

    tp += len(expected) - len(missed)
    fn += len(missed)
    fp += len(false_alarms)

    if not missed and not false_alarms:
        print(f"Case {i}: OK")
    if missed:
        print(f"Case {i}: MISSED       {missed}")
    if false_alarms:
        print(f"Case {i}: FALSE ALARM  {false_alarms}")

print()
print(f"caught {tp}  missed {fn}  false alarms {fp}")
if tp + fn:
    print(f"recall    = {tp}/{tp + fn} = {tp / (tp + fn):.0%}")
if tp + fp:
    print(f"precision = {tp}/{tp + fp} = {tp / (tp + fp):.0%}")