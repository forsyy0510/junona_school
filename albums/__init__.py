from flask import Blueprint

albums_bp = Blueprint('albums', __name__, template_folder='../templates/albums')

from . import routes 