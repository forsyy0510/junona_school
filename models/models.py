from flask_login import UserMixin
from datetime import datetime
from database import db
import json

# Section model moved to info/models.py as InfoSection


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    publication_date = db.Column(db.DateTime, nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(255), nullable=True)  # Изображение для превью
    files = db.relationship('File', backref='news', lazy=True)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    publication_date = db.Column(db.DateTime, nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(255), nullable=True)  # Изображение для превью
    files = db.relationship('File', backref='announcement', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=True)
    # section_id removed - Section model moved to info/models.py as InfoSection
    # section relationship removed - Section model moved to info/models.py as InfoSection
    kind = db.Column(db.String(20), default='doc')  # 'image' | 'doc'
    is_preview = db.Column(db.Boolean, default=False)


class InfoFile(db.Model):
    """Модель для файлов информационных разделов"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # Имя файла на диске
    original_filename = db.Column(db.String(255), nullable=False)  # Оригинальное имя файла
    file_path = db.Column(db.String(500), nullable=True)  # Путь к файлу на диске (опционально, для обратной совместимости)
    section_endpoint = db.Column(db.String(100), nullable=False)  # Раздел (main, about, etc.)
    field_name = db.Column(db.String(100), nullable=True)  # Поле формы (license_document, etc.)
    file_size = db.Column(db.Integer, nullable=False)  # Размер файла в байтах
    mime_type = db.Column(db.String(100), nullable=True)  # MIME тип файла
    is_image = db.Column(db.Boolean, default=False)  # Является ли файл изображением
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    display_name = db.Column(db.String(255), nullable=True)  # Имя для отображения пользователю
    file_data = db.Column(db.LargeBinary, nullable=True)  # Данные файла в БД (BLOB)
    stored_in_db = db.Column(db.Boolean, default=True)  # Флаг: хранится ли файл в БД (True) или в файловой системе (False)
    
    def __repr__(self):
        return f'<InfoFile {self.original_filename}>'
    
    def get_download_url(self):
        """Возвращает URL для скачивания файла"""
        # Для файлов питания используем специальный URL
        if self.section_endpoint == 'food' or self.field_name == 'menu_file':
            return f'/food/{self.filename}'
        
        # Проверяем, является ли раздел sidebar разделом
        # Импортируем InfoSection для проверки URL
        try:
            from info.models import InfoSection
            section = InfoSection.query.filter_by(endpoint=self.section_endpoint).first()
            if section and section.url and section.url.startswith('/sidebar/'):
                return f'/sidebar/download_file/{self.section_endpoint}/{self.filename}'
        except ImportError as e:
            # Ошибка импорта - логируем и используем стандартный URL
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Не удалось импортировать InfoSection для проверки URL: {e}")
        except Exception as e:
            # Другие ошибки (например, проблемы с БД) - логируем и используем стандартный URL
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ошибка при проверке типа раздела для {self.section_endpoint}: {e}")
        
        return f'/info/download_file/{self.section_endpoint}/{self.filename}'
    
    def get_file_info(self):
        """Возвращает информацию о файле для API"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'display_name': self.display_name or self.original_filename,
            'url': self.get_download_url(),
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'is_image': self.is_image,
            'upload_date': self.upload_date.isoformat(),
            'section_endpoint': self.section_endpoint,
            'field_name': self.field_name
        }


class PageContent(db.Model):
    """Модель для хранения контента редактируемых страниц"""
    id = db.Column(db.Integer, primary_key=True)
    page_key = db.Column(db.String(100), unique=True, nullable=False)  # 'index', 'events', 'info', 'projects', 'albums', 'contacts', 'about'
    content = db.Column(db.Text)  # JSON строка с контентом страницы
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_content(self):
        """Получить контент как словарь"""
        if self.content:
            try:
                return json.loads(self.content)
            except:
                return {}
        return {}
    
    def set_content(self, data):
        """Установить контент из словаря"""
        self.content = json.dumps(data, ensure_ascii=False)
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_or_create(page_key, default_content=None):
        """Получить или создать запись для страницы"""
        page = PageContent.query.filter_by(page_key=page_key).first()
        if not page:
            page = PageContent(page_key=page_key)
            if default_content:
                page.set_content(default_content)
            db.session.add(page)
            db.session.commit()
        return page


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password) 