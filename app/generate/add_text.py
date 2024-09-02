from PIL import Image, ImageDraw, ImageFont

def add_text_to_panel(text, panel_image):
  text_image = generate_text_image(text)

  result_image = Image.new('RGB', (panel_image.width, panel_image.height + text_image.height))

  result_image.paste(panel_image, (0, 0))

  result_image.paste(text_image, (0, panel_image.height))

  return result_image

def generate_text_image(text):
   # Define image dimensions
  width = 1024
  height = 128

  # Create a white background image
  image = Image.new('RGB', (width, height), color='white')

  # Create a drawing context
  draw = ImageDraw.Draw(image)

  # Choose a font (Pillow's default font)
  font = ImageFont.truetype(font="font/manga_temple/manga-temple.ttf", size=30)

  # Calculate text bounding box
  bbox = draw.textbbox((0, 0), text, font=font)
  text_width = bbox[2] - bbox[0]
  text_height = bbox[3] - bbox[1]

  # Calculate the position to center the text horizontally and vertically
  x = (width - text_width) // 2
  y = (height - text_height) // 2

  # Define text color (black in this example)
  text_color = (0, 0, 0)

  # Add text to the image
  draw.text((x, y), text, font=font, fill=text_color)

  # Save the image
  image.save('output_image.png')  

  return image

# text = """
# Vincent: I think we need a new product.
# Adrien: Let's brainstorm some ideas.
#   """

# image = add_text_to_panel(text, "panel1")

# # save image with PIL
# image.save('panel1-text.png')