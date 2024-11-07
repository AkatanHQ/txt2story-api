from generate_params import ParamTextGenerator  # Assuming the class is in a file named `ParamTextGenerator.py`

# Initialize the generator
generator = ParamTextGenerator()

# Define test data for characters
characters = [
    {
        "name": "Elara",
        "appearance": "Tall, lean, with short black hair and piercing green eyes. Wears a dark cloak over leather armor."
    },
    {
        "name": "Ronan",
        "appearance": "Broad-shouldered with a rugged beard and scar over his left brow. Dresses in a simple tunic and chainmail."
    }
]

# Generate detailed descriptions for each character
descriptions = generator.generate_character_description(characters)

# Print out the character descriptions
print("Character Descriptions:")
for description in descriptions:
    print(f"{description['name']}: {description['description']}")

# Define sample scenes for title generation
scenes = """
1. Elara meets Ronan in the forest while tracking a mysterious figure.
2. They uncover clues about a powerful artifact hidden in an ancient ruin.
3. Both characters face an internal struggle as they decide whether to trust each other.
"""

# Generate a title for the story
title = generator.generate_title(scenes)

# Print the generated title
print("\nGenerated Title:")
print(title)
