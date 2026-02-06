"""
Централизованная конфигурация базы данных
"""

from flask_sqlalchemy import SQLAlchemy

# Создаем единый экземпляр базы данных
db = SQLAlchemy()
