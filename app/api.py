# api.py
from flask import Blueprint, request, jsonify, send_file
from app.generate.comic_generator import ComicGenerator  # Updated to use ComicGenerator
from app.storage.storage_manager import ComicStorageManager
from app.utils.enums import StoryLength
import os
from io import BytesIO

# Initialize the storage manager once at the module level
storage_manager = ComicStorageManager()

api = Blueprint('api', __name__)

@api.route('/generate_comic', methods=['POST'])
@api.route('/generate_comic/<img_model>', methods=['POST'])
def generate_comic_route(img_model='dall-e-2'):
    data = request.json

    user_id = data.get('userId')
    scenario = data.get('scenario')
    story_title = data.get('storyTitle')
    selectedStyle = data.get('selectedStyle', 'tintinstyle')
    language = data.get('selectedLanguage', 'english')
    story_length = data.get('storyLength', 'short').upper()

    # Determine the number of panels based on story length
    try:
        num_panels = StoryLength[story_length].value
    except KeyError:
        return jsonify({"error": "Invalid storyLength provided. Choose 'short', 'medium', or 'long'."}), 400

    # Validate required fields
    if not user_id:
        return jsonify({"error": "userId must be provided."}), 400
    if not story_title:
        return jsonify({"error": "storyTitle must be provided."}), 400

    # Instantiate ComicGenerator with the storage manager and selected parameters
    comic_generator = ComicGenerator(
        storage_manager=storage_manager
    )

    # Generate the comic
    panels = comic_generator.generate_comic(
        scenario=scenario,
        user_id=user_id,
        img_model=img_model,
        selectedStyle=selectedStyle,
        language=language,
        story_title=story_title,
        num_panels=num_panels
    )
    
    if panels is None:
        return jsonify({"error": "Comic generation failed."}), 500

    return jsonify({"message": "Comic generated successfully.", "panels": panels}), 200


@api.route('/get_comic', methods=['GET'])
def get_comic_route():
    user_id = request.args.get('userId')
    story_title = request.args.get('storyTitle')

    if not user_id:
        return jsonify({"error": "userId must be provided."}), 400
    if not story_title:
        return jsonify({"error": "storyTitle must be provided."}), 400

    # Load the panels JSON using the shared storage manager
    panels = storage_manager.load_json(user_id=user_id, comic_name=story_title, json_name='panels.json')
    
    if panels is None:
        return jsonify({"error": "Comic not found."}), 404

    # Prepare response data with panel paths
    response_data = {
        "message": "Comic retrieved successfully.",
        "panels": panels
    }

    return jsonify(response_data), 200

@api.route('/get_comic_image', methods=['GET'])
def get_image_route():
    user_id = request.args.get('userId')
    story_title = request.args.get('storyTitle')
    panel_index = request.args.get('panelIndex')

    if not user_id:
        return jsonify({"error": "userId must be provided."}), 400
    if not story_title:
        return jsonify({"error": "storyTitle must be provided."}), 400
    if panel_index is None:
        return jsonify({"error": "panelIndex must be provided."}), 400

    # Attempt to load the image using the storage manager
    image = storage_manager.load_image_by_panel_index(user_id, story_title, panel_index)

    if image is None:
        return jsonify({"error": "Image not found."}), 404

    # Serve the image file
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
