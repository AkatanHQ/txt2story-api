from __future__ import annotations

"""test_chat_cli.py – simple CLI to talk to StoryGPT backend
---------------------------------------------------------
Requirements:
  pip install requests rich  # rich is optional but recommended

Usage:
  python test_chat_cli.py [http://localhost:4001/chat]

The script keeps the entire conversation state (story, entities, history)
between turns so you can iterate on a single story in one run.
---------------------------------------------------------
"""

import sys
import json
import textwrap
from typing import Any, Dict, List, Optional

import requests

try:
    from rich import print as rprint
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
except ImportError:  # graceful fallback
    RICH_AVAILABLE = False


# ────────────────────────────
# Utility helpers
# ────────────────────────────

def pretty_json(obj: Any) -> str:
    """Return obj as nicely formatted JSON string (2-space indent)."""
    return json.dumps(obj, indent=2, ensure_ascii=False)


def print_user(msg: str) -> None:
    if RICH_AVAILABLE:
        rprint(Panel(msg, title="[bold cyan]You", style="cyan"))


def print_assistant(resp: Dict[str, Any]) -> None:
    assistant_output = resp.get("assistant_output", "(no assistant_output)")
    modes = resp.get("modes", [])
    extra_lines: List[str] = []

    if modes:
        extra_lines.append(f"Modes: {', '.join(modes)}")
    if resp.get("image_b64"):
        extra_lines.append("[image base64 omitted]")

    footer = "\n".join(extra_lines)

    if RICH_AVAILABLE:
        body = assistant_output if footer == "" else assistant_output + "\n\n" + footer
        rprint(Panel(body, title="[bold magenta]Assistant", style="magenta"))
    else:
        print("-" * 60)
        print("Assistant:", textwrap.fill(assistant_output, width=80))
        if footer:
            print("\n" + footer)
        print("-" * 60)


# ────────────────────────────
# Main CLI loop
# ────────────────────────────

def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4001/chat"
    print("StoryGPT CLI tester – type 'exit' or 'quit' to leave.")
    print(f"Endpoint: {base_url}\n")

    story: Optional[Dict] = None
    entities: Optional[List[Dict]] = None
    history: Optional[List[Dict]] = None

    while True:
        try:
            user_input = Prompt.ask("You") if RICH_AVAILABLE else input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if user_input.strip().lower() in {"exit", "quit"}:  # graceful exit
            print("Goodbye!")
            break

        print_user(user_input)

        payload = {
            "user_input": user_input,
            "story": story,
            "entities": entities,
            "history": history,
        }

        try:
            response = requests.post(base_url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            print(f"[ERROR] HTTP request failed: {exc}")
            continue
        except ValueError as exc:
            print(f"[ERROR] Invalid JSON response: {exc}\nRaw text: {response.text[:500]}")
            continue

        # Persist conversation state for next turn
        story = data.get("story")
        entities = data.get("entities")
        history = data.get("history")
        settings = data.get("settings")

        # ────────────────────────────
        # Optional debug output (Rich / plain)
        # ────────────────────────────
        if RICH_AVAILABLE:
            # ---------- Story pages ----------
            if story and story.get("pages"):
                table = Table(title="Story Pages", title_style="bold yellow")
                table.add_column("Index", style="cyan", no_wrap=True)
                table.add_column("Text", style="white")
                for page in story.get("pages", []):
                    table.add_row(str(page.get("index", "?")), page.get("text", ""))
                console.print(table)

            # ---------- Story images ----------
            if story and story.get("images"):
                table = Table(title="Images", title_style="bold blue")
                table.add_column("Index", style="cyan", no_wrap=True)
                table.add_column("Prompt", style="white")
                table.add_column("Size", style="white", no_wrap=True)
                table.add_column("Quality", style="white", no_wrap=True)
                for img in story.get("images", []):
                    table.add_row(
                        str(img.get("index", "?")),
                        img.get("prompt", ""),
                        img.get("size", ""),
                        img.get("quality", ""),
                    )
                console.print(table)

            # ---------- Entities ----------
            if entities:
                table = Table(title="Entities", title_style="bold green")
                table.add_column("Name", style="cyan")
                table.add_column("Prompt", style="white")
                for entity in entities:
                    table.add_row(entity.get("name", ""), entity.get("prompt", ""))
                console.print(table)

            # ---------- History ----------
            if history:
                table = Table(title="History", title_style="bold yellow")
                table.add_column("Role", style="white")
                table.add_column("Content", style="white")
                for entry in history:
                    table.add_row(entry.get("role", ""), entry.get("content", ""))
                console.print(table)

            # ---------- Settings ----------
            if settings:
                table = Table(title="Settings", title_style="bold red")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="white")
                for key, value in settings.items():
                    table.add_row(key, str(value))
                console.print(table)
        else:
            # Fallback plain printing
            if story and story.get("pages"):
                print("\n[Story Pages]")
                for page in story.get("pages", []):
                    print(f"({page['index']}) {page.get('text', '')}")

            if story and story.get("images"):
                print("\n[Images]")
                for img in story.get("images", []):
                    line = f"({img['index']}) prompt: {img.get('prompt', '')}"
                    if img.get("size"):
                        line += f" | size: {img['size']}"
                    if img.get("quality"):
                        line += f" | quality: {img['quality']}"
                    print(line)

            if entities:
                print("\n[Entities]")
                for e in entities:
                    print(f"- {e['name']}: {e.get('prompt', '')}")

            if history:
                print("\n[History]")
                for h in history:
                    print(f"{h['role']}: {h['content']}")

            if settings:
                print("\n[Settings]")
                for k, v in settings.items():
                    print(f"{k}: {v}")

        # Finally, print assistant's textual response
        print_assistant(data)


if __name__ == "__main__":
    main()
