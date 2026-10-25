from redact import redact_text

assert redact_text("Reach me at diego.garcia@example.com or (425) 555-0163. Thanks, Diego Garcia") == \
    "Reach me at [EMAIL] or [PHONE]. Thanks, Diego Garcia"
assert redact_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456 from 203.0.113.40") == \
    "Authorization: [BEARER_TOKEN] from [IP_ADDRESS]"
assert redact_text("key demo_key_0123456789abcdef0123456789abcdef") == "key [API_KEY]"
print("all passed")