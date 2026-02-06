"""
Утилиты для обработки ошибок в API endpoints
"""
from flask import jsonify
import traceback
import logging

logger = logging.getLogger(__name__)

def handle_api_error(error, context=''):
    """
    Обработка ошибок в API endpoints
    
    Args:
        error: Объект исключения
        context: Контекст операции (например, 'При загрузке файла')
    
    Returns:
        JSON ответ с описанием ошибки и инструкциями
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Определяем тип ошибки и формируем ответ
    if isinstance(error, ValueError):
        return jsonify({
            'success': False,
            'error': error_message or 'Неверные данные',
            'error_type': 'ValidationError',
            'context': context,
            'instructions': [
                'Проверьте введенные данные',
                'Убедитесь, что все обязательные поля заполнены',
                'Проверьте формат данных'
            ]
        }), 400
    
    elif isinstance(error, PermissionError):
        return jsonify({
            'success': False,
            'error': 'Недостаточно прав для выполнения операции',
            'error_type': 'PermissionError',
            'context': context,
            'instructions': [
                'Убедитесь, что вы вошли в систему',
                'Проверьте права доступа',
                'Обратитесь к администратору'
            ]
        }), 403
    
    elif isinstance(error, FileNotFoundError):
        return jsonify({
            'success': False,
            'error': 'Файл не найден',
            'error_type': 'FileNotFoundError',
            'context': context,
            'instructions': [
                'Проверьте, что файл существует',
                'Попробуйте загрузить файл снова',
                'Если файл был удален, восстановите его из резервной копии'
            ]
        }), 404
    
    elif isinstance(error, IOError) or isinstance(error, OSError):
        return jsonify({
            'success': False,
            'error': 'Ошибка при работе с файлом',
            'error_type': 'IOError',
            'context': context,
            'instructions': [
                'Проверьте права доступа к файлам',
                'Убедитесь, что на диске достаточно места',
                'Попробуйте выполнить операцию снова'
            ]
        }), 500
    
    elif isinstance(error, KeyError):
        return jsonify({
            'success': False,
            'error': f'Отсутствует обязательный параметр: {error_message}',
            'error_type': 'KeyError',
            'context': context,
            'instructions': [
                'Проверьте, что все обязательные параметры переданы',
                'Убедитесь, что данные введены корректно'
            ]
        }), 400
    
    elif isinstance(error, Exception):
        # Логируем неизвестную ошибку
        logger.error(f'Необработанная ошибка в {context}: {error_type}: {error_message}')
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_message or 'Произошла ошибка при выполнении операции',
            'error_type': error_type,
            'context': context,
            'instructions': [
                'Попробуйте выполнить операцию снова',
                'Обновите страницу (Ctrl+F5)',
                'Если ошибка повторяется, сообщите администратору',
                'Укажите, какое действие вы пытались выполнить'
            ]
        }), 500
    
    else:
        return jsonify({
            'success': False,
            'error': 'Неизвестная ошибка',
            'error_type': 'Unknown',
            'context': context,
            'instructions': [
                'Попробуйте обновить страницу',
                'Если проблема сохраняется, сообщите администратору'
            ]
        }), 500


def validate_request_data(data, required_fields=None, optional_fields=None):
    """
    Валидация данных запроса
    
    Args:
        data: Словарь с данными
        required_fields: Список обязательных полей
        optional_fields: Список опциональных полей
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return False, f'Отсутствуют обязательные поля: {", ".join(missing_fields)}'
    
    if optional_fields:
        invalid_fields = [field for field in data.keys() if field not in (required_fields or []) + optional_fields]
        if invalid_fields:
            return False, f'Неизвестные поля: {", ".join(invalid_fields)}'
    
    return True, None


def safe_json_response(data, status_code=200):
    """
    Безопасное создание JSON ответа с обработкой ошибок
    
    Args:
        data: Данные для ответа
        status_code: HTTP статус код
    
    Returns:
        JSON ответ
    """
    try:
        return jsonify(data), status_code
    except Exception as e:
        logger.error(f'Ошибка при создании JSON ответа: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при формировании ответа',
            'instructions': [
                'Попробуйте повторить запрос',
                'Если проблема сохраняется, сообщите администратору'
            ]
        }), 500

