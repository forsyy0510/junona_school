from flask import Blueprint

announcements_bp = Blueprint('announcements', __name__, template_folder='../templates/announcements')

from . import routes 