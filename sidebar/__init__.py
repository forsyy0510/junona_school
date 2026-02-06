from flask import Blueprint

sidebar_bp = Blueprint('sidebar', __name__, template_folder='../templates/sidebar')

from . import routes
