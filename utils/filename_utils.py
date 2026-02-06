"""
Утилиты для безопасной обработки имен файлов с поддержкой русских букв
"""

import os
import re
import unicodedata


def safe_filename(filename):
    """
    Создает безопасное имя файла, сохраняя русские и другие Unicode символы
    
    Args:
        filename: Оригинальное имя файла
    
    Returns:
        Безопасное имя файла с сохранением русских букв
    """
    if not filename:
        return 'file'
    
    # Разделяем имя и расширение
    name, ext = os.path.splitext(filename)
    
    # Нормализуем Unicode (NFD -> NFC для корректной работы с русскими буквами)
    name = unicodedata.normalize('NFC', name)
    
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
    
    # Ограничиваем длину имени (255 символов для файловой системы)
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

