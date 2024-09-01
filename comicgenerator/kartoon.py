import os
import json
from generate_panels import generate_panels
from generate_image import text_to_image_dalle3
from add_text import add_text_to_panel
from create_strip import create_strip

# ==========================================================================================

# SCENARIO = """
# Characters: Adrien is a guy with blond hair. Vincent is a guy with black hair.
# Adrien and Vincent work at the office and want to start a new product, and they create it in one night before presenting it to the board.
# """
SCENARIO = """
Characters: Lily is a little girl with curly brown hair and a red dress. Max is a small boy with spiky blonde hair and blue overalls.
Lily and Max are best friends, and they go to the playground to play on the swings. Lily falls off the swing and Max helps her up. Lily cries and Max comforts her. Lily is happy again.
"""
FILE_NAME = "Lily_and_Max_at_the_playground"
STYLE = "american comic, colored"

# ==========================================================================================

output_folder = f"output/{FILE_NAME}"
os.makedirs(output_folder, exist_ok=True)

print(f"Generate panels with style '{STYLE}' for this scenario: \n {SCENARIO}")

panels = generate_panels(SCENARIO)

with open(f'{output_folder}/panels.json', 'w') as outfile:
  json.dump(panels, outfile)

panel_images = []

for panel in panels:
  panel_prompt = panel["description"] + ", cartoon box, " + STYLE
  print(f"Generate panel {panel['number']} with prompt: {panel_prompt}")
  panel_image = text_to_image_dalle3(panel_prompt)
  panel_image_with_text = add_text_to_panel(panel["text"], panel_image)
  panel_image_with_text.save(f"{output_folder}/panel-{panel['number']}.png")
  panel_images.append(panel_image_with_text)

create_strip(panel_images).save(f"{output_folder}/strip.png")
