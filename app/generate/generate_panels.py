from openai import OpenAI
from pydantic import BaseModel
from typing import List, Dict
import os
from dotenv import load_dotenv
import json
load_dotenv()

# Pydantic Models
class Panel(BaseModel):
    index: int
    description: str
    text: str

class Book(BaseModel):
    title: str
    genre: str
    keywords: List[str]
    panels: List[Panel]

# Template for function calling
template = """
You are a cartoon creator.

You will be given a short scenario, you must split it into {num_panels} parts.
Each part will be a different cartoon panel.
For each cartoon panel, you will:
1. Write a description of it with:
   - Precisely describe each character, including:
     - Physical Features: Height, skin color, hair type, hair color, and hair length.
     - Clothing: Provide details of what each character is wearing.
    - Example: A tall man. Blue eyes. His hair is dark brown, medium length, slightly wavy, and falls naturally around his face, framing his forehead and temples. He wears thin, rectangular black-framed glasses that sit comfortably on his nose, adding a scholarly yet approachable touch to his look. His bright blue eyes, accentuated by the glasses, convey a friendly yet confident expression. He has a well-built, athletic physique, standing at around 6'2" with broad shoulders and toned muscles. His posture is relaxed but upright, suggesting both ease and confidence. He is dressed casually in a light blue button-down shirt with the sleeves rolled up to his elbows, showing his forearms, and well-fitted dark jeans that complement his athletic build." and "An african-american black tall man with a well-built, athletic physique, standing at around 6'2". He has short black hair that is neatly styled, with a trimmed beard that frames his face. His eyes are dark brown, exuding warmth and charisma. He has a confident smile that gives him a friendly, approachable appearance. His posture is relaxed yet confident, showing his easy-going nature. He is dressed casually in a fitted black t-shirt and dark jeans, with a modern, stylish look that complements his personality." -- They are sitting at the office, with computers.
   - Scenario Description: Describe the scenario.
2. Write the text of the panel:
    - **Engaging Story:** Create an engaging narrative, using third-person storytelling to set the scene.
   - **Max 3 Lines:** Keep the text concise and suitable for young readers.
3. Start with index 0 for the panels.
4. The title should be short and relevant.
5. Repeat the character descriptions in a concise format at the start of each panel description, followed by the scenario description.

Language should be in {language}.

Please return the output in the following JSON format:
{{
    "title": "Your Book Title",
    "genre": "Your Genre",
    "keywords": ["keyword1", "keyword2"],
    "panels": [
        {{
            "index": int,
            "description": str,
            "text": str
        }}
    ]
}}

Short Scenario:
{scenario}
"""

def generate_panels(scenario: str, num_panels: int, language: str = "english") -> Book:
    formatted_prompt = template.format(scenario=scenario, num_panels=num_panels, language=language)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": formatted_prompt},
            ],
            functions=[{
                "name": "parse_book",
                "description": "Parse the generated cartoon panels into a structured book format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "genre": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "panels": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "index": {"type": "integer"},
                                    "description": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                                "required": ["index", "description", "text"],
                            },
                        },
                    },
                    "required": ["title", "genre", "keywords", "panels"],
                },
            }],
            function_call={"name": "parse_book"}
        )
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None  # Return None or handle it according to your needs

    # Extract and parse the book data
    try:
        print(json.loads(completion.choices[0].message.function_call.arguments))
        book_data = json.loads(completion.choices[0].message.function_call.arguments)
        return book_data
    except (IndexError, AttributeError) as e:
        print(f"Error extracting book data: {e}")
        return None  # Return None or handle it according to your needs
