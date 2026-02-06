from flask import Blueprint

news_bp = Blueprint('news_bp', __name__, template_folder='../templates/news')

from . import routes 