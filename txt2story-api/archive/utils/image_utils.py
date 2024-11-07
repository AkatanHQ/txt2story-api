import base64
from io import BytesIO

def encode_image_to_base64(image):
    """Helper function to convert an image to base64."""
    img_io = BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode('utf-8')