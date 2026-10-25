# Support Case Triage Toolkit

A small personal project that mirrors the kinds of systems a customer support
engineering platform needs: redaction of PII and secrets, case routing,
retrieval, an MCP tool server, and an evaluation harness with a CI quality gate.

All data is synthetic. Nothing here comes from any employer or client.

## Step 1: synthetic case data

```
python generate_data.py                 # 400 cases, seed 42
python generate_data.py --n 600 --seed 7
```

Only the Python standard library is needed (Python 3.8+).

Output: `data/cases.csv`. The same seed always produces the same file.

| Column | Meaning |
| --- | --- |
| `case_id` | Unique id, increasing with time |
| `created_at` | ISO timestamp over the last 90 days (used for KQL later) |
| `product` | Sub-product the case is about |
| `severity` | 1 (most urgent) to 4 |
| `text` | The customer's message, with fake PII and secrets mixed in |
| `true_team` | The correct team (the label the classifier learns) |
| `assigned_team` | Where the case was actually routed (about 5% wrong) |
| `is_misrouted` | 1 if `assigned_team` differs from `true_team` |
| `resolution_hours` | Hours to resolve (right-skewed) |
| `planted_pii` | JSON answer key: every fake email, phone, IP, key, token, and name placed in `text` |

Fake data is built to be safe:
- Emails use `contoso.com`, `fabrikam.com`, and `example.com`.
- Phone numbers use the fictional `555-01xx` range.
- IPs use documentation-only ranges.
- API keys start with `demo_key_` so secret scanners do not flag the CSV.


## Results: redaction (regex layer)

- Synthetic data: 400 cases with a planted-PII answer key.
- On that data, recall and precision were 100% for email, phone, IP,
  API key and bearer token. Leak check: 0 of 400 cases leaked anything
  except names. Names leaked 282 of 282 (regex cannot find names).
- That data uses clean formats I generated, so I also wrote 8 tricky cases by hand.
  Initial result: recall 57%, precision 80%. After allowing dots and a missing
  space in phone numbers: recall 86%, precision 86%.
- Still failing: an email written as "jo at contoso dot com" (no @ sign) and a
  version number "2.58.0.1" flagged as an IP address.
- Next layers: NER for names, and an LLM check for obfuscated or ambiguous cases.
- Tokenization (reversible) is available through `tokenize_text` / `detokenize_text`.

## Next steps

2. Redaction: regex layer first, then measure how much planted PII it catches.
3. MCP server exposing `redact_text`, `classify_case`, and `search_kb`.
4. Evaluation harness with an LLM judge and a CI regression gate.