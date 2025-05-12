# console_stateful.py – stateful StoryGPT CLI client
# --------------------------------------------------
# Preserves story, entities, and history between turns.
# Much like the monolith/frontend would.

import json
import textwrap
from typing import Dict, List
import requests

API_URL = "http://localhost:8000/chat"

DIVIDER = "=" * 70
SUBDIV = "-" * 70
INDENT = "  "

# Global state (like a frontend)
story = {
    "prompt": "A fox discovers a hidden city beneath the snow.",
    "pages": []
}

entities = [
    {"name": "Fay", "prompt": "A clever arctic fox with glowing eyes."}
]

history: List[dict] = []


# ─── Formatters ───────────────────────────────────────────────────────────

def _format_table(headers, rows):
    if not rows:
        return INDENT + "(none)"
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(str(cell))) for w, cell in zip(widths, row)]
    def fmt(row):
        return INDENT + " | ".join(str(c).ljust(w) for c, w in zip(row, widths))
    return "\n".join([fmt(headers), INDENT + "-+-".join("-"*w for w in widths)] + [fmt(r) for r in rows])

def _pp_story(s):
    out = [f"Prompt: {s.get('prompt', '')}", SUBDIV]
    for p in s.get("pages", []):
        t = textwrap.fill(p.get("text", ""), width=66)
        out.append(f"{INDENT}• Page {p['index']}\n{textwrap.indent(t, INDENT*2)}")
    return "\n".join(out or [INDENT + "(no pages)"])

def _pp_entities(ents):
    rows = [[e["name"], "yes" if e.get("b64_json") else "no", e.get("prompt", "")] for e in ents]
    return _format_table(["Name", "Img", "Prompt"], rows)

def pretty(resp: Dict) -> str:
    sections = [
        f"{DIVIDER}\nMODE: {resp.get('mode')}\n{DIVIDER}\n"
    ]
    if (msg := resp.get("assistant_output")):
        sections.append("Assistant:\n" + textwrap.indent(textwrap.fill(msg, 66), INDENT))
    if (s := resp.get("story")):
        sections.append("Story:\n" + _pp_story(s))
    if (ents := resp.get("entities")):
        sections.append("Entities:\n" + _pp_entities(ents))
    if (imgs := resp.get("image_urls")):
        sections.append("Images:\n" + "\n".join(f"{INDENT}• {url}" for url in imgs))
    return ("\n" + SUBDIV + "\n").join(sections)


# ─── Main REPL ────────────────────────────────────────────────────────────

def send(msg: str) -> Dict:
    global story, entities, history
    payload = {
        "user_input": msg,
        "story": story,
        "entities": entities,
        "history": history,
    }
    res = requests.post(API_URL, json=payload, timeout=30)
    res.raise_for_status()
    data = res.json()

    # update local state
    story = data.get("story", story)
    entities = data.get("entities", entities)
    history = data.get("history", history)

    return data


if __name__ == "__main__":
    print("📚 StoryGPT (stateful CLI)")
    print("Type messages to continue the story, 'exit' to quit.\n")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break
        if msg.lower() in {"exit", "quit"}:
            break
        try:
            response = send(msg)
            print(pretty(response))
        except Exception as e:
            print(f"❌ Error: {e}")