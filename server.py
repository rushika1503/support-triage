"""Support Case Triage: an MCP server.

Run it (it talks over stdio, so it will just wait for a client):
    python server.py

Look at it in the MCP Inspector (needs Node.js):
    npx @modelcontextprotocol/inspector python server.py

IMPORTANT: with stdio, stdout is the protocol channel. Never use print() here.
Log to stderr instead: print("...", file=sys.stderr)
"""
import csv
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from kb import ARTICLES
from redact import redact_text as _redact

HERE = Path(__file__).parent
CONFIDENCE_CUTOFF = 0.4   # below this, a human should review the routing

mcp = FastMCP("support-triage")


def _train():
    """Train the routing model once, when the server starts."""
    with open(HERE / "data" / "cases.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    texts = [_redact(r["text"]) for r in rows]
    labels = [r["true_team"] for r in rows]
    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
    model.fit(texts, labels)
    print(f"model trained on {len(rows)} cases", file=sys.stderr)
    return model


MODEL = _train()

STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "in", "on", "for",
             "with", "not", "has", "have", "we", "our", "it", "after", "from"}


def _words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


# ---------- TOOLS: actions the model can call ----------

@mcp.tool()
def redact_text(text: str) -> str:
    """Replace emails, phone numbers, IP addresses, API keys and bearer tokens
    with labels like [EMAIL]. Names are NOT detected."""
    return _redact(text)


@mcp.tool()
def classify_case(text: str) -> dict:
    """Predict which support team should handle a case.
    The text is redacted first. Returns the team, a confidence between 0 and 1,
    and whether a human should review the routing."""
    clean = _redact(text)
    probs = MODEL.predict_proba([clean])[0]
    best = int(probs.argmax())
    confidence = float(probs[best])
    return {
        "team": str(MODEL.classes_[best]),
        "confidence": round(confidence, 2),
        "needs_human": confidence < CONFIDENCE_CUTOFF,
    }


@mcp.tool()
def search_kb(query: str, top_k: int = 3) -> list[dict]:
    """Search the knowledge base by keyword overlap (version 1).
    Returns article ids, teams and titles. Read an article with the
    kb://article/{id} resource."""
    query_words = _words(_redact(query))
    scored = []
    for article in ARTICLES:
        score = len(query_words & _words(article["title"] + " " + article["body"]))
        if score:
            scored.append((score, article))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {"id": a["id"], "team": a["team"], "title": a["title"], "score": s}
        for s, a in scored[:top_k]
    ]


# ---------- RESOURCE: data the client can read ----------

@mcp.resource("kb://article/{article_id}")
def get_article(article_id: str) -> str:
    """The full text of one knowledge base article."""
    for article in ARTICLES:
        if article["id"] == article_id:
            return f"{article['title']} ({article['team']})\n\n{article['body']}"
    return f"No article with id {article_id}"


# ---------- PROMPT: a reusable template the user can pick ----------

@mcp.prompt()
def triage_case(case_text: str) -> str:
    """Ask the model to triage one support case using the tools."""
    return (
        "You are a support triage assistant.\n"
        "1. Call classify_case on the case to choose a team.\n"
        "2. Call search_kb to find related articles.\n"
        "3. Write a three-line triage note: team, confidence, and the best article.\n"
        "Never repeat personal data from the case.\n\n"
        f"Case:\n{case_text}"
    )


if __name__ == "__main__":
    mcp.run()   # stdio by default