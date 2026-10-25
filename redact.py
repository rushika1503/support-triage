import re

EMAIL_PATTERN = r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def find_emails(text):
    return re.findall(EMAIL_PATTERN, text)