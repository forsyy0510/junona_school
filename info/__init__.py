from flask import Blueprint

info_bp = Blueprint('info_bp', __name__, template_folder='../templates')

# Импортируем маршруты
from . import routes 