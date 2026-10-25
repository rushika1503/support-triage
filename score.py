import csv, json
from redact import find_emails, find_api_keys, find_bearer_tokens,find_ips,find_phones


FINDERS = {
    "EMAIL": find_emails,
    "API_KEY": find_api_keys,
    "BEARER_TOKEN":find_bearer_tokens,
    "PHONE":find_phones,
    "IP_ADDRESS":find_ips
}
with open("data/cases.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def score(kind,finder):
    tp = fp = fn = 0
    for row in rows:
        planted = [p["value"] for p in json.loads(row["planted_pii"]) if p["type"] == kind]
        found = finder(row["text"])
        for value in planted:
            if value in found:
                tp += 1
            else:
                fn += 1

        for value in found:
            if value not in planted:
                fp += 1

        # TODO: update tp, fn and fp for this case
        #   tp: planted emails that are also in found
        #   fn: planted emails that are NOT in found (missed)
        #   fp: found emails that are NOT in planted (false alarms)
    return tp,fn,fp

for kind,finder in FINDERS.items():
    tp,fp,fn = score(kind,finder)
    recall = tp / (tp + fn)
    precision = tp / (tp + fp) if (tp + fp) else 0
    print(f"{kind:<14} planted {tp+fn:>3}  caught {tp:>3}  missed {fn:>3}  false alarms {fp:>3}  recall {recall:.2f}  precision {precision:.2f}")
    # TODO: print recall = tp / (tp + fn) and precision = tp / (tp + fp)