#!/usr/bin/env python3
"""
Interactive StoryGPT console client
-----------------------------------
• Requires `requests`  (pip install requests)
• Make sure your FastAPI backend is already running, e.g.:
      uvicorn main:app --reload
• Press Ctrl‑C (KeyboardInterrupt) to quit.
"""

import json
import requests

BASE_URL = "http://127.0.0.1:8000"   # change if the server lives elsewhere
CONV_ID  = "demo"                    # any stable ID you like


def call_chat(text: str) -> dict:
    """POST /chat and return the parsed JSON."""
    r = requests.post(
        f"{BASE_URL}/chat",
        json={
            "conversation_id": CONV_ID,
            "user_input": text,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def main() -> None:
    print("StoryGPT console – type your prompt (Ctrl‑C to exit)\n")
    try:
        while True:
            # read user input
            try:
                user_text = input("> ").strip()
            except EOFError:      # Ctrl‑D → graceful exit
                break
            if not user_text:
                continue

            # call backend and pretty‑print result
            try:
                resp = call_chat(user_text)
                print(json.dumps(resp, indent=2, ensure_ascii=False))
            except requests.exceptions.RequestException as e:
                print(f"[HTTP error] {e}")
    except KeyboardInterrupt:
        pass             # fall through to final message
    finally:
        print("\nBye!  👋")


if __name__ == "__main__":
    main()
