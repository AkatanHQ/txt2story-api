from enum import Enum

class StyleDescription(Enum):
    TINTIN = "Belgian comic style featuring clean, uniform lines (ligne claire) with consistent line weight. Use flat, vibrant colors with minimal shading to create a clear and bold look. Characters should have simplified, realistic proportions with slightly stylized features. Detailed but simplified, adding depth without overpowering the characters. The overall atmosphere is adventurous and friendly. Lighting is bright and even, with no complex shadows. The scene should convey a sense of story and clarity, typical of classic European comics like Tintin."
    TODDLER = "cheerful and playful illustration for toddlers featuring characters with big round heads and small, chubby bodies. The characters should have large, bright eyes and wide, friendly smiles, representing diverse skin tones and hairstyles. Use a vibrant color palette with bold reds, yellows, blues, and greens, alongside soft pastels for a warm feel. The background should be simple and whimsical, featuring elements like lush green grass, colorful flowers, and a sunny blue sky. The art style should be cartoonish and hand-drawn, conveying a joyful and fun atmosphere with characters engaging in playful activities."

class StoryLength(Enum):
    SHORT = 2
    MEDIUM = 10
    LONG = 15