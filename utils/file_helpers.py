"""
Общие утилиты для работы с файлами
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
from utils.logger import logger


def generate_content_filename(original_filename, content_id, file_type='image', content_type=None):
    """
    Генерирует имя файла в формате день.месяц.год - номер файла
    Для документов не использует БД, считает файлы в файловой системе
    
    Args:
        original_filename: Оригинальное имя файла
        content_id: ID контента (новости/объявления)
        file_type: Тип файла ('image' или 'doc')
        content_type: Тип контента ('news' или 'announcements') - обязателен для документов
    
    Returns:
        Сгенерированное имя файла или None
    """
    if not original_filename:
        return None
    
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    
    # Для документов считаем файлы в файловой системе, для изображений - в БД
    if file_type == 'doc':
        if not content_type:
            # Пробуем определить по существующим папкам
            news_folder = get_content_folder_path('news', content_id, now)
            announcement_folder = get_content_folder_path('announcements', content_id, now)
            if os.path.exists(news_folder):
                content_type = 'news'
            elif os.path.exists(announcement_folder):
                content_type = 'announcements'
            else:
                # По умолчанию пробуем news
                content_type = 'news'
        
        # Считаем файлы в папке контента
        folder_path = get_content_folder_path(content_type, content_id, now)
        file_number = 1
        if os.path.exists(folder_path):
            existing_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.startswith(date_str) and 'документ' in f]
            file_number = len(existing_files) + 1
        filename = f"{date_str} - документ {file_number}{ext}"
    else:
        # Для изображений используем БД (они все еще сохраняются в БД)
        from models.models import File
        existing_files = File.query.filter_by(kind=file_type).filter(
            (File.news_id == content_id) | (File.announcement_id == content_id)
        ).count()
        file_number = existing_files + 1
        filename = f"{date_str} - {file_number}{ext}"
    
    return filename


def get_content_folder_path(content_type, content_id, publication_date=None):
    """
    Создает путь к папке контента в формате год/месяц/дата/номер_контента/
    
    Args:
        content_type: Тип контента ('news' или 'announcements')
        content_id: ID контента
        publication_date: Дата публикации (опционально)
    
    Returns:
        Путь к папке
    """
    target_date = publication_date if publication_date else datetime.now()
    
    year = target_date.strftime("%Y")
    month = target_date.strftime("%m")
    day = target_date.strftime("%d")
    
    folder_path = os.path.join('static', 'uploads', content_type, year, month, day, str(content_id))
    os.makedirs(folder_path, exist_ok=True)
    
    return folder_path


def save_image(file, content_type, content_id=None, publication_date=None, max_size=(1200, 1200), quality=85):
    """
    Сохраняет и оптимизирует изображение
    
    Args:
        file: Объект файла
        content_type: Тип контента ('news', 'announcements', etc.)
        content_id: ID контента (опционально)
        publication_date: Дата публикации (опционально)
        max_size: Максимальный размер изображения
        quality: Качество сжатия JPEG
    
    Returns:
        Имя сохраненного файла или None
    """
    if not file or not file.filename:
        return None
    
    try:
        if content_id:
            filename = generate_content_filename(file.filename, content_id, 'image')
        else:
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{uuid.uuid4()}{ext}"
        
        if not filename:
            return None
        
        if content_id:
            upload_folder = get_content_folder_path(content_type, content_id, publication_date)
        else:
            upload_folder = os.path.join('static', 'uploads', content_type)
            os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        optimize_image(file_path, max_size, quality)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения: {e}")
        return None


def save_document(file, content_type, content_id=None, publication_date=None):
    """
    Сохраняет документ
    
    Args:
        file: Объект файла
        content_type: Тип контента ('news', 'announcements', etc.)
        content_id: ID контента (опционально)
        publication_date: Дата публикации (опционально)
    
    Returns:
        Имя сохраненного файла или None
    """
    if not file or not file.filename:
        return None
    
    try:
        if content_id:
            filename = generate_content_filename(file.filename, content_id, 'doc', content_type)
        else:
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{uuid.uuid4()}{ext}"
        
        if not filename:
            return None
        
        if content_id:
            upload_folder = get_content_folder_path(content_type, content_id, publication_date)
        else:
            upload_folder = os.path.join('static', 'uploads', content_type)
            os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка при сохранении документа: {e}")
        return None


def optimize_image(file_path, max_size=(1200, 1200), quality=85):
    """
    Оптимизирует изображение
    
    Args:
        file_path: Путь к файлу изображения
        max_size: Максимальный размер
        quality: Качество сжатия JPEG
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        with PILImage.open(file_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка при оптимизации изображения {file_path}: {e}")
        return False


def get_file_url(filename, content_type, content_id):
    """
    Получает URL для файла с учетом структуры папок
    
    Args:
        filename: Имя файла
        content_type: Тип контента ('news' или 'announcements')
        content_id: ID контента
    
    Returns:
        URL файла или None
    """
    if not filename or not content_id:
        return None
    
    from models.models import News, Announcement
    
    if content_type == 'news':
        content = News.query.get(content_id)
    elif content_type == 'announcements':
        content = Announcement.query.get(content_id)
    else:
        return None
    
    if not content:
        return None
    
    target_date = content.publication_date if content.publication_date else content.created_at
    
    year = target_date.strftime("%Y")
    month = target_date.strftime("%m")
    day = target_date.strftime("%d")
    
    # Для документов используем роут скачивания, для изображений - прямой путь
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    is_document = ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.rtf', '.odt', '.ods', '.odp']
    
    if is_document:
        url = f"/{content_type}/download/{content_id}/{filename}"
    else:
        url = f"/static/uploads/{content_type}/{year}/{month}/{day}/{content_id}/{filename}"
    
    return url


def get_content_documents(content_type, content_id, publication_date=None):
    """
    Получает список документов из файловой системы для контента
    
    Args:
        content_type: Тип контента ('news' или 'announcements')
        content_id: ID контента
        publication_date: Дата публикации (опционально, если None, получается из БД)
    
    Returns:
        Список словарей с информацией о документах
    """
    if not content_id:
        return []
    
    try:
        # Если дата не передана, получаем из БД
        if publication_date is None:
            from models.models import News, Announcement
            if content_type == 'news':
                content = News.query.get(content_id)
            elif content_type == 'announcements':
                content = Announcement.query.get(content_id)
            else:
                return []
            
            if content:
                publication_date = content.publication_date if content.publication_date else content.created_at
        
        folder_path = get_content_folder_path(content_type, content_id, publication_date)
        if not os.path.exists(folder_path):
            return []
        
        documents = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                # Проверяем, что это документ (не изображение)
                is_document = ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.rtf', '.odt', '.ods', '.odp']
                if is_document and 'документ' in filename:
                    documents.append({
                        'filename': filename,
                        'url': get_file_url(filename, content_type, content_id),
                        'size': os.path.getsize(file_path)
                    })
        
        return sorted(documents, key=lambda x: x['filename'])
    except Exception as e:
        logger.error(f"Ошибка при получении документов для {content_type} {content_id}: {e}")
        return []

