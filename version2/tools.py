from typing import Dict, List, Optional, Tuple

# ────────────────────────────
# ░░ OpenAI tool definitions ░░
# ────────────────────────────
TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "generate_image_for_index",
            "description": "Generate an image for a given page index; store it on that page index.",
            "parameters": {
            "type": "object",
            "properties": {
                "index":  { "type": "integer", "description": "Page index the image is for." },
                "prompt": { "type": "string", "description": "Prompt for GPT-image-1." },
                "entity_names": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "Names of entities to reference."
                    }
            },
            "required": ["page", "prompt"]
            }
        }
    },

    {
        "type": "function",
            "function": {
            "name": "generate_image",
            "description": "Generate an image using the GPT-image model with optional entity inputs as references. If an entity has no image, its prompt is used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the image."},
                    "entity_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Names of entities to include in the image generation."
                    }
                },
                "required": ["prompt"]
            }
        }
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
            "description": "Add a new entity usable by future story/image generations. Make it unique",
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
            "description": "Update an existing entity, identified by `name`.\n"
                            "You can change any subset of: `new_name`, `prompt`, `b64_json`.\n"
                            "If multiple fields are supplied they’re all applied atomically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Identifier to update."},
                    "new_name":  {"type": "string", "description": "New identifier (must be unique)."},
                    "b64_json":  {"type": "string", "description": "New base64 image data."},
                    "prompt":    {"type": "string", "description": "New text description/prompt."}
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