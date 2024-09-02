# app/api.py

from flask import Blueprint, request
from app.generate_comic import generate_comic, get_strip

api = Blueprint('api', __name__)

@api.route('/generate_comic', methods=['POST'])
def generate_comic_route():
    data = request.json
    return generate_comic(data)

@api.route('/get_strip/<file_name>', methods=['GET'])
def get_strip_route(file_name):
    return get_strip(file_name)
