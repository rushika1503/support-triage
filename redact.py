import re

EMAIL_PATTERN = r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def find_emails(text):
    return re.findall(EMAIL_PATTERN, text)

API_KEY_PATTERN = r"demo_key_[0-9a-f]{32}"

def find_api_keys(text):
    return re.findall(API_KEY_PATTERN, text)

IP_PATTERN = r"\d{1,3}(?:\.\d{1,3}){3}"

def find_ips(text):
    return re.findall(IP_PATTERN, text)


BEARER_PATTERN = r"Bearer [A-Za-z0-9_-]{20,}"

def find_bearer_tokens(text):
    return re.findall(BEARER_PATTERN, text)


PHONE_PATTERN = r"(?:\+1 )?(?:\(\d{3}\) |\d{3}[ -])\d{3}[ -]\d{4}"

def find_phones(text):
    return re.findall(PHONE_PATTERN, text)


# Order matters: long, specific patterns first, so a later pattern
# (like phone) can't match inside something an earlier one already replaced.
PATTERNS = {
    "BEARER_TOKEN": BEARER_PATTERN,
    "API_KEY": API_KEY_PATTERN,
    "EMAIL": EMAIL_PATTERN,
    "IP_ADDRESS": IP_PATTERN,
    "PHONE": PHONE_PATTERN,
}

def redact_text(text):
    for kind, pattern in PATTERNS.items():
        # print(pattern, f"[{kind}]", text)
        text = re.sub(pattern, f"[{kind}]", text)
    return text


#tokenization
def tokenize_text(text):
    table = {}
    seen = {}
    counts= {}

    for kind,pattern in PATTERNS.items():
        def replace(match):
            value = match.group(0)
            if value not in seen:
                counts[kind] = counts.get(kind, 0) + 1
                token = f"[{kind}_{counts[kind]}]"
                seen[value] = token
                table[token] = value
            return seen[value]

        text = re.sub(pattern, replace, text)

    return text, table

def detokenize_text(text, table):
    for token, value in table.items():
        text = text.replace(token, value)
    return text