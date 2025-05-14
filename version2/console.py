# console.py – stateful StoryGPT CLI client with image saving & entity images
import json
import textwrap
import os
import base64
from datetime import datetime
from typing import Dict, List
import requests

API_URL = "http://localhost:4001/chat"

DIVIDER = "=" * 70
SUBDIV = "-" * 70
INDENT = "  "

# Global state (like a frontend)
story = {
    "prompt": "",
    "pages": [],
    "images": []
}

entities = []
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

# console.py – put this next to _pp_story / _pp_entities
def _pp_page_images(imgs):
    rows = [
        [
            img.get("index", "-"),
            (img.get("prompt") or "")[:40],  # crop long prompts
            img.get("size", ""),
            img.get("quality", "")
        ]
        for img in imgs
    ]
    return _format_table(["Pg", "Prompt", "Size", "Quality"], rows)


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
    sections = [f"{DIVIDER}\nMODE: {resp.get('mode')}\n{DIVIDER}\n"]

    # assistant free-text
    if (msg := resp.get("assistant_output")):
        sections.append("Assistant:\n" +
                        textwrap.indent(textwrap.fill(msg, 66), INDENT))

    # story pages                                         ▼▼ NEW ▼▼
    if (s := resp.get("story")):
        sections.append("Story:\n" + _pp_story(s))
        if s.get("images"):
            sections.append("Page images:\n" + _pp_page_images(s["images"]))

    # entities
    if (ents := resp.get("entities")):
        sections.append("Entities:\n" + _pp_entities(ents))

    # any loose images we just saved (see next step)
    if (loose := resp.get("_loose_image_paths")):
        sections.append("Generated image files:\n" +
                        "\n".join(f"{INDENT}• {p}" for p in loose))

    return ("\n" + SUBDIV + "\n").join(sections)


# ─── Helpers ──────────────────────────────────────────────────────────────

def encode_image_b64(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def manually_add_entity(name: str, image_path: str, prompt: str):
    global entities
    b64 = encode_image_b64(image_path)
    new_entity = {
        "name": name,
        "b64_json": b64,
        "prompt": prompt
    }
    entities.append(new_entity)
    print(f"✅ Manually added entity: {name} (image: {image_path})")

# ─── Main REPL ────────────────────────────────────────────────────────────

def send(msg: str) -> Dict:
    global story, entities, history
    payload = {
        "user_input": msg,
        "story": story,
        "entities": entities,
        "history": history,
    }
    res = requests.post(API_URL, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()

    # ── update local state ───────────────────────────────
    story    = data.get("story", story)
    entities = data.get("entities", entities)
    history  = data.get("history", history)

    # ── capture any ad-hoc image ─────────────────────────
    loose_paths = []
    if (image_b64 := data.get("image_b64")):
        os.makedirs("out_images", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path  = f"out_images/image_{timestamp}.png"
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
        loose_paths.append(out_path)

    for img in (story.get("images") or []):
        if img and img.get("image_b64"):
            index = img.get("index", "unknown")
            filename = f"out_images/page_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as f:
                f.write(base64.b64decode(img["image_b64"]))
            loose_paths.append(filename)

    # pass those filenames back to pretty()
    if loose_paths:
        data["_loose_image_paths"] = loose_paths

    return data



if __name__ == "__main__":
    print("📚 StoryGPT (stateful CLI)")
    print("Type messages to continue the story, 'exit' to quit.")
    print("Special command: add_entity_with_image <name> <image_path> <prompt>\n")
    manually_add_entity("John", "out_images/Man1.webp", "a young man with brown hair")
    manually_add_entity("Dog", "out_images/dog2.webp", "dog has a hat on")

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break
        if msg.lower() in {"exit", "quit"}:
            break

        if msg.startswith("add_entity_with_image"):
            try:
                _, name, path, *prompt_parts = msg.split()
                prompt = " ".join(prompt_parts)
                manually_add_entity(name, path, prompt)
            except Exception as e:
                print(f"❌ Failed to add entity: {e}")
            continue

        try:
            response = send(msg)
            print(pretty(response))
        except Exception as e:
            print(f"❌ Error: {e}")
