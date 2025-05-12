from typing import Dict, List, Optional, Tuple

# ────────────────────────────
# ░░ OpenAI tool definitions ░░
# ────────────────────────────
TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "set_page_count",
            "description": (
                "Set (or change) the total number of pages for the story. "
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "num_pages": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                        "description": "Desired page count (1–30).",
                    }
                },
                "required": ["num_pages"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_text",
            "description": "Edit the text of a single page by index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Zero-based page index."},
                    "new_text": {"type": "string", "description": "Replacement text."},
                },
                "required": ["page", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_all",
            "description": "Replace every page with new text entries in order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of new page texts.",
                    }
                },
                "required": ["new_texts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "insert_page",
            "description": "Insert a new page at the given index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "Insert position."},
                    "text": {"type": "string", "description": "Text for the new page."},
                },
                "required": ["index", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_page",
            "description": "Delete a page at the given index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "Index of the page."}
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_page",
            "description": "Move a page from one position to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_index": {"type": "integer", "description": "Current index."},
                    "to_index": {"type": "integer", "description": "Destination index."},
                },
                "required": ["from_index", "to_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_story_prompt",
            "description": "Update the story prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_prompt": {"type": "string", "description": "New prompt."}
                },
                "required": ["new_prompt"],
            },
        },
    },
    # Entity CRUD tool calls
    {
        "type": "function",
        "function": {
            "name": "add_entity",
            "description": "Add a new entity usable by future story/image generations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique identifier."},
                    "b64_json": {"type": "string", "description": "Optional base64 image."},
                    "prompt": {"type": "string", "description": "Optional text description."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_entity",
            "description": "Update an existing entity's prompt and/or image (identified by `name`).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Identifier to update."},
                    "b64_json": {"type": "string", "description": "Optional base64 image."},
                    "prompt": {"type": "string", "description": "Optional text description."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_entity",
            "description": "Remove an entity by its `name`.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Identifier to remove."}
                },
                "required": ["name"],
            },
        },
    }
]