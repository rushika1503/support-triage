"""
generate_data.py  --  Step 1 of the Support Case Triage Toolkit

What this does
--------------
Creates a fake-but-realistic dataset of support cases (a CSV file) that every
later step uses:
  * redaction   -> needs case text that contains PII and secrets
  * routing     -> needs cases labeled with the correct team
  * KQL / ADX   -> needs timestamps, products, and resolution times
  * evaluation  -> needs an answer key to measure against

Everything here is fake. Only Python's standard library is used, so there is
nothing to install.

Run:
    python generate_data.py                  (400 cases, seed 42)
    python generate_data.py --n 600 --seed 7
"""
import argparse
import csv
import json
import math
import os
import random
import string
from collections import Counter
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# 1. The "world" we are simulating
# ---------------------------------------------------------------------------

# Support teams and how common each one is. The weights are unequal on
# purpose: real support data is imbalanced, and that affects the classifier.
TEAMS = {
    "Azure": 0.24,
    "Microsoft 365": 0.22,
    "Identity": 0.16,
    "Endpoint": 0.14,
    "Power Platform": 0.12,
    "Dynamics 365": 0.12,
}

# When a case is misrouted it usually lands on a team that sounds similar.
CONFUSABLE = {
    "Azure": ["Identity", "Endpoint"],
    "Microsoft 365": ["Identity", "Endpoint"],
    "Identity": ["Microsoft 365", "Azure"],
    "Endpoint": ["Microsoft 365", "Azure"],
    "Power Platform": ["Dynamics 365", "Microsoft 365"],
    "Dynamics 365": ["Power Platform", "Microsoft 365"],
}
MISROUTE_RATE = 0.05  # about 5% of cases go to the wrong team (label noise)

# Severity 1 = most urgent. Typical hours to resolve by severity.
SEVERITY_WEIGHTS = {1: 0.05, 2: 0.20, 3: 0.50, 4: 0.25}
MEAN_HOURS = {1: 6, 2: 14, 3: 30, 4: 52}
TEAM_SPEED = {
    "Azure": 1.0, "Microsoft 365": 0.9, "Identity": 0.8,
    "Endpoint": 1.0, "Power Platform": 1.1, "Dynamics 365": 1.3,
}

# Each team has a few (product, issue template) pairs. The {placeholders}
# are filled in with random fake values, so no two cases read the same.
ISSUES = {
    "Azure": [
        ("Virtual Machines", "My VM {res} in {region} will not start and shows error {err} after the last resize."),
        ("Storage", "Uploads to storage account {res} are failing with {err} since this morning."),
        ("App Service", "Our web app {res} returns HTTP 502 intermittently and the deployment log shows {err}."),
        ("Kubernetes", "Pods in cluster {res} are stuck in Pending and the node pool in {region} reports {err}."),
        ("Azure SQL", "Queries against database {res} time out under load with {err}."),
    ],
    "Microsoft 365": [
        ("Exchange Online", "A mailbox is not receiving external email and the message trace shows {err}."),
        ("Teams", "Teams meetings drop audio after about ten minutes for several users and the client log shows {err}."),
        ("SharePoint", "Site {res} shows access denied for a whole group after a permission change, correlation error {err}."),
        ("OneDrive", "OneDrive sync is stuck at processing changes on several laptops with error {err}."),
        ("Outlook", "Outlook keeps asking for a password and shows {err} when opening shared mailboxes."),
    ],
    "Identity": [
        ("Sign-in", "Users cannot sign in and see {err} after we turned on conditional access."),
        ("MFA", "MFA prompts are not arriving for some users and the sign-in log shows {err}."),
        ("App registration", "Our app registration {res} fails token requests with {err}."),
        ("Directory sync", "Directory sync with on-premises has not completed for two days and the sync service reports {err}."),
        ("Password reset", "Self-service password reset sends users to a blank page with error {err}."),
    ],
    "Endpoint": [
        ("Intune enrollment", "New laptops fail to enroll and the company portal shows {err}."),
        ("Compliance policy", "Devices are marked non-compliant even though they meet the policy, status {err}."),
        ("App deployment", "A required app is stuck on installing on many devices and the log shows {err}."),
        ("Defender", "Defender for Endpoint shows devices as inactive although they are online, sensor error {err}."),
        ("Windows Update", "A feature update fails on a subset of devices with {err} and rolls back."),
    ],
    "Power Platform": [
        ("Power Automate", "A flow {res} that ran daily now fails at the HTTP step with {err}."),
        ("Power Apps", "Our canvas app is very slow to open and shows {err} when loading the data source."),
        ("Dataverse", "Importing a solution into the production environment fails with {err}."),
        ("Power BI", "Scheduled refresh for dataset {res} fails with {err} since the gateway update."),
        ("Connectors", "The custom connector returns {err} for every call after we rotated credentials."),
    ],
    "Dynamics 365": [
        ("Sales", "Opportunity records are not saving and users see {err} in the form."),
        ("Customer Service", "Cases are not being routed by the queue rule and the workflow log shows {err}."),
        ("Finance", "Posting a journal fails with {err} for one legal entity."),
        ("Field Service", "Work orders are not syncing to the mobile app, error {err}."),
        ("Marketing", "The customer journey stops at the email step with {err}."),
    ],
}

REGIONS = ["westus2", "eastus", "northeurope", "centralindia", "uksouth"]
WHEN = [
    "It started this morning.",
    "This began after last night's maintenance window.",
    "It has been happening for about three days.",
    "It started right after a configuration change.",
    "We noticed it yesterday afternoon.",
]
TRIED = [
    "We already restarted the service.",
    "We tried again from a different network.",
    "A colleague reproduced it on another machine.",
    "We rolled back the last change but it did not help.",
    "Nothing has changed on our side as far as we know.",
]
IMPACT = [
    "This is blocking our finance team.",
    "About {n} users are affected.",
    "This affects a customer-facing system.",
    "It is not urgent but it is annoying.",
]
RESOURCE_PREFIXES = [
    "vm-prod", "stgacct", "app-orders", "aks-core", "sqldb-billing",
    "flow-invoice", "hr-portal", "sales-hub", "gw-main",
]

# Busier during working hours (index = hour of day, 0-23).
HOUR_WEIGHTS = [1] * 7 + [2, 5, 8, 9, 8, 6, 8, 9, 8, 6, 4, 2] + [1] * 5

# ---------------------------------------------------------------------------
# 2. Fake personal data (the things the redaction step must find later)
# ---------------------------------------------------------------------------

FIRST = ["Alex", "Priya", "Maria", "Chen", "Omar", "Fatima", "Liam", "Sofia",
         "Ravi", "Hannah", "Diego", "Aisha", "Noah", "Mei", "Lucas", "Zara"]
LAST = ["Johnson", "Patel", "Garcia", "Nguyen", "Khan", "Silva", "Brown", "Kim",
        "Singh", "Martin", "Lopez", "Ivanov", "Clark", "Ahmed", "Rossi", "Walker"]
# Fictional or reserved domains, so these can never be real addresses.
DOMAINS = ["contoso.com", "fabrikam.com", "example.com"]


def fake_phone(rng):
    """555-01xx numbers are reserved for fiction, so none of these are real."""
    area = rng.choice([206, 425, 360, 509])
    line = f"{rng.randint(0, 99):02d}"
    style = rng.choice(["paren", "dash", "intl"])
    if style == "paren":
        return f"({area}) 555-01{line}"
    if style == "dash":
        return f"{area}-555-01{line}"
    return f"+1 {area} 555 01{line}"


def fake_ip(rng):
    """Documentation-only IP ranges (TEST-NET), never routable."""
    prefix = rng.choice(["192.0.2", "198.51.100", "203.0.113"])
    return f"{prefix}.{rng.randint(1, 254)}"


def fake_api_key(rng):
    """Obviously fake prefix so GitHub secret scanning will not flag the CSV."""
    return "demo_key_" + "".join(rng.choices("0123456789abcdef", k=32))


def fake_bearer(rng):
    alphabet = string.ascii_letters + string.digits + "-_"
    return "Bearer " + "".join(rng.choices(alphabet, k=40))


def fake_error(rng):
    style = rng.choice(["hex", "aadsts", "plain"])
    if style == "hex":
        return "0x8007" + "".join(rng.choices("0123456789ABCDEF", k=4))
    if style == "aadsts":
        return f"AADSTS{rng.randint(10000, 99999)}"
    return f"ERR-{rng.randint(1000, 9999)}"


def fake_resource(rng):
    return f"{rng.choice(RESOURCE_PREFIXES)}-{rng.randint(1, 99):02d}"


def plant(pii_log, kind, value):
    """Record a planted value in the answer key and hand it back for the text."""
    pii_log.append({"type": kind, "value": value})
    return value


# ---------------------------------------------------------------------------
# 3. Building one case
# ---------------------------------------------------------------------------

def build_text(rng, team, pii_log):
    """Return (text, product, severity) for one case, logging planted PII."""
    product, template = rng.choice(ISSUES[team])
    severity = rng.choices(
        list(SEVERITY_WEIGHTS), weights=list(SEVERITY_WEIGHTS.values())
    )[0]

    parts = []
    if severity <= 2 and rng.random() < 0.5:
        parts.append("URGENT:")
    parts.append(template.format(
        res=fake_resource(rng), region=rng.choice(REGIONS), err=fake_error(rng)
    ))
    parts.append(rng.choice(WHEN))
    if rng.random() < 0.6:
        parts.append(rng.choice(TRIED))
    if rng.random() < 0.7:
        parts.append(rng.choice(IMPACT).format(n=rng.choice([5, 12, 40, 150, 600])))

    # --- planted personal data -------------------------------------------
    first, last = rng.choice(FIRST), rng.choice(LAST)
    email = f"{first.lower()}.{last.lower()}@{rng.choice(DOMAINS)}"
    phone = fake_phone(rng)

    r = rng.random()
    if r < 0.40:
        found = plant(pii_log, "EMAIL", email)
        parts.append(f"You can reach me at {found}.")
    elif r < 0.65:
        e = plant(pii_log, "EMAIL", email)
        p = plant(pii_log, "PHONE", phone)
        parts.append(f"Reach me at {e} or {p}.")
    elif r < 0.85:
        p = plant(pii_log, "PHONE", phone)
        parts.append(f"Call me on {p}.")
    # else: 15% of cases have no contact details at all

    if rng.random() < 0.35:
        ip = plant(pii_log, "IP_ADDRESS", fake_ip(rng))
        parts.append(f"The affected server is at {ip}.")

    r = rng.random()
    if r < 0.15:
        key = plant(pii_log, "API_KEY", fake_api_key(rng))
        parts.append(f"For reference, our key is {key}.")
    elif r < 0.25:
        token = plant(pii_log, "BEARER_TOKEN", fake_bearer(rng))
        parts.append(f"The failing request used the header Authorization: {token}.")

    if rng.random() < 0.70:
        name = plant(pii_log, "NAME", f"{first} {last}")
        parts.append(f"Thanks, {name}")

    return " ".join(parts), product, severity


def random_timestamp(rng, end, days=90):
    """A random moment in the last `days` days; busier on weekdays, 9-5."""
    while True:
        day = end - timedelta(days=rng.randint(0, days - 1))
        if day.weekday() >= 5 and rng.random() < 0.7:
            continue  # skip most weekend slots
        hour = rng.choices(range(24), weights=HOUR_WEIGHTS)[0]
        return day.replace(hour=hour, minute=rng.randint(0, 59),
                           second=rng.randint(0, 59), microsecond=0)


def resolution_hours(rng, team, severity):
    """Right-skewed (log-normal): most cases are quick, a few take very long."""
    mean = MEAN_HOURS[severity] * TEAM_SPEED[team]
    sigma = 0.6
    mu = math.log(mean) - sigma ** 2 / 2
    return max(0.5, round(rng.lognormvariate(mu, sigma), 1))


def assign_team(rng, true_team):
    """Usually correct; about 5% of the time, routed to the wrong team."""
    if rng.random() >= MISROUTE_RATE:
        return true_team
    if rng.random() < 0.8:
        return rng.choice(CONFUSABLE[true_team])
    return rng.choice([t for t in TEAMS if t != true_team])


# ---------------------------------------------------------------------------
# 4. Putting it together
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate fake support cases.")
    parser.add_argument("--n", type=int, default=400, help="number of cases")
    parser.add_argument("--seed", type=int, default=42,
                        help="same seed = identical data every run")
    parser.add_argument("--out", default=os.path.join("data", "cases.csv"))
    args = parser.parse_args()

    rng = random.Random(args.seed)
    end = datetime(2026, 10, 1)
    rows = []

    for _ in range(args.n):
        true_team = rng.choices(list(TEAMS), weights=list(TEAMS.values()))[0]
        pii_log = []
        text, product, severity = build_text(rng, true_team, pii_log)
        assigned = assign_team(rng, true_team)

        # Self-check: every planted value must really appear in the text.
        for item in pii_log:
            assert item["value"] in text, f"planted value missing: {item}"

        rows.append({
            "created_at": random_timestamp(rng, end).isoformat(),
            "product": product,
            "severity": severity,
            "text": text,
            "true_team": true_team,
            "assigned_team": assigned,
            "is_misrouted": int(assigned != true_team),
            "resolution_hours": resolution_hours(rng, true_team, severity),
            "planted_pii": json.dumps(pii_log),
        })

    rows.sort(key=lambda r: r["created_at"])
    for i, row in enumerate(rows):
        row["case_id"] = f"CASE-{100000 + i}"

    columns = ["case_id", "created_at", "product", "severity", "text",
               "true_team", "assigned_team", "is_misrouted",
               "resolution_hours", "planted_pii"]
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print_summary(rows, args.out)


def print_summary(rows, path):
    n = len(rows)
    print(f"Wrote {n} cases to {path}\n")

    print("Cases per true team:")
    for team, count in Counter(r["true_team"] for r in rows).most_common():
        print(f"  {team:<15} {count:>4}  ({count / n:.0%})")

    misrouted = sum(r["is_misrouted"] for r in rows)
    print(f"\nMisrouted cases: {misrouted} ({misrouted / n:.1%})")

    pii_counts = Counter()
    for r in rows:
        for item in json.loads(r["planted_pii"]):
            pii_counts[item["type"]] += 1
    print("\nPlanted PII / secrets (the answer key for redaction):")
    for kind, count in pii_counts.most_common():
        print(f"  {kind:<13} {count:>4}")

    print("\nSeverity counts:", dict(sorted(Counter(r["severity"] for r in rows).items())))

    print("\nThree sample cases:")
    for r in rows[:3]:
        print(f"  {r['case_id']} | {r['created_at']} | true={r['true_team']} "
              f"| assigned={r['assigned_team']} | sev={r['severity']} "
              f"| {r['resolution_hours']}h")
        print(f"    {r['text']}")
        print(f"    planted: {r['planted_pii']}\n")


if __name__ == "__main__":
    main()