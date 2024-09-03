# app/api.py

from flask import Blueprint, request
from app.generate.generate_comic import generate_comic

api = Blueprint('api', __name__)

@api.route('/generate_comic', methods=['POST'])
def generate_comic_route():
    data = request.json
    return generate_comic(data)