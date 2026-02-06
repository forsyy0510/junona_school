"""
Модели для информационных страниц
"""

from database import db
import json

class InfoSection(db.Model):
    """Модель для информационных разделов"""
    __tablename__ = 'info_section'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text)
    content_blocks = db.Column(db.Text)  # JSON строка с блоками контента
    
    def get_content_blocks(self):
        """Получить блоки контента как список"""
        if self.content_blocks:
            try:
                return json.loads(self.content_blocks)
            except:
                return []
        return []
    
    def set_content_blocks(self, blocks):
        """Установить блоки контента"""
        self.content_blocks = json.dumps(blocks, ensure_ascii=False)
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'url': self.url,
            'title': self.title,
            'text': self.text,
            'content_blocks': self.get_content_blocks()
        }
