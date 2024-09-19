import re
from openai import OpenAI

template = """
You are a cartoon creator.

You will be given a short scenario, you must split it in {num_panels} parts.
Each part will be a different cartoon panel.
For each cartoon panel, you will write a description of it with:
 - the characters in the panel, they must be described precisely each time
 - the background of the panel
The description should be only word or group of word delimited by a comma, no sentence.
Always use the characters descriptions instead of their name in the cartoon panel description.
You can not use the same description twice.
You will also write the text of the panel.
The text should not be more than 2 small sentences.
Each sentence should start by the character name

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
            appearance: 'A guy with black hair wearing a hat.',
            description: '',
            picture: null
        }}
    ]
}},
Example output:

# Panel 1
description: 2 guys, a blond hair guy wearing glasses, a dark hair guy wearing hat, sitting at the office, with computers
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

def generate_panels(scenario, num_panels):
    # Format the prompt
    print('test')
    formatted_prompt = template.format(scenario=scenario, num_panels=num_panels)
    print('test2')
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
