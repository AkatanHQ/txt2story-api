from flask import Blueprint, request, jsonify
from app.generate.generate_comic import generate_comic
from app.storage.storage_manager import ComicStorageManager

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

    # Initialize the storage manager
    storage_manager = ComicStorageManager()

    # Pass the storage manager to the generate_comic function
    panels = generate_comic(storage_manager, scenario=scenario, user_id=user_id, file_name=file_name, style=style, manual_panels=manual_panels)
    
    if panels is None:
        return jsonify({"error": "Comic generation failed."}), 500

    return jsonify({"message": "Comic generated successfully.", "panels": panels}), 200
