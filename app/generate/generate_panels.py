import re
from openai import OpenAI

template = """
You are a cartoon creator.

You will be given a short scenario, you must split it in {num_panels} parts.
Each part will be a different cartoon panel.
For each cartoon panel, you will:
1. Write a description of it with:
   - Precisely describe each character, including:
     - Physical Features: Height, skin color, hair type, hair color, and hair length (e.g., "long black hair reaching the mid-back"), eye color.
     - Clothing: Provide details of what each character is wearing, specifying colors and styles.
     - Always include specific colors for all features. Repeat the full character description in every panel to maintain consistency.
   - Scenario Description: Describe the scenario
2. Write the text of the panel:
   - The text should not exceed two small sentences.
   - Each sentence must start with the character's name to make it clear who is speaking or acting.

Language should be in {language}.

Example input:
scenario: {{
    description: 'Adrien and Vincent want to start a new product, and they create it in one night before presenting it to the board.',
    characters: [
        {{
            id: 0,
            name: 'Adrien',
            appearance: 'A guy with blond hair wearing glasses.',
            description: '',
            picture: null
        }},
        {{
            id: 1,
            name: 'Vincent',
            appearance: 'A black guy with black hair and a beard',
            description: '',
            picture: null
        }}
    ],
}},
Example output in English:

# Panel 0
description: "A tall man. Blue eyes. His hair is dark brown, medium length, slightly wavy, and falls naturally around his face, framing his forehead and temples. He wears thin, rectangular black-framed glasses that sit comfortably on his nose, adding a scholarly yet approachable touch to his look. His bright blue eyes, accentuated by the glasses, convey a friendly yet confident expression. He has a well-built, athletic physique, standing at around 6'2" with broad shoulders and toned muscles. His posture is relaxed but upright, suggesting both ease and confidence. He is dressed casually in a light blue button-down shirt with the sleeves rolled up to his elbows, showing his forearms, and well-fitted dark jeans that complement his athletic build." and "An african-american black tall man with a well-built, athletic physique, standing at around 6'2". He has short black hair that is neatly styled, with a trimmed beard that frames his face. His eyes are dark brown, exuding warmth and charisma. He has a confident smile that gives him a friendly, approachable appearance. His posture is relaxed yet confident, showing his easy-going nature. He is dressed casually in a fitted black t-shirt and dark jeans, with a modern, stylish look that complements his personality." -- They are sitting at the office, with computers.
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
