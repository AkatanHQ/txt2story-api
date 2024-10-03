import re
from openai import OpenAI

template = """
You are a cartoon creator.

You will be given a short scenario, you must split it in {num_panels} parts.
Each part will be a different cartoon panel.
For each cartoon panel, you will write a description of it with:
 - Precisely describe each character, using detailed physical features (e.g., height, skin color, hair type and color, eye color), clothing, posture, and expressions (e.g., smiling, laughing).
 - Include detailed descriptions of the background environment, such as trees, the sky, other people in the background, and any other relevant surroundings.
The description should be only word or group of word delimited by a comma, no sentence.
Always use the characters descriptions instead of their name in the cartoon panel description.
Repeat the character description in each panel.
Describe the environment and what they do at the end.
You will also write the text of the panel.
The text should not be more than 2 small sentences.
Each sentence should start by the character name
Language should be in {language}.

Example input:
scenario: {{
    description: 'Adrien and Vincent want to start a new product, and they create it in one night before presenting it to the board.',
    characters: [
        {{
            id: 1,
            name: 'Adrien',
            appearance: 'A guy with blond hair wearing glasses.',
            description: '',
            picture: null
        }},
        {{
            id: 2,
            name: 'Vincent',
            appearance: 'A black guy with black hair and a beard',
            description: '',
            picture: null
        }}
    ],
}},
Example output in English:

# Panel 1
description: "A tall man with blonde hair and blue eyes. His hair is medium length, slightly wavy, and falls naturally around his face, framing his forehead and temples. He wears thin, rectangular black-framed glasses that sit comfortably on his nose, adding a scholarly yet approachable touch to his look. His bright blue eyes, accentuated by the glasses, convey a friendly yet confident expression. He has a well-built, athletic physique, standing at around 6'2" with broad shoulders and toned muscles. His posture is relaxed but upright, suggesting both ease and confidence. He is dressed casually in a light blue button-down shirt with the sleeves rolled up to his elbows, showing his forearms, and well-fitted dark jeans that complement his athletic build." and ""A african-american black tall man with a well-built, athletic physique, standing at around 6'2". He has short black hair that is neatly styled, with a trimmed beard that frames his face. His eyes are dark brown, exuding warmth and charisma. He has a confident smile that gives him a friendly, approachable appearance. His posture is relaxed yet confident, showing his easy-going nature. He is dressed casually in a fitted black t-shirt and dark jeans, with a modern, stylish look that complements his personality.". They are sitting at the office, with computers.
text:
```
Vincent: I think Generative AI are the future of the company.
Adrien: Let's create a new product with it.
```
# end

Short Scenario:
{scenario}

Split the scenario in {num_panels} parts:
"
"""

def generate_panels(scenario, num_panels, language="english"):
    # Format the prompt
    formatted_prompt = template.format(scenario=scenario, num_panels=num_panels, language=language)
    client = OpenAI()

    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": formatted_prompt},
        ]
    )

    # Extract the content from the API response
    result = completion.choices[0].message.content
    print(result)
    
    # Parse and return the panel information
    return extract_panel_info(result)

def extract_panel_info(text):
    panel_info_list = []
    panel_blocks = text.split('# Panel')

    for block in panel_blocks:
        if block.strip() != '':
            panel_info = {}
            
            # Extracting panel index
            panel_index = re.search(r'\d+', block)
            if panel_index is not None:
                panel_info['index'] = panel_index.group()
            
            # Extracting panel description
            panel_description = re.search(r'description: (.+)', block)
            if panel_description is not None:
                panel_info['description'] = panel_description.group(1)
            
            # Extracting panel text
            panel_text = re.search(r'text:\n```\n(.+)\n```', block, re.DOTALL)
            if panel_text is not None:
                panel_info['text'] = panel_text.group(1)
            
            panel_info_list.append(panel_info)
    return panel_info_list
