import csv, json

with open("data/cases.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(len(rows), "cases")
row = rows[0]
print(row["text"])
print()
for item in json.loads(row["planted_pii"]):
    print(item["type"], "->", item["value"])