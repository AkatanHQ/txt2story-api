#!/usr/bin/env python3
"""
StoryGPT console client (v2.3)
------------------------------

A tiny REPL that talks to the FastAPI backend at http://localhost:8000/chat.
It prints **all** fields returned by the ChatResponse model, but in a much more
structured layout than previous versions: clearly‑labeled sections, neat tables
for entities, and consistent dividers. It degrades gracefully when optional
sections (like images) are absent.

Run the server first:

    uvicorn main:app --reload

Then start this client:

    python console_structured.py
"""

from __future__ import annotations

import json
import textwrap
from typing import Dict, List, Sequence

import requests  # pip install requests

API_URL = "http://localhost:8000/chat"

# ──────────────────────────────────────────────────────────────────────────────
# Utility formatting helpers
# ──────────────────────────────────────────────────────────────────────────────

DIVIDER = "=" * 70
SUBDIV  = "-" * 70
INDENT  = "  "  # two‑space indent keeps things compact yet readable


def _format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Return a monospace table with left‑aligned columns.

    Because we avoid extra dependencies, we calculate column widths manually.
    """
    if not rows:
        return INDENT + "(none)"

    # Calculate max width for each column
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(str(cell))) for w, cell in zip(widths, row)]

    def _row(cells: Sequence[str]) -> str:
        return INDENT + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths))

    header_line = _row(headers)
    divider_line = INDENT + "-+-".join("-" * w for w in widths)
    data_lines = [_row(r) for r in rows]
    return "\n".join([header_line, divider_line, *data_lines])


# ──────────────────────────────────────────────────────────────────────────────
# Pretty‑printers for individual top‑level response fields
# ──────────────────────────────────────────────────────────────────────────────

def _pp_story(story: Dict) -> str:
    prompt = story.get("prompt", "—")
    page_lines = []
    for page in story.get("pages", []):
        idx = page.get("index", "?")
        txt = page.get("text", "")
        wrapped = textwrap.indent(textwrap.fill(txt, 68), INDENT * 2)
        page_lines.append(f"{INDENT}• page {idx}:\n{wrapped}")
    pages_block = "\n".join(page_lines) if page_lines else INDENT + "(no pages)"
    return (
        f"Story prompt: {prompt}\n"
        f"{SUBDIV}\n"
        f"{pages_block}"
    )


def _pp_entities(entities: List[Dict]) -> str:
    rows = []
    for ent in entities:
        name = ent.get("name", "—")
        has_img = "yes" if ent.get("b64_json") else "no"
        prompt = ent.get("prompt", "—")
        rows.append([name, has_img, prompt])
    return _format_table(["Name", "Img", "Prompt"], rows)


# ──────────────────────────────────────────────────────────────────────────────
# User‑facing pretty() combining everything
# ──────────────────────────────────────────────────────────────────────────────

def pretty(resp: Dict) -> str:
    """Return a fully‑formatted, human‑readable representation of ChatResponse."""
    sections: List[str] = []

    # 1) Mode headline
    mode = resp.get("mode", "—")
    sections.append(f"{DIVIDER}\nMODE: {mode}\n{DIVIDER}\n")

    # 2) Assistant free‑form reply
    if (assistant_msg := resp.get("assistant_output")):
        wrapped = textwrap.indent(textwrap.fill(assistant_msg, 68), INDENT)
        sections.append("Assistant:\n" + wrapped + "\n")

    # 3) Story section
    if (story := resp.get("story")):
        sections.append("Story:" + "\n" + _pp_story(story) + "\n")

    # 4) Entities section
    if "entities" in resp:
        sections.append("Entities:\n" + _pp_entities(resp["entities"]) + "\n")

    # 5) Images section
    if (urls := resp.get("image_urls")):
        url_lines = "\n".join(f"{INDENT}• {u}" for u in urls)
        sections.append("Images:\n" + url_lines + "\n")

    # 6) Raw JSON toggle (comment out to hide)
    # raw_json = json.dumps(resp, indent=2)
    # sections.append("RAW JSON →\n" + raw_json + "\n")

    # Join all pieces with a thin divider for clarity
    return ("\n" + SUBDIV + "\n").join(sections).rstrip()


# ──────────────────────────────────────────────────────────────────────────────
# Networking helpers and REPL loop
# ──────────────────────────────────────────────────────────────────────────────

def send(user_input: str) -> Dict:
    """POST user_input to /chat and return the parsed JSON."""
    resp = requests.post(API_URL, json={"user_input": user_input}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("🎬  StoryGPT console client – type 'quit' to exit")
    try:
        while True:
            try:
                msg = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if msg.lower() in {"quit", "exit"}:
                break
            try:
                response_json = send(msg)
                print(pretty(response_json))
            except Exception as exc:
                print(f"⚠️  Error: {exc}")
    finally:
        print("\n👋  Goodbye!")


if __name__ == "__main__":
    main()
