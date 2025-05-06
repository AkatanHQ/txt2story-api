#!/usr/bin/env python3
"""
Simple console client for the StoryGPT FastAPI backend.
Run the server first:

    uvicorn main:app --reload

Then start this client:

    python cli_test.py
"""
import json
import requests   # pip install requests

API_URL = "http://localhost:8000/chat"

def send(user_input: str) -> dict:
    """POST user_input to /chat and return the parsed JSON."""
    resp = requests.post(API_URL, json={"user_input": user_input}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def pretty(d: dict) -> str:
    """Nicely format the response for console display."""
    mode = d["mode"]
    out = [f"\n[MODE: {mode}]"]
    if d.get("assistant_output"):
        out.append(f"Assistant: {d['assistant_output']}")
    if d.get("story"):
        story = d["story"]
        out.append(f"\nStory prompt → {story['prompt']}")
        for page in story["pages"]:
            out.append(f"  • page {page['index']}: {page['text']}")
    return "\n".join(out)

def main() -> None:
    print("🎬  StoryGPT console client – type 'quit' to exit")
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

if __name__ == "__main__":
    main()
