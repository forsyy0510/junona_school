#!/usr/bin/env python3
"""
Система управления файлами для проекта Site Junona
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
import json
import mimetypes
import re
import unicodedata
from database import db
from utils.logger import logger

class FileManager:
    """Класс для управления файлами в проекте"""
    
    def __init__(self, base_upload_path='static/uploads'):
        # IMPORTANT: use absolute path so uploads work независимо от текущей рабочей директории процесса.
        # file_manager.py находится в корне проекта рядом с папкой static/.
        try:
            project_root = os.path.abspath(os.path.dirname(__file__))
        except Exception:
            project_root = os.path.abspath('.')

        if os.path.isabs(base_upload_path):
            self.base_upload_path = base_upload_path
        else:
            self.base_upload_path = os.path.join(project_root, base_upload_path)
        self.allowed_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 
            'txt', 'rtf', 'htm', 'html', 'xml', 
            'zip', 'rar', '7z', 'sig'
        }
        self.image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
    
    def _safe_filename_preserve_unicode(self, filename):
        """Создает безопасное имя файла, сохраняя русские и другие Unicode символы"""
        if not filename:
            return 'file'
        
        # Разделяем имя и расширение
        name, ext = os.path.splitext(filename)
        
        # Нормализуем Unicode (NFD -> NFC для корректной работы с русскими буквами)
        try:
            name = unicodedata.normalize('NFC', name)
        except:
            pass
        
        # Удаляем опасные символы, но сохраняем русские буквы, цифры, латиницу и некоторые безопасные символы
        # Разрешаем: русские буквы, латинские буквы, цифры, пробелы, дефисы, подчеркивания, точки
        # Удаляем: / \ : * ? " < > | и другие опасные символы
        safe_chars_pattern = re.compile(r'[^\w\s\-\.а-яА-ЯёЁ]', re.UNICODE)
        name = safe_chars_pattern.sub('', name)
        
        # Заменяем множественные пробелы на одинарные
        name = re.sub(r'\s+', ' ', name)
        
        # Удаляем ведущие и завершающие точки, пробелы и дефисы
        name = name.strip('._ -')
        
        # Если имя стало пустым, используем дефолтное
        if not name:
            name = 'file'
        
        # Оставляем место для расширения
        max_name_length = 200
        if len(name) > max_name_length:
            name = name[:max_name_length]
        
        # Обрабатываем расширение
        ext = ext.lower() if ext else ''
        # Удаляем опасные символы из расширения
        ext = re.sub(r'[^\w\.]', '', ext)
        
        # Объединяем имя и расширение
        result = name + ext
        
        # Финальная проверка - если результат пустой или содержит только точки
        if not result or result.replace('.', '').strip() == '':
            result = 'file' + ext
        
        return result
        
    def create_section_folder(self, section_name):
        """Создает папку для раздела если её нет"""
        # Создаем папку в структуре: static/uploads/section_name/
        section_folder = os.path.join(self.base_upload_path, section_name)
        os.makedirs(section_folder, exist_ok=True)
        return section_folder
    
    def create_info_folder_path(self, section_endpoint, upload_date=None):
        """Создает путь к папке раздела Сведения в формате год/раздел/"""
        # Используем дату загрузки если указана, иначе текущую дату
        if upload_date is None:
            from datetime import datetime
            upload_date = datetime.now()
        elif isinstance(upload_date, str):
            from datetime import datetime
            upload_date = datetime.fromisoformat(upload_date)
        
        year = upload_date.strftime("%Y")
        
        # Создаем путь: static/uploads/info/год/раздел/
        folder_path = os.path.join(self.base_upload_path, 'info', year, section_endpoint)
        
        # Создаем папку если её нет
        os.makedirs(folder_path, exist_ok=True)
        
        logger.debug(f'Created info folder path: {folder_path}')
        return folder_path
    
    def create_documents_folder(self, section_name, date=None):
        """Создает иерархическую папку для документов по дате (год/месяц/день)"""
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.fromisoformat(date)
        
        year = date.strftime('%Y')
        month = date.strftime('%m')
        day = date.strftime('%d')
        
        # Создаем структуру: static/uploads/documents/year/month/day/
        folder_path = os.path.join(self.base_upload_path, 'documents', year, month, day)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
    
    def generate_document_filename(self, original_filename, section_name, date=None):
        """Генерирует имя файла документа в формате день.месяц.год - номер.расширение"""
        if not original_filename:
            return None
            
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.fromisoformat(date)
        
        # Получаем расширение
        name, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        
        # Создаем безопасное имя
        safe_name = secure_filename(name)
        if not safe_name:
            safe_name = 'document'
        
        # Формат: день.месяц.год - номер.расширение
        date_str = date.strftime('%d.%m.%Y')
        
        # Создаем папку для документов
        documents_folder = self.create_documents_folder(section_name, date)
        
        # Ищем следующий номер
        counter = 1
        while True:
            filename = f"{date_str} - {counter}{ext}"
            file_path = os.path.join(documents_folder, filename)
            if not os.path.exists(file_path):
                break
            counter += 1
        
        return filename
    
    def generate_unique_filename(self, original_filename, section_name):
        """Генерирует уникальное имя файла"""
        if not original_filename:
            return None
            
        # Получаем расширение
        name, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        
        # Создаем безопасное имя
        safe_name = secure_filename(name)
        if not safe_name:
            safe_name = 'file'
        
        # Генерируем уникальное имя
        unique_id = str(uuid.uuid4())[:8]
        unique_filename = f"{safe_name}_{unique_id}{ext}"
        
        # Проверяем, что файл не существует
        section_folder = self.create_section_folder(section_name)
        file_path = os.path.join(section_folder, unique_filename)
        
        counter = 1
        while os.path.exists(file_path):
            unique_filename = f"{safe_name}_{unique_id}_{counter}{ext}"
            file_path = os.path.join(section_folder, unique_filename)
            counter += 1
            
        return unique_filename
    
    def generate_info_filename(self, original_filename, section_endpoint, file_type='doc'):
        """Генерирует имя файла в формате год - номер файла для раздела Сведения"""
        if not original_filename:
            return None
        
        # Получаем текущую дату
        from datetime import datetime
        now = datetime.now()
        year = now.strftime("%Y")
        
        # Получаем расширение файла
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        
        # Подсчитываем количество уже загруженных файлов для этого раздела
        # Lazy import to avoid circular imports at module load time (info/__init__ imports routes).
        from models.models import InfoFile
        existing_files = InfoFile.query.filter_by(section_endpoint=section_endpoint).count()
        file_number = existing_files + 1
        
        # Формируем имя файла
        if file_type == 'image':
            filename = f"{year} - {file_number}{ext}"
        else:
            filename = f"{year} - документ {file_number}{ext}"
        
        return filename
    
    def is_allowed_file(self, filename):
        """Проверяет, разрешен ли тип файла"""
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in self.allowed_extensions
    
    def is_image_file(self, filename):
        """Проверяет, является ли файл изображением"""
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in self.image_extensions
    
    def optimize_image(self, file_path, max_size=(2400, 2400), quality=95):
        """Оптимизирует изображение без заметной потери качества.

        ВАЖНО: не конвертируем всё в JPEG — сохраняем исходный формат по расширению.
        """
        try:
            _, ext = os.path.splitext(file_path or '')
            ext = (ext or '').lower()
            if ext in ('.jpg', '.jpeg'):
                fmt = 'JPEG'
            elif ext == '.png':
                fmt = 'PNG'
            elif ext == '.webp':
                fmt = 'WEBP'
            else:
                # Неизвестный формат — оставляем как есть
                return True

            with PILImage.open(file_path) as img:
                # PNG с прозрачностью не переводим в JPEG, поэтому RGB-конверсию делаем только для JPEG/WEBP.
                if fmt in ('JPEG', 'WEBP') and img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Уменьшаем только если реально больше max_size
                img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

                save_kwargs = {'optimize': True}
                if fmt == 'JPEG':
                    save_kwargs.update({'quality': int(quality), 'progressive': True})
                elif fmt == 'WEBP':
                    save_kwargs.update({'quality': max(70, min(int(quality), 100))})

                img.save(file_path, fmt, **save_kwargs)
            return True
        except Exception as e:
            logger.error(f"Ошибка при оптимизации изображения {file_path}: {e}")
            return False
    
    def save_file(self, file, section_name, field_name=None, optimize_images=True):
        """Сохраняет файл в папку раздела"""
        if not file or not file.filename:
            return None
            
        if not self.is_allowed_file(file.filename):
            raise ValueError(f"Недопустимый тип файла: {file.filename}")
        
        # Создаем папку для раздела
        section_folder = self.create_section_folder(section_name)
        
        # Используем оригинальное имя файла, делаем его безопасным
        original_filename = secure_filename(file.filename)
        if not original_filename:
            original_filename = 'file'
        
        # Проверяем, существует ли файл с таким именем
        file_path = os.path.join(section_folder, original_filename)
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_filename)
            original_filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(section_folder, original_filename)
            counter += 1
        
        # Сохраняем файл
        file.save(file_path)
        
        # Оптимизируем изображения если нужно
        if optimize_images and self.is_image_file(original_filename):
            self.optimize_image(file_path)
        
        # Получаем информацию о файле
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        is_image = self.is_image_file(original_filename)
        
        return {
            'filename': original_filename,
            'original_name': file.filename,
            'file_path': file_path,
            'section': section_name,
            'url': f'/info/download_file/{section_name}/{original_filename}',
            'is_image': is_image,
            'size': file_size,
            'mime_type': mime_type,
            'created_at': datetime.now().isoformat()
        }
    
    def save_info_file(self, file, section_endpoint, field_name=None, optimize_images=True):
        """Сохраняет файл в раздел Сведения только в файловую систему (без хранения содержимого в БД)"""
        if not file or not file.filename:
            return None
            
        if not self.is_allowed_file(file.filename):
            raise ValueError(f"Недопустимый тип файла: {file.filename}")
        
        # Определяем тип файла
        is_image = self.is_image_file(file.filename)
        
        # Определяем, является ли файл документом (docx, xlsx и т.п.)
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()
        is_document = ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.rtf', '.odt', '.ods', '.odp', '.sig']
        
        # Используем оригинальное имя файла, сохраняя русские символы
        original_filename = self._safe_filename_preserve_unicode(file.filename)
        if not original_filename:
            original_filename = 'file'
        
        # Создаем папку для раздела в новой структуре
        upload_date = datetime.now()
        folder_path = self.create_info_folder_path(section_endpoint, upload_date)
        
        # Для Excel меню (field_name == 'menu_file') лучше перезаписывать файл с тем же именем,
        # чтобы повторная загрузка обновляла контент (и не создавались _1/_2).
        reused_existing = False
        if field_name == 'menu_file':
            filename = original_filename
            file_path = os.path.join(folder_path, filename)
            try:
                file.save(file_path)  # overwrite if exists
            except Exception as e:
                logger.error(f"Ошибка при сохранении файла меню {filename}: {e}")
                raise
        else:
            # Проверяем, существует ли файл с таким именем, и добавляем номер если нужно
            filename = original_filename
            file_path = os.path.join(folder_path, filename)
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                file_path = os.path.join(folder_path, filename)
                counter += 1
            
            # Сохраняем файл
            file.save(file_path)
        
        # Оптимизируем изображения если нужно (только если сохраняли новый файл)
        if optimize_images and is_image and not reused_existing:
            self.optimize_image(file_path)
        
        # Получаем информацию о файле с диска
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Определяем URL для скачивания
        if section_endpoint == 'food' or field_name == 'menu_file':
            download_url = f'/food/{filename}'
        else:
            # Проверяем, является ли раздел sidebar разделом
            try:
                # Lazy import to avoid circular imports at module load time.
                from info.models import InfoSection
                section = InfoSection.query.filter_by(endpoint=section_endpoint).first()
                if section and section.url and section.url.startswith('/sidebar/'):
                    download_url = f'/sidebar/download_file/{section_endpoint}/{filename}'
                else:
                    download_url = f'/info/download_file/{section_endpoint}/{filename}'
            except Exception as e:
                # Логируем ошибку для диагностики, но не скрываем её
                error_msg = str(e).lower()
                if 'no such column' in error_msg or 'operationalerror' in error_msg:
                    # Ошибка БД - возможно, схема не обновлена
                    logger.warning(f"Ошибка БД при проверке типа раздела для {section_endpoint}: {e}")
                else:
                    # Другие ошибки - логируем как ошибку
                    logger.error(f"Ошибка при проверке типа раздела для {section_endpoint}: {e}")
                # Используем стандартный URL в случае ошибки
                download_url = f'/info/download_file/{section_endpoint}/{filename}'

        return {
            'filename': filename,
            'original_name': file.filename,
            'file_path': file_path,
            'section': section_endpoint,
            'url': download_url,
            'is_image': is_image,
            'size': file_size,
            'mime_type': mime_type,
            'created_at': upload_date.isoformat()
        }
    
    def save_document(self, file, section_name, date=None, optimize_images=True):
        """Сохраняет документ с оригинальным именем в папку проекта"""
        if not file or not file.filename:
            return None
            
        if not self.is_allowed_file(file.filename):
            raise ValueError(f"Недопустимый тип файла: {file.filename}")
        
        # Создаем папку для раздела (простая структура)
        section_folder = self.create_section_folder(section_name)
        
        # Используем оригинальное имя файла, делаем его безопасным
        original_filename = secure_filename(file.filename)
        if not original_filename:
            original_filename = 'document'
        
        # Проверяем, существует ли файл с таким именем
        file_path = os.path.join(section_folder, original_filename)
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_filename)
            original_filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(section_folder, original_filename)
            counter += 1
        
        # Сохраняем файл
        file.save(file_path)
        
        # Оптимизируем изображения если нужно
        if optimize_images and self.is_image_file(original_filename):
            self.optimize_image(file_path)
        
        return {
            'filename': original_filename,
            'original_name': file.filename,
            'file_path': file_path,
            'section': section_name,
            'url': f'/info/download_file/{section_name}/{original_filename}',
            'is_image': self.is_image_file(original_filename),
            'size': os.path.getsize(file_path),
            'created_at': datetime.now().isoformat()
        }
    
    def delete_file(self, filename, section_name, field_name=None):
        """Удаляет файл из папки, БД и form_data"""
        try:
            logger.debug(f"Удаление файла {filename} из раздела {section_name}, поле: {field_name}")
            
            # Ищем файл в БД для определения пути (с обработкой ошибок, если колонок нет)
            info_file = None
            try:
                # Lazy import to avoid circular imports at module load time.
                from models.models import InfoFile
                query = InfoFile.query.filter_by(
                    filename=filename,
                    section_endpoint=section_name
                )
                if field_name:
                    query = query.filter_by(field_name=field_name)
                info_file = query.first()
            except Exception as e:
                # Если ошибка из-за отсутствующих колонок в БД, пропускаем проверку БД
                if 'no such column' in str(e).lower() or 'file_data' in str(e).lower():
                    logger.warning(
                        "Поля file_data/stored_in_db еще не добавлены в БД. "
                        "Пропускаю поиск файла в InfoFile. Будет поиск в файловой системе."
                    )
                    info_file = None
                else:
                    logger.error(f"Ошибка при поиске файла в InfoFile: {e}")
                    info_file = None
            
            file_deleted = False
            
            if info_file:
                # Проверяем, хранится ли файл в БД (с обработкой ошибок)
                stored_in_db = False
                try:
                    stored_in_db = getattr(info_file, 'stored_in_db', False)
                except AttributeError:
                    stored_in_db = False
                
                # Если файл хранится в БД, удаляем только из БД
                if stored_in_db:
                    logger.info(f"Удаление файла из БД: {filename} (размер: {getattr(info_file, 'file_size', 0)} байт)")
                else:
                    # Если файл хранится в файловой системе, удаляем с диска
                    file_path = getattr(info_file, 'file_path', None)
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"Файл удален с диска: {file_path}")
                            file_deleted = True
                        except Exception as e:
                            logger.warning(f"Не удалось удалить файл с диска {file_path}: {e}")
                
                # Удаляем запись из БД
                try:
                    db.session.delete(info_file)
                    db.session.commit()
                    logger.info(f"Запись о файле удалена из БД: {filename}")
                    file_deleted = True
                except Exception as e:
                    logger.error(f"Ошибка при удалении из БД: {e}")
                    db.session.rollback()
            else:
                # Если файл не найден в БД (документ), ищем в файловой системе
                # Ищем в новой структуре info/год/раздел/
                found_path = None
                logger.debug(f"Файл не найден в БД, ищем в файловой системе: {filename}, раздел: {section_name}")
                for root, dirs, files_list in os.walk(os.path.join(self.base_upload_path, 'info')):
                    if filename in files_list:
                        found_path = os.path.join(root, filename)
                        if os.path.exists(found_path):
                            try:
                                os.remove(found_path)
                                logger.info(f"Файл удален из файловой системы: {found_path}")
                                file_deleted = True
                                break
                            except Exception as e:
                                logger.warning(f"Не удалось удалить файл {found_path}: {e}")
                
                # Если не найден в новой структуре, проверяем другие возможные пути
                if not file_deleted:
                    possible_paths = [
                        os.path.join(self.base_upload_path, section_name, filename),
                        os.path.join(self.base_upload_path, 'pages', section_name, filename)
                    ]

                    # Для файлов меню питания (старый путь): static/uploads/nutrition/menus/<filename>
                    if section_name == 'food' and field_name == 'menu_file':
                        possible_paths.append(os.path.join(self.base_upload_path, 'nutrition', 'menus', filename))
                    
                    for file_path in possible_paths:
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info(f"Файл удален: {file_path}")
                                file_deleted = True
                                break
                            except Exception as e:
                                logger.warning(f"Не удалось удалить файл {file_path}: {e}")
                
                # Если все еще не найден, ищем во всех папках uploads
                if not file_deleted:
                    logger.debug(f"Файл не найден в стандартных местах, ищем во всех папках uploads: {filename}")
                    for root, dirs, files_list in os.walk(self.base_upload_path):
                        if filename in files_list:
                            found_path = os.path.join(root, filename)
                            if os.path.exists(found_path):
                                try:
                                    os.remove(found_path)
                                    logger.info(f"Файл удален из файловой системы (глобальный поиск): {found_path}")
                                    file_deleted = True
                                    break
                                except Exception as e:
                                    logger.warning(f"Не удалось удалить файл {found_path}: {e}")
                
                if not file_deleted:
                    logger.warning(f"Файл не найден в файловой системе для удаления: {filename}, раздел: {section_name}")
            
            # Удаляем файл из form_data в section.text
            try:
                # Lazy import to avoid circular imports at module load time.
                from info.models import InfoSection
                section = InfoSection.query.filter_by(endpoint=section_name).first()
                if section and section.text:
                    import json
                    data = json.loads(section.text)
                    if 'form_data' in data:
                        form_data = data['form_data']
                        updated = False
                        
                        # Удаляем из конкретного поля, если указано
                        if field_name and field_name in form_data:
                            field_value = form_data[field_name]
                            if isinstance(field_value, str):
                                # Удаляем файл из строки с файлами
                                files = [f.strip() for f in field_value.split(',') if f.strip()]
                                new_files = []
                                for file_url in files:
                                    # Извлекаем имя файла из URL (убираем display_name после |)
                                    file_url_clean = file_url.split('|')[0].strip() if '|' in file_url else file_url.strip()
                                    file_url_filename = file_url_clean.split('/')[-1].strip()
                                    if file_url_filename != filename:
                                        new_files.append(file_url)
                                if len(new_files) != len(files):
                                    form_data[field_name] = ', '.join(new_files) if new_files else ''
                                    updated = True
                                    logger.info(f"Файл удален из поля {field_name} в form_data")
                            elif isinstance(field_value, list):
                                # Поле file_with_name: массив объектов {url, displayName, filename}
                                def _file_match(f):
                                    if isinstance(f, dict):
                                        fn = f.get('filename') or (f.get('url') or '').split('/')[-1].strip()
                                        return fn == filename
                                    return False
                                new_list = [f for f in field_value if not _file_match(f)]
                                if len(new_list) != len(field_value):
                                    form_data[field_name] = new_list
                                    updated = True
                                    logger.info(f"Файл удален из поля {field_name} (массив) в form_data")
                            elif isinstance(field_value, dict):
                                # Один файл в виде объекта
                                fn = field_value.get('filename') or (field_value.get('url') or '').split('/')[-1].strip()
                                if fn == filename:
                                    form_data[field_name] = ''
                                    updated = True
                                    logger.info(f"Файл удален из поля {field_name} (объект) в form_data")
                        
                        # Удаляем из списка files (для раздела main)
                        if 'files' in form_data and isinstance(form_data['files'], list):
                            original_count = len(form_data['files'])
                            form_data['files'] = [
                                f for f in form_data['files'] 
                                if isinstance(f, dict) and f.get('filename') != filename
                            ]
                            if len(form_data['files']) != original_count:
                                updated = True
                                logger.info(f"Файл удален из списка files в form_data")
                        
                        # Удаляем из всех полей, содержащих этот файл (если field_name не указан или для очистки дубликатов)
                        # Если field_name указан, удаляем только из этого поля
                        # Если не указан, удаляем из всех полей (для очистки дубликатов)
                        if not field_name:
                            # Удаляем из всех полей, где может быть этот файл
                            for field_key, field_value in form_data.items():
                                if field_key == 'files':
                                    continue
                                if isinstance(field_value, str) and filename in field_value:
                                    files = [f.strip() for f in field_value.split(',') if f.strip()]
                                    new_files = []
                                    for file_url in files:
                                        # Извлекаем имя файла из URL
                                        file_url_clean = file_url.split('|')[0].strip()
                                        file_url_filename = file_url_clean.split('/')[-1].strip()
                                        if file_url_filename != filename:
                                            new_files.append(file_url)
                                    if len(new_files) != len(files):
                                        form_data[field_key] = ', '.join(new_files) if new_files else ''
                                        updated = True
                                        logger.info(f"Файл удален из поля {field_key} в form_data")
                        
                        if updated:
                            data['form_data'] = form_data
                            section.text = json.dumps(data, ensure_ascii=False)
                            try:
                                db.session.commit()
                                logger.info(f"Файл удален из form_data раздела {section_name}")
                            except Exception as e:
                                logger.error(f"Ошибка при обновлении form_data: {e}")
                                db.session.rollback()
            except Exception as e:
                logger.error(f"Ошибка при удалении файла из form_data: {e}")
            
            if file_deleted or info_file:
                return True
            else:
                logger.warning(f"Файл не найден: {filename} в разделе {section_name}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {filename}: {e}")
            return False
    
    def get_file_info(self, filename, section_name):
        """Получает информацию о файле"""
        # Пробуем новую структуру папок (uploads/section_name)
        file_path = os.path.join(self.base_upload_path, section_name, filename)
        if not os.path.exists(file_path):
            # Пробуем старую структуру (pages/section_name)
            file_path = os.path.join(self.base_upload_path, 'pages', section_name, filename)
            if not os.path.exists(file_path):
                return None
            
        stat = os.stat(file_path)
        return {
            'filename': filename,
            'file_path': file_path,
            'size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'is_image': self.is_image_file(filename),
            'url': f'/info/download_file/{section_name}/{filename}'
        }
    
    def get_section_files(self, section_name, field_name=None):
        """Получает список всех файлов в разделе из файловой системы"""
        try:
            files = []
            
            # Пробуем новую структуру папок
            section_folder = os.path.join(self.base_upload_path, section_name)
            if os.path.exists(section_folder):
                for filename in os.listdir(section_folder):
                    file_path = os.path.join(section_folder, filename)
                    if os.path.isfile(file_path):
                        file_info = self.get_file_info(filename, section_name)
                        if file_info:
                            files.append(file_info)
            
            # Пробуем старую структуру папок
            old_section_folder = os.path.join(self.base_upload_path, 'pages', section_name)
            if os.path.exists(old_section_folder):
                for filename in os.listdir(old_section_folder):
                    file_path = os.path.join(old_section_folder, filename)
                    if os.path.isfile(file_path):
                        file_info = self.get_file_info(filename, section_name)
                        if file_info:
                            files.append(file_info)
            
            return sorted(files, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Ошибка при получении файлов раздела {section_name}: {e}")
            return []
    
    def get_section_files_from_db(self, section_name, field_name=None):
        """Получает список файлов раздела из базы данных с проверкой существования.
        ПРИМЕЧАНИЕ: Это метод только для ЧТЕНИЯ. Он больше не удаляет файлы и не обновляет пути автоматически (side-effects removed).
        """
        try:
            files = []
            
            # Получаем файлы из базы данных
            # Lazy import to avoid circular imports at module load time.
            from models.models import InfoFile
            query = InfoFile.query.filter_by(section_endpoint=section_name)
            if field_name:
                query = query.filter_by(field_name=field_name)
            info_files = query.all()
            
            for info_file in info_files:
                # Проверяем существование файла по полному пути
                file_exists = False
                actual_file_path = None
                if (hasattr(info_file, 'file_path') and info_file.file_path and 
                    os.path.exists(info_file.file_path)):
                    file_exists = True
                    actual_file_path = info_file.file_path
                
                # Если файл не найден по полному пути, ищем в файловой системе (READ ONLY check)
                if not file_exists:
                    # Ищем в новой структуре info/год/раздел/
                    found_path = None
                    for root, dirs, filenames in os.walk(os.path.join(self.base_upload_path, 'info')):
                        if info_file.filename in filenames:
                            found_path = os.path.join(root, info_file.filename)
                            if os.path.exists(found_path):
                                # Мы нашли файл, но НЕ обновляем БД здесь (getter shouldn't mutate)
                                # Сохраняем путь локально для получения актуального размера файла
                                file_exists = True
                                actual_file_path = found_path
                                break
                    
                    # Если не найден в новой структуре, проверяем старую
                    if not file_exists:
                        old_paths = [
                            os.path.join(self.base_upload_path, section_name, info_file.filename),
                            os.path.join(self.base_upload_path, 'pages', section_name, info_file.filename)
                        ]
                        for old_path in old_paths:
                            if os.path.exists(old_path):
                                file_exists = True
                                actual_file_path = old_path
                                break
                    
                # Если файл не найден нигде - пропускаем его в выдаче, но НЕ УДАЛЯЕМ из БД
                if not file_exists:
                    # logger.warning(f"Файл есть в БД, но не найден на диске: {info_file.filename}")
                    continue
                
                # Получаем актуальный размер файла с диска, если путь известен
                file_size = info_file.file_size
                if actual_file_path and os.path.exists(actual_file_path):
                    try:
                        file_size = os.path.getsize(actual_file_path)
                    except (OSError, IOError):
                        pass
                
                # Используем display_name, если установлен, иначе original_filename
                display_name = info_file.display_name if info_file.display_name else (info_file.original_filename or info_file.filename)
                
                # Определяем URL для скачивания
                # Проверяем, является ли раздел sidebar разделом
                download_url = None
                try:
                    from info.models import InfoSection
                    section = InfoSection.query.filter_by(endpoint=section_name).first()
                    if section and section.url and section.url.startswith('/sidebar/'):
                        download_url = f'/sidebar/download_file/{section_name}/{info_file.filename}'
                except Exception as e:
                    # Если не удалось проверить, используем стандартный URL
                    logger.debug(f"Не удалось определить тип раздела для {section_name}: {e}")
                
                # Если не определили как sidebar, используем метод get_download_url
                if not download_url:
                    try:
                        download_url = info_file.get_download_url()
                    except Exception as e:
                        # Если метод get_download_url не работает, формируем URL вручную
                        logger.debug(f"Ошибка при вызове get_download_url для {info_file.filename}: {e}")
                        download_url = f'/info/download_file/{section_name}/{info_file.filename}'
                
                file_info = {
                    'id': info_file.id,
                    'filename': info_file.filename,
                    'original_filename': info_file.original_filename or info_file.filename,
                    'display_name': display_name,
                    'url': download_url,
                    'file_size': file_size,
                    'mime_type': info_file.mime_type,
                    'is_image': info_file.is_image,
                    'upload_date': info_file.upload_date.isoformat(),
                    'section_endpoint': info_file.section_endpoint,
                    'field_name': info_file.field_name
                }
                files.append(file_info)
            
            return sorted(files, key=lambda x: x['upload_date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Ошибка при получении файлов раздела {section_name}: {e}")
            return []
    
    def get_file_by_id(self, file_id):
        """Получает файл по ID из базы данных"""
        try:
            # Lazy import to avoid circular imports at module load time.
            from models.models import InfoFile
            info_file = InfoFile.query.get(file_id)
            if (info_file and hasattr(info_file, 'file_path') and 
                info_file.file_path and os.path.exists(info_file.file_path)):
                return info_file
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении файла по ID {file_id}: {e}")
            return None
    
    def update_file_display_name(self, file_id, display_name):
        """Обновляет отображаемое имя файла (не изменяет original_filename)"""
        try:
            # Lazy import to avoid circular imports at module load time.
            from models.models import InfoFile
            info_file = InfoFile.query.get(file_id)
            if info_file:
                # Обновляем только display_name, original_filename остается неизменным
                info_file.display_name = display_name if display_name else info_file.original_filename
                
                # Также обновляем form_data в section.text для правильного отображения в шаблоне
                try:
                    # Lazy import to avoid circular imports at module load time.
                    from info.models import InfoSection
                    section = InfoSection.query.filter_by(endpoint=info_file.section_endpoint).first()
                    if section and section.text:
                        import json
                        data = json.loads(section.text)
                        if 'form_data' in data:
                            form_data = data['form_data']
                            updated = False
                            
                            # Обновляем во всех полях, содержащих этот файл
                            for field_key, field_value in form_data.items():
                                if isinstance(field_value, str) and info_file.filename in field_value:
                                    # Парсим файлы из строки
                                    files = [f.strip() for f in field_value.split(',') if f.strip()]
                                    new_files = []
                                    for file_url in files:
                                        file_url_clean = file_url.split('|')[0] if '|' in file_url else file_url
                                        file_url_filename = file_url_clean.split('/')[-1]
                                        if file_url_filename == info_file.filename:
                                            # Обновляем имя файла в URL
                                            new_file_url = f"{file_url_clean}|{display_name}"
                                            new_files.append(new_file_url)
                                            updated = True
                                        else:
                                            new_files.append(file_url)
                                    
                                    if updated:
                                        form_data[field_key] = ', '.join(new_files) if new_files else ''
                            
                            if updated:
                                data['form_data'] = form_data
                                section.text = json.dumps(data, ensure_ascii=False)
                except Exception as e:
                    logger.debug(f"Ошибка при обновлении form_data: {e}")
                
                db.session.commit()
                logger.debug(f"Обновлено display_name для файла {info_file.filename}: {display_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении имени файла {file_id}: {e}")
            db.session.rollback()
            return False
    
    def _extract_used_files(self):
        """Извлекает список используемых файлов из базы данных"""
        used_files = set()
        # Lazy import to avoid circular imports at module load time.
        from info.models import InfoSection
        sections = InfoSection.query.all()
        
        for section in sections:
            section_files = self._extract_section_files(section)
            used_files.update(section_files)
        
        return used_files
    
    def _extract_section_files(self, section):
        """Извлекает файлы из раздела"""
        if not section.text:
            return []
        
        try:
            data = json.loads(section.text)
            if 'form_data' not in data:
                return []
            
            files = []
            for field_value in data['form_data'].values():
                if isinstance(field_value, str) and field_value.startswith('/download_file/'):
                    filename = field_value.split('/')[-1]
                    files.append((section.endpoint, filename))
            
            return files
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _clean_section_directory(self, section_name, used_files):
        """Очищает директорию раздела от неиспользуемых файлов"""
        # Пробуем новую структуру папок
        section_path = os.path.join(self.base_upload_path, 'pages', section_name)
        if not os.path.isdir(section_path):
            # Пробуем старую структуру
            section_path = os.path.join(self.base_upload_path, section_name)
            if not os.path.isdir(section_path):
                return 0
        
        cleaned_count = 0
        for filename in os.listdir(section_path):
            file_path = os.path.join(section_path, filename)
            if os.path.isfile(file_path) and (section_name, filename) not in used_files:
                if self._remove_file_safely(file_path, section_name, filename):
                    cleaned_count += 1
        
        return cleaned_count
    
    def _remove_file_safely(self, file_path, section_name, filename):
        """Безопасно удаляет файл с обработкой ошибок"""
        try:
            os.remove(file_path)
            logger.info(f"Удален неиспользуемый файл: {section_name}/{filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {file_path}: {e}")
            return False

    def clean_orphaned_files(self):
        """Удаляет файлы, которые не используются в базе данных"""
        used_files = self._extract_used_files()
        cleaned_count = 0
        
        if not os.path.exists(self.base_upload_path):
            return cleaned_count
        
        # Очищаем папки в новой структуре (pages/)
        pages_path = os.path.join(self.base_upload_path, 'pages')
        if os.path.exists(pages_path):
            for section_name in os.listdir(pages_path):
                cleaned_count += self._clean_section_directory(section_name, used_files)
        
        # Очищаем папки в старой структуре
        for section_name in os.listdir(self.base_upload_path):
            if section_name != 'pages':  # Пропускаем папку pages
                cleaned_count += self._clean_section_directory(section_name, used_files)
        
        return cleaned_count

# Создаем глобальный экземпляр менеджера файлов
file_manager = FileManager()
