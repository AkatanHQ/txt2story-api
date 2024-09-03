from flask import Blueprint, request, jsonify, send_file
from app.generate.generate_comic import generate_comic
from app.storage.storage_manager import ComicStorageManager
import os
from io import BytesIO

# Initialize the storage manager once at the module level
storage_manager = ComicStorageManager()

api = Blueprint('api', __name__)

@api.route('/generate_comic', methods=['POST'])
def generate_comic_route():
    data = request.json

    user_id = data.get('user_id')
    scenario = data.get('scenario')
    file_name = data.get('file_name')
    style = data.get('style', 'american comic, colored')
    manual_panels = data.get('manual_panels')

    if not user_id:
        return jsonify({"error": "user_id must be provided."}), 400
    if not file_name:
        return jsonify({"error": "file_name must be provided."}), 400

    # Pass the storage manager to the generate_comic function
    panels = generate_comic(storage_manager, scenario=scenario, user_id=user_id, file_name=file_name, style=style, manual_panels=manual_panels)
    
    if panels is None:
        return jsonify({"error": "Comic generation failed."}), 500

    return jsonify({"message": "Comic generated successfully.", "panels": panels}), 200

@api.route('/get_comic', methods=['GET'])
def get_comic_route():
    user_id = request.args.get('user_id')
    file_name = request.args.get('file_name')

    if not user_id:
        return jsonify({"error": "user_id must be provided."}), 400
    if not file_name:
        return jsonify({"error": "file_name must be provided."}), 400

    # Load the panels JSON using the shared storage manager
    panels = storage_manager.load_json(user_id=user_id, comic_name=file_name, json_name='panels.json')
    
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
    user_id = request.args.get('user_id')
    file_name = request.args.get('file_name')
    panel_number = request.args.get('panel_number')

    if not user_id:
        return jsonify({"error": "user_id must be provided."}), 400
    if not file_name:
        return jsonify({"error": "file_name must be provided."}), 400
    if not panel_number:
        return jsonify({"error": "panel_number must be provided."}), 400

    # Attempt to load the image using the storage manager
    image = storage_manager.load_image_by_panel_number(user_id, file_name, panel_number)

    if image is None:
        return jsonify({"error": "Image not found."}), 404

    # Serve the image file
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
