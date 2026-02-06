"""
Новые маршруты для информационных страниц с улучшенной системой
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required
from . import info_bp
from .models import InfoSection
from database import db
import os
import json
import uuid
from datetime import datetime
from file_manager import file_manager
from utils.logger import logger


# Маппинг новых endpoint'ов согласно методическим рекомендациям 2024
ENDPOINT_MAPPING = {
    'common': 'main',  # Основные сведения
    'struct': 'structure',  # Структура
    'document': 'documents',  # Документы
    'education': 'education',  # Образование (без изменений)
    'eduStandarts': 'standards',  # Образовательные стандарты
    'managers': 'management',  # Руководство
    'employees': 'teachers',  # Педагогический состав
    'objects': 'facilities',  # МТО
    'grants': 'scholarships',  # Стипендии
    'paid_edu': 'paid-services',  # Платные услуги
    'budget': 'finance',  # Финансы
    'vacant': 'vacancies',  # Вакансии
    'inter': 'international',  # Международное сотрудничество
    'catering': 'food',  # Питание
}

@info_bp.route('/<section_endpoint>')
def show_section_new(section_endpoint):
    """Показать информационный раздел"""
    # Проверяем маппинг новых endpoint'ов
    actual_endpoint = ENDPOINT_MAPPING.get(section_endpoint, section_endpoint)
    
    section = InfoSection.query.filter_by(endpoint=actual_endpoint).first()
    
    # Автоматическое создание раздела "Образование", если его нет
    if not section and actual_endpoint == 'education':
        logger.info(f"Автоматическое создание раздела 'Образование' (endpoint: {actual_endpoint})")
        try:
            section = InfoSection(
                endpoint='education',
                url='/sveden/education',
                title='Образование',
                text=json.dumps({
                    'form_data': {
                        'title': 'Образование',
                        'implemented_programs': '',
                        'adapted_programs': '',
                        'curriculum_noo': '',
                        'curriculum_ooo': '',
                        'curriculum_soo': '',
                        'calendar_schedule': '',
                        'student_numbers_noo': '',
                        'student_numbers_ooo': '',
                        'student_numbers_soo': '',
                        'student_numbers_document': '',
                        'education_languages': '',
                        'professional_programs': '',
                        'graduate_employment': ''
                    }
                }, ensure_ascii=False),
                content_blocks=json.dumps([], ensure_ascii=False)
            )
            db.session.add(section)
            db.session.commit()
            logger.info("Раздел 'Образование' успешно создан")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании раздела 'Образование': {e}")
            flash('Ошибка при создании раздела', 'error')
            return redirect(url_for('main.index'))
    
    if not section:
        flash('Раздел не найден', 'error')
        return redirect(url_for('main.index'))
    
    # Автоматически очищаем несуществующие файлы перед отображением (только если есть данные)
    if section.text:
        try:
            _update_form_data_file_names(section)
            cleaned_count, processed = _clean_section_files(section)
            if processed and cleaned_count > 0:
                logger.info(f"Автоматически очищено {cleaned_count} несуществующих файлов из раздела {section_endpoint}")
        except Exception as e:
            logger.error(f"Ошибка при автоматической очистке файлов: {e}")
    
    from flask import make_response
    # Передаем текущую дату для фильтрации блюд в архиве
    today = datetime.now().strftime('%d.%m.%Y')

    # Флаг для различия поведения разметки между /sveden/* и /info/*
    try:
        current_path = request.path or ''
    except Exception:
        current_path = ''
    is_sveden = current_path.startswith('/sveden/')

    # Подразделы: показываем карточки дочерних разделов, если у них form_data.parent == actual_endpoint.
    # ВАЖНО: используем actual_endpoint, потому что URL может быть /sveden/catering,
    # а реальный endpoint в БД — 'food'.
    children = []
    try:
        all_sections = InfoSection.query.all()

        def _safe_form_data(sec):
            try:
                td = json.loads(sec.text) if sec and sec.text else {}
                if not isinstance(td, dict):
                    return {}
                fd = td.get('form_data', {})
                return fd if isinstance(fd, dict) else {}
            except Exception:
                return {}

        def _normalize_parent(parent_val):
            if not parent_val:
                return None
            if isinstance(parent_val, str):
                p = parent_val.strip()
                if p.startswith('/sidebar/'):
                    p = p.replace('/sidebar/', '')
                return p or None
            return None

        def _sort_key(sec):
            fd = _safe_form_data(sec)
            order = 10**9
            try:
                order = int(fd.get('order') or 0) or 10**9
            except Exception:
                order = 10**9
            title = (sec.title or '').strip().lower()
            return (order, title, sec.endpoint or '')

        direct_children = []
        for s in all_sections:
            try:
                if not s or not s.endpoint or s.endpoint == actual_endpoint:
                    continue
                fd = _safe_form_data(s)
                parent_val = _normalize_parent(fd.get('parent'))
                if parent_val == actual_endpoint:
                    direct_children.append(s)
            except Exception:
                continue

        children = sorted(direct_children, key=_sort_key)
    except Exception:
        children = []

    response = make_response(
        render_template(
            'info/section.html',
            section=section,
            children=children,
            today=today,
            is_sveden=is_sveden,
        )
    )
    
    # Отключаем кэширование
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# Редиректы для обратной совместимости со старыми URL /info/*
@info_bp.route('/main')
def redirect_main():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/common', code=301)

@info_bp.route('/structure')
def redirect_structure():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/struct', code=301)

@info_bp.route('/documents')
def redirect_documents():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/document', code=301)

@info_bp.route('/standards')
def redirect_standards():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/eduStandarts', code=301)

@info_bp.route('/management')
def redirect_management():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/managers', code=301)

@info_bp.route('/teachers')
def redirect_teachers():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/employees', code=301)

@info_bp.route('/facilities')
def redirect_facilities():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/objects', code=301)

@info_bp.route('/scholarships')
def redirect_scholarships():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/grants', code=301)

@info_bp.route('/paid-services')
def redirect_paid_services():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/paid_edu', code=301)

@info_bp.route('/finance')
def redirect_finance():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/budget', code=301)

@info_bp.route('/vacancies')
def redirect_vacancies():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/vacant', code=301)

@info_bp.route('/international')
def redirect_international():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/inter', code=301)

@info_bp.route('/food')
def redirect_food():
    """Редирект со старого URL на новый"""
    return redirect('/sveden/catering', code=301)


@info_bp.route('/section/<section_endpoint>')
def get_section_data(section_endpoint):
    """Получить данные раздела в JSON формате"""
    section = InfoSection.query.filter_by(endpoint=section_endpoint).first()
    
    if not section:
        return jsonify({'success': False, 'error': 'Раздел не найден'})
    
    # Автоматически очищаем несуществующие файлы перед получением данных
    try:
        # Сначала обновляем имена файлов в form_data на основе БД
        _update_form_data_file_names(section)
        # Затем очищаем несуществующие файлы из form_data (это критично!)
        cleaned_count, processed = _clean_section_files(section)
        if processed and cleaned_count > 0:
            logger.info(f"Очищено {cleaned_count} несуществующих файлов из form_data раздела {section_endpoint}")
        # Также очищаем несуществующие файлы из БД (с обработкой ошибок)
        from models.models import InfoFile
        try:
            db_files = InfoFile.query.filter_by(section_endpoint=section_endpoint).all()
        except Exception as e:
            # Если ошибка из-за отсутствующих полей в БД, пропускаем очистку БД
            if 'no such column' in str(e).lower() or 'file_data' in str(e):
                logger.warning(f"Поля file_data/stored_in_db еще не добавлены в БД. Пропускаю очистку БД. Запустите: python migrate_db_add_file_fields.py")
                db_files = []
            else:
                logger.error(f"Ошибка при получении файлов из БД: {e}")
                db_files = []
        
        for db_file in db_files:
            file_path = getattr(db_file, 'file_path', None)
            if file_path and not os.path.exists(file_path):
                # Проверяем альтернативные пути
                found = False
                uploads_info_root = os.path.join(current_app.root_path, 'static', 'uploads', 'info')
                for root, dirs, filenames in os.walk(uploads_info_root):
                    if db_file.filename in filenames:
                        found = True
                        break
                if not found:
                    logger.info(f"Удаляем несуществующий файл из БД: {db_file.filename}")
                    db.session.delete(db_file)
        if db_files and any(not os.path.exists(getattr(f, 'file_path', '')) for f in db_files if getattr(f, 'file_path', None)):
            db.session.commit()
    except Exception as e:
        logger.error(f"Ошибка при автоматической очистке файлов: {e}")
    
    # Парсим данные полей из поля text, если они там есть
    form_data = {}
    try:
        if section.text:
            import json
            text_data = json.loads(section.text)
            if isinstance(text_data, dict) and 'form_data' in text_data:
                form_data = text_data['form_data']
    except Exception as e:
        pass
    
    return jsonify({
        'success': True,
        'section': {
            'id': section.id,
            'endpoint': section.endpoint,
            'title': section.title,
            'text': section.text,
            'content_blocks': section.get_content_blocks(),
            'form_data': form_data
        }
    })


@info_bp.route('/subsections/<parent_endpoint>')
@login_required
def get_subsections(parent_endpoint):
    """Список подразделов (InfoSection), у которых form_data.parent == parent_endpoint."""
    try:
        parent_endpoint = (parent_endpoint or '').strip()
        if not parent_endpoint:
            return jsonify({'success': False, 'error': 'Не указан parent_endpoint'}), 400

        subsections = []
        all_sections = InfoSection.query.all()
        for s in all_sections:
            try:
                if not s.text:
                    continue
                td = json.loads(s.text)
                if not isinstance(td, dict):
                    continue
                form_data = td.get('form_data', {})
                if not isinstance(form_data, dict):
                    continue
                parent_val = form_data.get('parent')
                if not parent_val:
                    continue
                if isinstance(parent_val, str) and parent_val.startswith('/sidebar/'):
                    parent_val = parent_val.replace('/sidebar/', '')
                if parent_val == parent_endpoint:
                    subsections.append({'endpoint': s.endpoint, 'title': s.title})
            except Exception:
                continue

        subsections.sort(key=lambda x: (x.get('title') or '').lower())
        return jsonify({'success': True, 'subsections': subsections})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@info_bp.route('/create_subsection', methods=['POST'])
@login_required
def create_subsection():
    """Создать подраздел для мастера заполнения (по требованию: для раздела food)."""
    try:
        data = request.get_json() or {}
        parent_endpoint = (data.get('parent_endpoint') or '').strip()
        title = (data.get('title') or '').strip()

        if not parent_endpoint:
            return jsonify({'success': False, 'error': 'Не указан parent_endpoint'}), 400
        if parent_endpoint != 'food':
            return jsonify({'success': False, 'error': 'Подразделы разрешены только для раздела "food"'}), 400
        if not title:
            return jsonify({'success': False, 'error': 'Не указан заголовок подраздела'}), 400

        endpoint = f"{parent_endpoint}-sub-{uuid.uuid4().hex[:8]}"
        while InfoSection.query.filter_by(endpoint=endpoint).first():
            endpoint = f"{parent_endpoint}-sub-{uuid.uuid4().hex[:8]}"

        text_data = {
            'text': '',
            'form_data': {
                'parent': parent_endpoint,
                'content': ''
            }
        }

        section = InfoSection(
            endpoint=endpoint,
            title=title,
            url=f'/{endpoint}',
            text=json.dumps(text_data, ensure_ascii=False),
        )
        section.set_content_blocks([])
        db.session.add(section)
        db.session.commit()

        return jsonify({'success': True, 'section': {'endpoint': endpoint, 'title': title}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@info_bp.route('/delete_subsection', methods=['POST'])
@login_required
def delete_subsection():
    """Удалить подраздел (только если parent='food' и нет дочерних подразделов)."""
    try:
        data = request.get_json() or {}
        endpoint = (data.get('endpoint') or '').strip()
        if not endpoint:
            return jsonify({'success': False, 'error': 'Не указан endpoint'}), 400

        section = InfoSection.query.filter_by(endpoint=endpoint).first()
        if not section:
            return jsonify({'success': False, 'error': 'Раздел не найден'}), 404

        # Проверяем parent
        parent_val = None
        try:
            td = json.loads(section.text) if section.text else {}
            if isinstance(td, dict):
                fd = td.get('form_data', {})
                if isinstance(fd, dict):
                    parent_val = fd.get('parent')
        except Exception:
            parent_val = None

        if parent_val != 'food':
            return jsonify({'success': False, 'error': 'Удалять можно только подразделы раздела "food"'}), 400

        # Запрет удаления, если есть дети
        all_sections = InfoSection.query.all()
        for s in all_sections:
            if s.id == section.id:
                continue
            try:
                if not s.text:
                    continue
                td = json.loads(s.text)
                if not isinstance(td, dict):
                    continue
                fd = td.get('form_data', {})
                if not isinstance(fd, dict):
                    continue
                pv = fd.get('parent')
                if isinstance(pv, str) and pv.startswith('/sidebar/'):
                    pv = pv.replace('/sidebar/', '')
                if pv == endpoint:
                    return jsonify({'success': False, 'error': 'Нельзя удалить подраздел с дочерними элементами'}), 400
            except Exception:
                continue

        # Удаляем связанные файлы из БД/диска
        try:
            from models.models import InfoFile
            section_files = InfoFile.query.filter_by(section_endpoint=endpoint).all()
            for info_file in section_files:
                try:
                    fp = getattr(info_file, 'file_path', None)
                    if fp and os.path.exists(fp):
                        os.remove(fp)
                    db.session.delete(info_file)
                except Exception:
                    pass
        except Exception:
            pass

        db.session.delete(section)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def _extract_form_data(section_data):
    """Извлекает данные формы из данных раздела"""
    form_data = {}
    excluded_keys = ['title', 'text', 'content_blocks']
    
    for key, value in section_data.items():
        if key not in excluded_keys:
            form_data[key] = value
    
    return form_data


def _get_existing_text_data(section):
    """Получает существующие текстовые данные раздела"""
    if not section.text:
        return {}
    
    try:
        return json.loads(section.text)
    except (json.JSONDecodeError, TypeError):
        return {}


def _create_text_data(existing_text_data, section_data, form_data):
    """Создает структуру текстовых данных"""
    existing_form_data = existing_text_data.get('form_data', {})
    
    # Начинаем с существующих данных - это гарантирует, что поля, которые есть
    # в existing_form_data, но отсутствуют в form_data, будут сохранены
    merged_form_data = existing_form_data.copy()
    
    # Обновляем/добавляем новые данные из form_data
    # Важно: сохраняем существующие значения, если новое значение пустое
    # Это предотвращает случайную потерю данных при очистке полей формы
    for key, value in form_data.items():
        # Проверяем, является ли значение пустым
        is_empty = (
            value == '' or 
            value is None or 
            (isinstance(value, (list, dict)) and len(value) == 0)
        )
        
        if is_empty:
            # Если новое значение пустое, сохраняем старое значение только если оно truthy
            # Это предотвращает случайную потерю данных, но позволяет очищать falsy значения
            # (пустые строки, 0, False и т.д.)
            if key in merged_form_data:
                existing_value = merged_form_data[key]
                # Сохраняем старое значение только если оно truthy
                # Это позволяет пользователям очищать falsy значения (пустые строки, 0, False)
                if existing_value:
                    # Старое значение truthy - сохраняем его
                    pass  # Уже в merged_form_data
                else:
                    # Старое значение falsy - удаляем его (пользователь явно очистил поле)
                    merged_form_data.pop(key, None)
            # Если поля не было, не добавляем пустое значение
        else:
            # Если значение не пустое, обновляем его
            merged_form_data[key] = value
    
    # ВАЖНО: Поля, которые есть в existing_form_data, но отсутствуют в form_data,
    # уже сохранены в merged_form_data благодаря копированию в начале функции.
    # Это гарантирует, что поля, которые не были отправлены в форме, не будут потеряны.
    
    return {
        'text': existing_text_data.get('text', section_data.get('text', '')),
        'form_data': merged_form_data
    }


def _update_existing_section(section, section_data):
    """Обновляет существующий раздел"""
    section.title = section_data.get('title', section.title)
    
    form_data = _extract_form_data(section_data)
    existing_text_data = _get_existing_text_data(section)
    text_data = _create_text_data(existing_text_data, section_data, form_data)
    
    section.text = json.dumps(text_data, ensure_ascii=False)
    
    if 'content_blocks' in section_data:
        section.set_content_blocks(section_data['content_blocks'])


def _create_new_section(section_id, section_data):
    """Создает новый раздел"""
    form_data = _extract_form_data(section_data)
    text_data = _create_text_data({}, section_data, form_data)
    
    section = InfoSection(
        endpoint=section_id,
        title=section_data.get('title', ''),
        text=json.dumps(text_data, ensure_ascii=False),
        url=f'/{section_id}'
    )
    
    section.set_content_blocks(section_data.get('content_blocks', []))
    return section


@info_bp.route('/wizard_save', methods=['POST'])
@login_required
def wizard_save():
    """Сохранение данных мастера заполнения"""
    try:
        wizard_data = request.form.get('wizard_data')
        save_single = request.form.get('save_single', 'false').lower() == 'true'
        
        if not wizard_data:
            return jsonify({'success': False, 'error': 'Данные мастера не получены'})
        
        data = json.loads(wizard_data)
        
        # Обрабатываем каждый раздел
        for section_id, section_data in data.items():
            section = InfoSection.query.filter_by(endpoint=section_id).first()
            
            if section:
                _update_existing_section(section, section_data)
            else:
                new_section = _create_new_section(section_id, section_data)
                db.session.add(new_section)
        
        db.session.commit()
        
        message = 'Шаг успешно сохранен' if save_single else 'Все данные успешно сохранены'
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


# Функции для работы с файлами теперь в file_manager.py

@info_bp.route('/clean_files', methods=['POST'])
def clean_files():
    """Очистка несуществующих файлов из базы данных"""
    try:
        cleaned_count = file_manager.clean_orphaned_files()
        return jsonify({'success': True, 'message': f'Очищено {cleaned_count} неиспользуемых файлов'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/reset_file_data', methods=['POST'])
def reset_file_data():
    """Сброс всех данных о файлах в базе данных"""
    try:
        sections = InfoSection.query.all()
        updated_count = 0
        
        for section in sections:
            if section.text:
                try:
                    data = json.loads(section.text)
                    if 'form_data' in data:
                        original_data = data.copy()
                        
                        # Очищаем все поля с файлами
                        for field_name, field_value in data['form_data'].items():
                            if isinstance(field_value, str) and field_value.startswith('/download_file/'):
                                data['form_data'][field_name] = ''
                                updated_count += 1
                        
                        # Сохраняем изменения если что-то изменилось
                        if data != original_data:
                            section.text = json.dumps(data, ensure_ascii=False)
                            
                except Exception as e:
                    logger.error(f"Ошибка в разделе {section.endpoint}: {e}")
                    continue
        
        if updated_count > 0:
            db.session.commit()
            return jsonify({'success': True, 'message': f'Очищено {updated_count} полей с файлами'})
        else:
            return jsonify({'success': True, 'message': 'Данные о файлах уже пустые'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    """Загрузка файла на сервер с сохранением в базе данных"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не найден'})
        
        # Проверяем общий размер запроса относительно MAX_CONTENT_LENGTH
        max_len = current_app.config.get('MAX_CONTENT_LENGTH')
        if max_len and request.content_length and request.content_length > max_len:
            max_mb = round(max_len / (1024 * 1024))
            return jsonify({'success': False, 'error': f'Файл слишком большой. Максимум {max_mb} МБ'}), 413

        file = request.files['file']
        section = request.form.get('section', 'general')
        if not section or section == 'undefined':
            section = 'main'
        field_name = request.form.get('field_name')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        # Серверная валидация типа файла
        allowed_ext = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif',
            '.sig',
            # Архивы
            '.zip', '.rar', '.7z', '.tar', '.gz', '.tgz',
        }
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in allowed_ext:
            return jsonify({'success': False, 'error': f'Недопустимый формат файла: {ext}. Разрешено: {", ".join(sorted(allowed_ext))}'})
        
        # Получаем раздел из базы данных; если нет — создаём пустой
        section_obj = InfoSection.query.filter_by(endpoint=section).first()
        if not section_obj:
            section_obj = InfoSection(
                endpoint=section,
                title=section,
                url=f'/{section}',
                text=json.dumps({'form_data': {}}, ensure_ascii=False)
            )
            db.session.add(section_obj)
            db.session.commit()
        
        # НЕ удаляем старые файлы автоматически - пользователь должен удалять их вручную
        # Это предотвращает случайное удаление файлов при повторной загрузке
        
        # Используем новую систему загрузки файлов с сохранением в БД
        # Для разделов Сведения используем новую структуру папок info/год/раздел/
        if section in ['main', 'about', 'documents', 'education', 'standards', 'structure', 'management', 'teachers', 'material', 'facilities', 'scholarships', 'paid-services', 'paid', 'financial', 'finance', 'vacancies', 'nutrition', 'food', 'international']:
            file_info = file_manager.save_info_file(file, section, field_name)
        else:
            file_info = file_manager.save_file(file, section, field_name)
        
        if file_info:
            # Создаем или обновляем запись в БД для сохранения original_filename
            from models.models import InfoFile
            db_file = None
            try:
                # Ищем существующую запись
                query = InfoFile.query.filter_by(
                    filename=file_info['filename'],
                    section_endpoint=section
                )
                if field_name:
                    query = query.filter_by(field_name=field_name)
                db_file = query.first()
                
                # Если не нашли с учетом field_name, ищем без него (для совместимости)
                if not db_file:
                    db_file = InfoFile.query.filter_by(
                        filename=file_info['filename'],
                        section_endpoint=section
                    ).first()
                
                # Если записи нет, создаем новую
                if not db_file:
                    # Читаем данные файла для сохранения в БД
                    file_data = None
                    try:
                        with open(file_info['file_path'], 'rb') as f:
                            file_data = f.read()
                    except Exception as e:
                        logger.warning(f"Не удалось прочитать файл для сохранения в БД: {e}")
                    
                    db_file = InfoFile(
                        filename=file_info['filename'],
                        original_filename=file_info['original_name'],
                        file_path=file_info['file_path'],
                        section_endpoint=section,
                        field_name=field_name,
                        file_size=file_info['size'],
                        mime_type=file_info.get('mime_type'),
                        is_image=file_info.get('is_image', False),
                        display_name=file_info['original_name'],
                        file_data=file_data,
                        stored_in_db=file_data is not None
                    )
                    db.session.add(db_file)
                    db.session.commit()
                    logger.info(f"Создана запись InfoFile для файла {file_info['filename']}")
                else:
                    # Обновляем original_filename, если он изменился или отсутствует
                    if not db_file.original_filename or db_file.original_filename != file_info['original_name']:
                        db_file.original_filename = file_info['original_name']
                        if not db_file.display_name:
                            db_file.display_name = file_info['original_name']
                        db.session.commit()
                        logger.info(f"Обновлен original_filename для файла {file_info['filename']}")
            except Exception as e:
                # Обрабатываем ошибки при сохранении в БД
                error_str = str(e).lower()
                db_file = None
                
                # Всегда пытаемся выполнить rollback, если сессия активна
                try:
                    if db.session.is_active:
                        db.session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Ошибка при rollback транзакции: {rollback_error}")
                
                # Проверяем тип ошибки
                if 'no such column' in error_str or 'file_data' in error_str:
                    # Ошибка схемы БД - поля еще не добавлены
                    logger.warning(
                        "Поля file_data/stored_in_db еще не добавлены в БД. "
                        "Пропускаю сохранение файла в InfoFile. Имя будет взято из запроса."
                    )
                else:
                    # Другие ошибки БД - логируем как ошибку с полным traceback
                    logger.error(f"Ошибка при сохранении файла в InfoFile: {e}", exc_info=True)
            
            # Используем display_name из БД, если есть, иначе original_name
            # Важно: original_name содержит оригинальное имя с правильным расширением
            display_name = db_file.display_name if db_file and db_file.display_name else file_info['original_name']
            
            # Убеждаемся, что display_name содержит правильное расширение
            if display_name:
                _, display_ext = os.path.splitext(display_name)
                _, original_ext = os.path.splitext(file_info['original_name'])
                # Если расширения не совпадают, используем расширение из original_name
                if display_ext.lower() != original_ext.lower() and original_ext:
                    name_without_ext, _ = os.path.splitext(display_name)
                    display_name = name_without_ext + original_ext
            
            # Обновляем данные раздела с новым файлом
            try:
                if section_obj.text:
                    data = json.loads(section_obj.text)
                else:
                    data = {'form_data': {}}
                
                if field_name:
                    # Для конкретного поля - добавляем файл к существующим (если есть)
                    # Сохраняем URL с display_name для правильного отображения в шаблоне
                    file_url_with_name = f"{file_info['url']}|{display_name}"
                    
                    # Проверяем, нет ли уже этого файла в текущем поле
                    # Это предотвращает дублирование при повторной загрузке
                    filename_to_check = file_info['filename']
                    file_already_in_field = False
                    if field_name in data['form_data'] and data['form_data'][field_name]:
                        existing_value = data['form_data'][field_name]
                        if isinstance(existing_value, str):
                            existing_files = [f.strip() for f in existing_value.split(',') if f.strip()]
                            for existing_file_url in existing_files:
                                existing_file_url_clean = existing_file_url.split('|')[0].strip() if '|' in existing_file_url else existing_file_url.strip()
                                existing_filename = existing_file_url_clean.split('/')[-1].strip()
                                # Сравниваем имена файлов (без суффиксов _2, _3 и т.д.)
                                base_name_1, ext_1 = os.path.splitext(filename_to_check)
                                base_name_2, ext_2 = os.path.splitext(existing_filename)
                                # Убираем суффиксы _2, _3 и т.д. для сравнения
                                base_name_1_clean = base_name_1.rsplit('_', 1)[0] if '_' in base_name_1 and base_name_1.rsplit('_', 1)[-1].isdigit() else base_name_1
                                base_name_2_clean = base_name_2.rsplit('_', 1)[0] if '_' in base_name_2 and base_name_2.rsplit('_', 1)[-1].isdigit() else base_name_2
                                if base_name_1_clean == base_name_2_clean and ext_1.lower() == ext_2.lower():
                                    file_already_in_field = True
                                    logger.info(f"Файл {filename_to_check} уже есть в поле {field_name}, не добавляем дубликат")
                                    break
                    
                    if not file_already_in_field:
                        # Проверяем, есть ли уже файлы в этом поле
                        if field_name in data['form_data'] and data['form_data'][field_name]:
                            existing_value = data['form_data'][field_name]
                            # Если это строка с файлами через запятую, добавляем новый файл
                            if isinstance(existing_value, str) and (existing_value.startswith('/download_file/') or existing_value.startswith('/info/download_file/')):
                                # Проверяем, нет ли уже этого файла в списке
                                existing_files = [f.strip() for f in existing_value.split(',') if f.strip()]
                                # Проверяем по URL (без display_name)
                                file_url_clean = file_info['url']
                                if not any(f.startswith(file_url_clean) for f in existing_files):
                                    existing_files.append(file_url_with_name)
                                    data['form_data'][field_name] = ', '.join(existing_files)
                                # Если файл уже есть, не добавляем
                            else:
                                # Если поле не содержит файлов, заменяем
                                data['form_data'][field_name] = file_url_with_name
                        else:
                            # Поле пустое, просто устанавливаем значение
                            data['form_data'][field_name] = file_url_with_name
                    else:
                        # Файл уже есть в текущем поле - просто не добавляем дубликат
                        logger.info(f"Файл {file_info['filename']} уже есть в поле {field_name}, пропускаем добавление")
                        # Важно: возвращаем url, чтобы клиент мог правильно обработать ответ
                        return jsonify({
                            'success': True, 
                            'message': 'Файл уже загружен в это поле', 
                            'filename': file_info['filename'],
                            'original_name': file_info['original_name'],
                            'display_name': display_name,
                            'url': file_info['url'],
                            'is_image': file_info.get('is_image', False),
                            'size': file_info.get('size'),
                            'mime_type': file_info.get('mime_type'),
                            'id': db_file.id if db_file else None
                        })
                else:
                    # Для раздела main - добавляем в список файлов
                    if 'files' not in data['form_data']:
                        data['form_data']['files'] = []
                    
                    data['form_data']['files'].append({
                        'filename': file_info['filename'],
                        'original_name': file_info['original_name'],
                        'url': file_info['url'],
                        'size': file_info['size'],
                        'uploaded_at': file_info['created_at']
                    })
                
                section_obj.text = json.dumps(data, ensure_ascii=False)
                db.session.commit()
            except Exception as e:
                logger.error(f"Ошибка при обновлении данных раздела: {e}")
            
            return jsonify({
                'success': True,
                'filename': file_info['filename'],
                'original_name': file_info['original_name'],
                'display_name': display_name,
                'url': file_info['url'],
                'is_image': file_info['is_image'],
                'size': file_info['size'],
                'mime_type': file_info['mime_type'],
                'id': db_file.id if db_file else None
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка при сохранении файла'})
            
    except ValueError as e:
        try:
            from utils.error_utils import handle_api_error
            return handle_api_error(e, 'При загрузке файла')
        except ImportError:
            return jsonify({'success': False, 'error': str(e), 'instructions': ['Проверьте формат файла', 'Убедитесь, что файл не поврежден']}), 400
    except Exception as e:
        try:
            from utils.error_utils import handle_api_error
            return handle_api_error(e, 'При загрузке файла')
        except ImportError:
            return jsonify({'success': False, 'error': f'Ошибка при загрузке файла: {str(e)}', 'instructions': ['Попробуйте загрузить файл снова', 'Проверьте размер файла', 'Если проблема сохраняется, сообщите администратору']}), 500

@info_bp.route('/download_file/<section>/<filename>')
@info_bp.route('/info/download_file/<section>/<filename>')
def download_file(section, filename):
    """Скачивание файла пользователем. Поддерживает файлы из БД и файловой системы"""
    try:
        from io import BytesIO
        import mimetypes
        import urllib.parse
        
        file_path = None
        download_filename = filename
        file_data = None
        mimetype = None
        
        # Пытаемся получить файл из БД
        from models.models import InfoFile
        info_file = None
        try:
            info_file = InfoFile.query.filter_by(
                filename=filename,
                section_endpoint=section
            ).first()
        except Exception as e:
            # Если ошибка из-за отсутствующих полей в БД, пропускаем проверку БД
            if 'no such column' in str(e).lower() or 'file_data' in str(e):
                logger.warning(f"Поля file_data/stored_in_db еще не добавлены в БД. Пропускаю проверку БД. Запустите: python migrate_db_add_file_fields.py")
            else:
                logger.error(f"Ошибка при поиске файла в БД: {e}")
        
        # Если файл найден в БД
        if info_file:
            # Используем оригинальное имя из БД
            download_filename = info_file.original_filename or info_file.display_name or filename
            
            # Проверяем, хранится ли файл в БД
            # Проверяем наличие обоих атрибутов перед доступом
            # ВАЖНО: Проверяем file_data is not None, а не truthiness,
            # так как пустые файлы (b'') являются falsy, но валидны
            if (hasattr(info_file, 'stored_in_db') and hasattr(info_file, 'file_data') and 
                info_file.stored_in_db and info_file.file_data is not None):
                # Файл хранится в БД - используем данные из БД
                # Пустые файлы (0 байт) также валидны и должны быть отданы
                file_data = info_file.file_data
                mimetype = info_file.mime_type
            elif (hasattr(info_file, 'file_path') and info_file.file_path and 
                  os.path.exists(info_file.file_path)):
                # Файл в файловой системе, используем путь из БД
                file_path = info_file.file_path
                mimetype = info_file.mime_type
        
        uploads_root = os.path.join(current_app.root_path, 'static', 'uploads')
        uploads_info_root = os.path.join(uploads_root, 'info')

        # Если файл не найден в БД или не хранится в БД, ищем в файловой системе
        if not file_data and not file_path:
            # Для разделов Сведения ищем в структуре info/год/раздел/
            if section in ['main', 'about', 'documents', 'education', 'standards', 'structure', 'management', 'teachers', 'material', 'facilities', 'scholarships', 'paid-services', 'paid', 'financial', 'finance', 'vacancies', 'nutrition', 'food', 'international']:
                # Ищем в новой структуре папок
                for root, dirs, files in os.walk(uploads_info_root):
                    if filename in files:
                        file_path = os.path.join(root, filename)
                        break
            
            # Если не найден в новой структуре, пробуем структуру для новостей/объявлений
            if not file_path or not os.path.exists(file_path):
                for root, dirs, files in os.walk(uploads_root):
                    if filename in files:
                        file_path = os.path.join(root, filename)
                        if os.path.exists(file_path):
                            break
            
            # Если не найден, пробуем старую структуру (для совместимости)
            if not file_path or not os.path.exists(file_path):
                file_path = os.path.join(uploads_root, section, filename)
                
                if not os.path.exists(file_path):
                    file_path = os.path.join(uploads_root, 'pages', section, filename)
            
            # Если файл не найден в файловой системе, пытаемся получить оригинальное имя из form_data
            if not file_path or not os.path.exists(file_path):
                try:
                    section_obj = InfoSection.query.filter_by(endpoint=section).first()
                    if section_obj and section_obj.text:
                        data = json.loads(section_obj.text)
                        if 'form_data' in data:
                            # Ищем файл в form_data по имени файла
                            for field_value in data['form_data'].values():
                                if isinstance(field_value, str) and filename in field_value:
                                    # Извлекаем display_name из URL (формат: url|display_name)
                                    files = [f.strip() for f in field_value.split(',') if f.strip()]
                                    for file_url in files:
                                        if filename in file_url:
                                            if '|' in file_url:
                                                # Есть display_name
                                                display_name = file_url.split('|')[-1].strip()
                                                if display_name:
                                                    download_filename = display_name
                                            break
                except Exception as e:
                    logger.debug(f"Не удалось получить оригинальное имя из form_data: {e}")
        
        # Если файл не найден ни в БД, ни в файловой системе
        if not file_data and (not file_path or not os.path.exists(file_path)):
            flash('Файл не найден', 'error')
            return redirect(url_for('main.index'))
        
        # Убеждаемся, что расширение имени скачивания совпадает с реальным файлом
        if not download_filename:
            download_filename = filename
        
        # Определяем расширение файла
        if file_path:
            _, file_ext = os.path.splitext(file_path)
        elif info_file and info_file.original_filename:
            _, file_ext = os.path.splitext(info_file.original_filename)
        else:
            _, file_ext = os.path.splitext(filename)
        
        name_no_ext, download_ext = os.path.splitext(download_filename)
        if file_ext and download_ext and file_ext.lower() != download_ext.lower():
            download_filename = name_no_ext + file_ext
        elif file_ext and not download_ext:
            download_filename = download_filename + file_ext
        
        # Определяем MIME-тип
        if not mimetype:
            if file_path:
                mimetype, _ = mimetypes.guess_type(file_path)
            if not mimetype:
                mimetype, _ = mimetypes.guess_type(download_filename)
            if not mimetype:
                mimetype = 'application/octet-stream'
        
        # Кодируем имя файла для правильного отображения в браузере
        encoded_filename = urllib.parse.quote(download_filename.encode('utf-8'))
        
        # Для изображений отдаём inline, чтобы они корректно отображались в <img>.
        # Для остальных типов оставляем attachment (скачивание).
        is_inline = bool(mimetype and str(mimetype).startswith('image/'))

        # Создаем response
        if file_data:
            file_stream = BytesIO(file_data)
            if is_inline:
                response = send_file(file_stream, mimetype=mimetype, as_attachment=False)
            else:
                response = send_file(file_stream, mimetype=mimetype, as_attachment=True, download_name=download_filename)
        else:
            if is_inline:
                response = send_file(file_path, mimetype=mimetype, as_attachment=False)
            else:
                response = send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=download_filename)
        
        # Для скачивания выставляем Content-Disposition с корректным UTF-8 именем.
        # Для inline-изображений не трогаем Content-Disposition, чтобы браузер мог отрисовать <img>.
        if not is_inline:
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        else:
            # На всякий случай убираем Content-Disposition полностью для картинок:
            # некоторые браузеры/прокси могут некорректно обрабатывать inline+filename.
            try:
                response.headers.pop('Content-Disposition', None)
            except Exception:
                pass
        
        # Добавляем заголовки для правильного определения типа файла
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла {filename}: {e}")
        flash('Ошибка при скачивании файла', 'error')
        return redirect(url_for('main.index'))

@info_bp.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    """Удаление файла с сервера и из базы данных"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        section = data.get('section')
        field_name = data.get('field_name')
        
        logger.debug(f"delete_file: filename={filename}, section={section}, field_name={field_name}")
        
        if not all([filename, section]):
            logger.warning(f"delete_file: Missing data - filename={filename}, section={section}")
            return jsonify({'success': False, 'error': 'Недостаточно данных для удаления'})
        
        # Удаляем файл из файловой системы и из базы данных
        success = file_manager.delete_file(filename, section, field_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Файл удален'})
        else:
            # Если файл не найден, это не всегда ошибка - возможно, он уже был удален
            return jsonify({'success': True, 'message': 'Файл не найден (возможно, уже удален)'})
        
    except Exception as e:
        logger.error(f"delete_file: Exception: {e}")
        return jsonify({'success': False, 'error': str(e)})


@info_bp.route('/section_data')
def get_all_sections_data():
    """Получить данные всех разделов для проверки заголовков"""
    try:
        sections = InfoSection.query.all()
        sections_data = []
        
        for section in sections:
            sections_data.append({
                'id': section.id,
                'endpoint': section.endpoint,
                'title': section.title,
                'url': section.url
            })
        
        return jsonify({
            'success': True,
            'sections': sections_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/get_section_files/<section_endpoint>')
@login_required
def get_section_files(section_endpoint):
    """Получить список файлов раздела (только существующие файлы).
    
    Очистка несуществующих файлов из form_data выполняется автоматически перед получением списка.
    Записи из БД не удаляются (read-only), несуществующие файлы просто не включаются в результат.
    """
    try:
        field_name = request.args.get('field_name')
        
        # Автоматически очищаем несуществующие файлы из form_data перед получением списка
        try:
            section_obj = InfoSection.query.filter_by(endpoint=section_endpoint).first()
            if section_obj:
                # Сначала обновляем имена файлов в form_data на основе БД
                _update_form_data_file_names(section_obj)
                # Затем очищаем несуществующие файлы из form_data
                cleaned_count, processed = _clean_section_files(section_obj)
                if processed and cleaned_count > 0:
                    logger.info(f"Очищено {cleaned_count} несуществующих файлов из form_data раздела {section_endpoint}")
        except Exception as e:
            logger.error(f"Ошибка при автоматической очистке файлов из form_data: {e}")
        
        # Для разделов Сведения используем новую функцию с проверкой БД
        # Проверяем, есть ли файлы в БД для этого раздела (с обработкой ошибок)
        from models.models import InfoFile
        has_db_files = False
        try:
            has_db_files = InfoFile.query.filter_by(section_endpoint=section_endpoint).first() is not None
        except Exception as e:
            # Если ошибка из-за отсутствующих полей в БД, считаем что файлов в БД нет
            if 'no such column' in str(e).lower() or 'file_data' in str(e):
                logger.warning(f"Поля file_data/stored_in_db еще не добавлены в БД. Пропускаю проверку БД. Запустите: python migrate_db_add_file_fields.py")
            else:
                logger.error(f"Ошибка при проверке файлов в БД: {e}")
        
        # Получаем объект раздела для доступа к form_data
        section_obj = InfoSection.query.filter_by(endpoint=section_endpoint).first()
        
        if has_db_files or section_endpoint in ['main', 'about', 'documents', 'education', 'standards', 'structure', 'management', 'teachers', 'material', 'facilities', 'scholarships', 'paid-services', 'paid', 'financial', 'finance', 'vacancies', 'nutrition', 'food', 'international']:
            # Используем БД для получения файлов
            # get_section_files_from_db проверяет существование файлов и возвращает только существующие
            # ПРИМЕЧАНИЕ: Метод не удаляет записи из БД (read-only), несуществующие файлы просто не включаются в результат
            files = file_manager.get_section_files_from_db(section_endpoint, field_name)
            
            # ДЛЯ ДОКУМЕНТОВ: также загружаем файлы из form_data для указанного поля
            # Это нужно, потому что документы (pdf, docx и т.п.) не сохраняются в БД
            # ВАЖНО: загружаем только для указанного поля, чтобы избежать дублирования
            if field_name and section_obj:
                try:
                    if section_obj.text:
                        import json
                        data = json.loads(section_obj.text)
                        if 'form_data' in data and field_name in data['form_data']:
                            field_value = data['form_data'][field_name]
                            if isinstance(field_value, str) and field_value.strip():
                                # Парсим файлы из поля
                                file_urls = [url.strip() for url in field_value.split(',') if url.strip()]
                                for file_url in file_urls:
                                    # Извлекаем имя файла и display_name
                                    if '|' in file_url:
                                        url_part, display_name = file_url.split('|', 1)
                                        display_name = display_name.strip()
                                    else:
                                        url_part = file_url
                                        display_name = None
                                    
                                    # Извлекаем имя файла из URL
                                    if '/info/download_file/' in url_part or '/download_file/' in url_part:
                                        filename = url_part.split('/')[-1].strip()
                                        
                                        # Проверяем, нет ли уже этого файла в списке (из БД)
                                        file_exists_in_list = any(f.get('filename') == filename for f in files)
                                        
                                        # Проверяем существование файла в файловой системе
                                        if not file_exists_in_list and _file_exists(url_part, section_endpoint):
                                            # Добавляем файл из form_data
                                            files.append({
                                                'filename': filename,
                                                'original_filename': display_name or filename,
                                                'display_name': display_name or filename,
                                                'url': url_part,
                                                'is_image': False,
                                                'field_name': field_name
                                            })
                                            logger.debug(f"Добавлен файл из form_data: {filename} для поля {field_name}")
                except Exception as e:
                    logger.error(f"Ошибка при загрузке файлов из form_data: {e}")
        else:
            # Используем файловую систему
            files = file_manager.get_section_files(section_endpoint, field_name)
        
        # Дополнительная проверка: фильтруем файлы, которых нет в файловой системе
        valid_files = []
        for file_info in files:
            file_path = file_info.get('file_path') or file_info.get('url', '')
            if isinstance(file_path, str) and file_path.startswith('/'):
                # Это URL, нужно проверить существование файла
                filename = file_info.get('filename') or file_path.split('/')[-1]
                file_url = file_info.get('url', file_path)
                if _file_exists(file_url, section_endpoint):
                    valid_files.append(file_info)
                else:
                    logger.debug(f"Файл не существует, исключаем из списка: {filename}")
            elif isinstance(file_path, str) and os.path.exists(file_path):
                # Это путь к файлу, проверяем существование
                valid_files.append(file_info)
            elif 'url' in file_info:
                # Проверяем по URL
                if _file_exists(file_info['url'], section_endpoint):
                    valid_files.append(file_info)
                else:
                    logger.debug(f"Файл не существует по URL, исключаем: {file_info.get('filename')}")
            else:
                # Если нет пути и URL, пропускаем
                logger.debug(f"Файл без пути и URL, исключаем: {file_info.get('filename')}")
        
        # Удаляем дубликаты по базовому имени файла (без суффиксов _2, _3)
        unique_files = []
        seen = set()
        def normalize_filename(fn: str):
            if not fn:
                return ''
            name, ext = os.path.splitext(fn)
            if '_' in name and name.rsplit('_', 1)[-1].isdigit():
                name = name.rsplit('_', 1)[0]
            return f"{name}{ext.lower()}"
        for f in valid_files:
            fn = f.get('filename') or (f.get('url', '').split('/')[-1] if isinstance(f.get('url', ''), str) else None)
            key = normalize_filename(fn)
            if key in seen:
                continue
            seen.add(key)
            unique_files.append(f)

        return jsonify({
            'success': True,
            'files': unique_files
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении файлов раздела {section_endpoint}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/update_file_display_name', methods=['POST'])
@login_required
def update_file_display_name():
    """Обновить отображаемое имя файла"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        display_name = data.get('display_name')
        
        if not file_id or not display_name:
            return jsonify({'success': False, 'error': 'Недостаточно данных'})
        
        success = file_manager.update_file_display_name(file_id, display_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Имя файла обновлено'})
        else:
            return jsonify({'success': False, 'error': 'Файл не найден'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/clean_missing_files', methods=['POST'])
@login_required
def clean_missing_files():
    """Очистить несуществующие файлы из базы данных"""
    try:
        from models.models import InfoFile
        
        # Получаем все файлы из БД
        all_files = InfoFile.query.all()
        cleaned_count = 0
        
        for info_file in all_files:
            # Проверяем наличие атрибута file_path перед доступом
            if (hasattr(info_file, 'file_path') and info_file.file_path and 
                not os.path.exists(info_file.file_path)):
                db.session.delete(info_file)
                cleaned_count += 1
                logger.info(f"Удалена запись о несуществующем файле: {info_file.filename}")
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Очищено {cleaned_count} несуществующих файлов'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

def _is_file_field(field_value):
    """Проверяет, является ли поле файловым"""
    return isinstance(field_value, str) and (field_value.startswith('/download_file/') or field_value.startswith('/static/uploads/') or field_value.startswith('/info/download_file/'))


def _file_exists(file_url, section_endpoint=None):
    """Проверяет существование файла по URL"""
    if not _is_file_field(file_url):
        return True

    uploads_root = os.path.join(current_app.root_path, 'static', 'uploads')
    uploads_info_root = os.path.join(uploads_root, 'info')
    
    # Извлекаем имя файла из URL (убираем возможные параметры после |)
    filename = file_url.split('/')[-1].split('|')[0].strip()
    
    if not filename:
        return False
    
    # Сначала проверяем в БД (InfoFile) - это самый надежный способ
    try:
        from models.models import InfoFile
        if section_endpoint:
            info_file = InfoFile.query.filter_by(
                filename=filename,
                section_endpoint=section_endpoint
            ).first()
        else:
            info_file = InfoFile.query.filter_by(filename=filename).first()
            
        if info_file:
            # Проверяем существование по пути из БД (с проверкой наличия атрибута)
            if (hasattr(info_file, 'file_path') and info_file.file_path and 
                os.path.exists(info_file.file_path)):
                return True
            # Если путь неверный, ищем файл в файловой системе
            found = False
            for root, dirs, files in os.walk(uploads_info_root):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    if os.path.exists(file_path):
                        # Обновляем путь в БД
                        info_file.file_path = file_path
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                        found = True
                        return True
            # Если файл не найден в файловой системе, но есть в БД - файл удален
            if not found:
                logger.debug(f"Файл в БД, но не найден на диске: {filename}")
                return False
    except Exception as e:
        logger.debug(f"Ошибка при проверке файла в БД: {e}")
    
    # Если файла нет в БД, проверяем файловую систему напрямую
    # Проверяем новую структуру папок info/год/раздел/
    if section_endpoint:
        # Ищем в структуре info/год/раздел/
        for root, dirs, files in os.walk(uploads_info_root):
            if filename in files:
                file_path = os.path.join(root, filename)
                if os.path.exists(file_path):
                    return True
    else:
        # Если раздел не указан, ищем везде
        for root, dirs, files in os.walk(uploads_info_root):
            if filename in files:
                file_path = os.path.join(root, filename)
                if os.path.exists(file_path):
                    return True
    
    # Проверяем старую структуру по разделу
    if section_endpoint:
        old_path = os.path.join(uploads_root, section_endpoint, filename)
        if os.path.exists(old_path):
            return True
        
        # Проверяем в pages/
        pages_path = os.path.join(uploads_root, 'pages', section_endpoint, filename)
        if os.path.exists(pages_path):
            return True
    
    # Проверяем старую структуру по URL (если URL содержит путь)
    if file_url.startswith('/'):
        file_path = file_url[1:]  # Убираем первый слеш
        if os.path.exists(file_path):
            return True
    
    # Проверяем все возможные пути в uploads (последняя попытка)
    if os.path.exists(uploads_root):
        for root, dirs, files in os.walk(uploads_root):
            if filename in files:
                file_path = os.path.join(root, filename)
                if os.path.exists(file_path):
                    return True
    
    logger.debug(f"Файл не найден: {filename} (URL: {file_url}, раздел: {section_endpoint})")
    return False


def _update_form_data_file_names(section):
    """Обновляет имена файлов в form_data на основе данных из БД"""
    if not section.text:
        return False
    
    try:
        from models.models import InfoFile
        data = json.loads(section.text)
        if 'form_data' not in data:
            return False
        
        form_data = data['form_data']
        updated = False
        
        # Обновляем имена файлов во всех полях
        for field_key, field_value in form_data.items():
            if isinstance(field_value, str) and field_value.strip():
                # Проверяем, содержит ли поле файловые ссылки
                if (field_value.startswith('/download_file/') or 
                    field_value.startswith('/info/download_file/') or
                    field_value.startswith('/static/uploads/')):
                    
                    # Обрабатываем строку с файлами (может быть один или несколько)
                    files = [f.strip() for f in field_value.split(',') if f.strip()]
                    new_files = []
                    
                    for file_url in files:
                        if (file_url.startswith('/download_file/') or 
                            file_url.startswith('/static/uploads/') or 
                            file_url.startswith('/info/download_file/')):
                            
                            # Извлекаем имя файла из URL
                            file_url_clean = file_url.split('|')[0] if '|' in file_url else file_url
                            filename = file_url_clean.split('/')[-1]
                            
                            # Ищем файл в БД (с обработкой ошибок, если колонок нет)
                            try:
                                info_file = InfoFile.query.filter_by(
                                    filename=filename,
                                    section_endpoint=section.endpoint
                                ).first()
                                
                                if info_file:
                                    # Используем display_name или original_filename
                                    display_name = info_file.display_name if info_file.display_name else info_file.original_filename
                                    new_file_url = f"{file_url_clean}|{display_name}"
                                    if new_file_url != file_url:
                                        updated = True
                                    new_files.append(new_file_url)
                                else:
                                    # Если файла нет в БД, оставляем как есть
                                    new_files.append(file_url)
                            except Exception as db_error:
                                # Если ошибка из-за отсутствующих колонок, просто пропускаем обновление
                                if 'no such column' in str(db_error).lower() or 'file_data' in str(db_error):
                                    new_files.append(file_url)
                                else:
                                    raise
                        else:
                            new_files.append(file_url)
                    
                    # Обновляем поле
                    if updated:
                        form_data[field_key] = ', '.join(new_files) if new_files else ''
        
        if updated:
            data['form_data'] = form_data
            section.text = json.dumps(data, ensure_ascii=False)
            db.session.commit()
            logger.info(f"Обновлены имена файлов в form_data для раздела {section.endpoint}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении имен файлов в form_data: {e}")
        return False


def _clean_section_files(section):
    """Очищает несуществующие файлы из раздела"""
    if not section.text:
        return 0, False
    
    try:
        data = json.loads(section.text)
        if 'form_data' not in data:
            return 0, False
        
        form_data = data['form_data']
        cleaned_data = {}
        section_cleaned = 0  # сколько удалено несуществующих
        section_updated = False  # были ли изменения (в т.ч. дедуп)
        
        # Специальная обработка для раздела main с новой структурой
        if section.endpoint == 'main' and 'files' in form_data:
            if isinstance(form_data['files'], list):
                existing_files = []
                for file_info in form_data['files']:
                    if isinstance(file_info, dict) and 'filename' in file_info:
                        filename = file_info['filename']
                        
                        # Проверяем существование файла используя улучшенную функцию
                        file_url = f"/info/download_file/{section.endpoint}/{filename}"
                        if _file_exists(file_url, section.endpoint):
                            existing_files.append(file_info)
                        else:
                            section_cleaned += 1
                            logger.debug(f"Удаляем несуществующий файл из files списка: {filename} (раздел: {section.endpoint})")
                    else:
                        existing_files.append(file_info)
                
                cleaned_data['files'] = existing_files
                # Копируем остальные поля
                for field_name, field_value in form_data.items():
                    if field_name != 'files':
                        cleaned_data[field_name] = field_value
            else:
                cleaned_data = form_data
        else:
            # Обычная обработка для других разделов
            for field_name, field_value in form_data.items():
                if isinstance(field_value, str) and field_value.strip():
                    # Проверяем, содержит ли поле файловые ссылки
                    if (field_value.startswith('/download_file/') or 
                        field_value.startswith('/info/download_file/') or
                        field_value.startswith('/static/uploads/')):
                        
                        # Обрабатываем строку с файлами (может быть один или несколько)
                        files = [f.strip() for f in field_value.split(',') if f.strip()]

                        # Убираем дубликаты по базовому имени/расширению
                        def normalize_filename(url: str):
                            url_clean = url.split('|')[0].strip() if '|' in url else url.strip()
                            filename = url_clean.split('/')[-1].strip()
                            base, ext = os.path.splitext(filename)
                            if '_' in base and base.rsplit('_', 1)[-1].isdigit():
                                base = base.rsplit('_', 1)[0]
                            return f"{base}{ext.lower()}"

                        seen = set()
                        deduped_files = []
                        for file_url in files:
                            key = normalize_filename(file_url)
                            if key in seen:
                                # дедупликация
                                section_updated = True
                                continue
                            seen.add(key)
                            deduped_files.append(file_url)

                        existing_files = []
                        for file_url in deduped_files:
                            if (file_url.startswith('/download_file/') or 
                                file_url.startswith('/static/uploads/') or 
                                file_url.startswith('/info/download_file/')):
                                
                                # Проверяем существование файла с указанием раздела
                                if _file_exists(file_url, section.endpoint):
                                    existing_files.append(file_url)
                                else:
                                    section_cleaned += 1
                                    logger.debug(f"Удаляем несуществующий файл из form_data: {file_url} (раздел: {section.endpoint})")
                            else:
                                # Если это не файловая ссылка, оставляем как есть
                                existing_files.append(file_url)
                        
                        # Обновляем поле
                        # фиксируем изменения, если кол-во изменилось
                        if len(existing_files) != len(files):
                            section_updated = True

                        if existing_files:
                            cleaned_data[field_name] = ', '.join(existing_files)
                        else:
                            cleaned_data[field_name] = ''
                    else:
                        # Не файловое поле, оставляем как есть
                        cleaned_data[field_name] = field_value
                else:
                    # Не файловое поле, оставляем как есть
                    cleaned_data[field_name] = field_value
        
        # Также очищаем ссылки на несуществующие файлы в content_blocks (фото/документы/фото персон)
        try:
            blocks = section.get_content_blocks()
        except Exception:
            blocks = []

        blocks_updated = False

        def clean_file_list(urls):
            """Возвращает список только существующих файловых URL (и не трогает не-URL значения)."""
            nonlocal section_cleaned, blocks_updated
            if not isinstance(urls, list):
                return urls
            cleaned = []
            for u in urls:
                if isinstance(u, str) and _is_file_field(u):
                    if _file_exists(u, None):
                        cleaned.append(u)
                    else:
                        section_cleaned += 1
                        blocks_updated = True
                else:
                    cleaned.append(u)
            if len(cleaned) != len(urls):
                blocks_updated = True
            return cleaned

        def clean_documents_list(docs):
            """Чистит документы в формате [{url,name}, ...] или [url,...]."""
            nonlocal section_cleaned, blocks_updated
            if not isinstance(docs, list):
                return docs
            cleaned = []
            for d in docs:
                if isinstance(d, dict):
                    url = d.get('url')
                    if isinstance(url, str) and _is_file_field(url):
                        if _file_exists(url, None):
                            cleaned.append(d)
                        else:
                            section_cleaned += 1
                            blocks_updated = True
                    else:
                        cleaned.append(d)
                elif isinstance(d, str) and _is_file_field(d):
                    if _file_exists(d, None):
                        cleaned.append(d)
                    else:
                        section_cleaned += 1
                        blocks_updated = True
                else:
                    cleaned.append(d)
            if len(cleaned) != len(docs):
                blocks_updated = True
            return cleaned

        if isinstance(blocks, list) and blocks:
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                btype = b.get('type')

                # Фото в блоках
                if btype in ('text', 'photos'):
                    if 'photos' in b:
                        b['photos'] = clean_file_list(b.get('photos', []))
                    if 'documents' in b:
                        b['documents'] = clean_documents_list(b.get('documents', []))

                # Фото/файлы в блюдах
                if btype in ('dishes',):
                    dishes = b.get('dishes')
                    if isinstance(dishes, list):
                        for dish in dishes:
                            if isinstance(dish, dict):
                                if isinstance(dish.get('photo'), str) and _is_file_field(dish.get('photo')):
                                    if not _file_exists(dish.get('photo'), None):
                                        dish['photo'] = ''
                                        section_cleaned += 1
                                        blocks_updated = True
                                mf = dish.get('menu_file_url') or dish.get('menu_file')
                                if isinstance(mf, str) and _is_file_field(mf):
                                    if not _file_exists(mf, None):
                                        # не удаляем ключ, просто очищаем
                                        if 'menu_file_url' in dish:
                                            dish['menu_file_url'] = ''
                                        if 'menu_file' in dish:
                                            dish['menu_file'] = ''
                                        section_cleaned += 1
                                        blocks_updated = True

                if btype in ('daily-dish',):
                    dish = b.get('dish')
                    if isinstance(dish, dict) and isinstance(dish.get('photo'), str) and _is_file_field(dish.get('photo')):
                        if not _file_exists(dish.get('photo'), None):
                            dish['photo'] = ''
                            section_cleaned += 1
                            blocks_updated = True

                # Фото в персонах
                if btype == 'person':
                    persons = b.get('persons')
                    if isinstance(persons, list):
                        for p in persons:
                            if isinstance(p, dict) and isinstance(p.get('photo'), str) and _is_file_field(p.get('photo')):
                                if not _file_exists(p.get('photo'), None):
                                    p['photo'] = ''
                                    section_cleaned += 1
                                    blocks_updated = True

            if blocks_updated:
                try:
                    section.set_content_blocks(blocks)
                except Exception:
                    # если не удалось, просто не обновляем blocks
                    blocks_updated = False

        if section_cleaned > 0 or section_updated or blocks_updated:
            data['form_data'] = cleaned_data
            section.text = json.dumps(data, ensure_ascii=False)
            db.session.commit()
            logger.info(f"Очищено {section_cleaned} несуществующих файлов и обновлено (дедуп) в разделе {section.endpoint}")
            return section_cleaned, True
        
        return 0, True
        
    except (json.JSONDecodeError, TypeError):
        return 0, False



@info_bp.route('/clean_specific_section', methods=['POST'])
def clean_specific_section():
    """Очистить несуществующие файлы из конкретного раздела"""
    try:
        data = request.get_json()
        section_endpoint = data.get('section_endpoint')
        
        if not section_endpoint:
            return jsonify({'success': False, 'error': 'Не указан раздел'})
        
        section = InfoSection.query.filter_by(endpoint=section_endpoint).first()
        if not section:
            return jsonify({'success': False, 'error': 'Раздел не найден'})
        
        section_cleaned, processed = _clean_section_files(section)
        
        if processed:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Очищено {section_cleaned} несуществующих файлов из раздела {section_endpoint}'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Несуществующих файлов не найдено'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/clean_files')
def clean_files_page():
    """Страница для очистки файлов"""
    return current_app.send_static_file('clean_files.html')

# Удалены dev/test/debug маршруты для чистоты кода

 

 

 

@info_bp.route('/clean_all_orphaned_files', methods=['POST'])
@login_required
def clean_all_orphaned_files():
    """Очищает все несуществующие файлы из всех разделов"""
    try:
        sections = InfoSection.query.all()
        total_cleaned = 0
        processed_sections = 0
        
        for section in sections:
            if section.text:
                cleaned_count, processed = _clean_section_files(section)
                if processed:
                    total_cleaned += cleaned_count
                    processed_sections += 1
        
        if processed_sections > 0:
            db.session.commit()
            return jsonify({
                'success': True,
                'total_cleaned': total_cleaned,
                'processed_sections': processed_sections,
                'message': f'Очищено {total_cleaned} несуществующих файлов из {processed_sections} разделов'
            })
        else:
            return jsonify({
                'success': True,
                'total_cleaned': 0,
                'processed_sections': 0,
                'message': 'Нет файлов для очистки'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/upload_main_file', methods=['POST'])
@login_required
def upload_main_file():
    """Загрузка файла в раздел Основные сведения"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не найден'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        # Автоматически очищаем несуществующие файлы перед загрузкой
        try:
            section_obj = InfoSection.query.filter_by(endpoint='main').first()
            if section_obj:
                _clean_section_files(section_obj)
        except Exception as e:
            logger.error(f"Ошибка при автоматической очистке файлов: {e}")
        
        # Сохраняем файл в папку main
        file_info = file_manager.save_file(file, 'main')
        
        if file_info:
            # Обновляем базу данных с информацией о файле
            section = InfoSection.query.filter_by(endpoint='main').first()
            if section:
                if section.text:
                    data = json.loads(section.text)
                else:
                    data = {'form_data': {}}
                
                # Добавляем файл в form_data
                if 'files' not in data['form_data']:
                    data['form_data']['files'] = []
                
                data['form_data']['files'].append({
                    'filename': file_info['filename'],
                    'original_name': file_info['original_name'],
                    'url': file_info['url'],
                    'size': file_info['size'],
                    'uploaded_at': file_info['created_at']
                })
                
                section.text = json.dumps(data, ensure_ascii=False)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'filename': file_info['filename'],
                'original_name': file_info['original_name'],
                'url': file_info['url'],
                'size': file_info['size']
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка при сохранении файла'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/delete_main_file', methods=['POST'])
@login_required
def delete_main_file():
    """Удаление файла из раздела Основные сведения"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'Имя файла не указано'})
        
        # Удаляем файл с диска
        file_manager.delete_file(filename, 'main')
        
        # Удаляем файл из базы данных
        section = InfoSection.query.filter_by(endpoint='main').first()
        if section and section.text:
            data = json.loads(section.text)
            if 'form_data' in data and 'files' in data['form_data']:
                data['form_data']['files'] = [f for f in data['form_data']['files'] if f['filename'] != filename]
                section.text = json.dumps(data, ensure_ascii=False)
                db.session.commit()
        
        return jsonify({'success': True, 'message': 'Файл удален'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/get_main_files', methods=['GET'])
def get_main_files():
    """Получение списка файлов раздела Основные сведения"""
    try:
        # Автоматически очищаем несуществующие файлы перед получением списка
        try:
            section_obj = InfoSection.query.filter_by(endpoint='main').first()
            if section_obj:
                _clean_section_files(section_obj)
        except Exception as e:
            logger.error(f"Ошибка при автоматической очистке файлов: {e}")
        
        section = InfoSection.query.filter_by(endpoint='main').first()
        if not section or not section.text:
            return jsonify({'success': True, 'files': []})
        
        data = json.loads(section.text)
        files = data.get('form_data', {}).get('files', [])
        
        return jsonify({'success': True, 'files': files})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/main_page')
def main_page():
    """Страница Основные сведения с интерфейсом загрузки файлов"""
    return render_template('info/main_page.html')

@info_bp.route('/clean_field_files', methods=['POST'])
@login_required
def clean_field_files():
    """Очистка старых файлов из конкретного поля раздела"""
    try:
        data = request.get_json()
        section_endpoint = data.get('section_endpoint')
        field_name = data.get('field_name')
        
        if not section_endpoint or not field_name:
            return jsonify({'success': False, 'error': 'Не указан раздел или поле'})
        
        section = InfoSection.query.filter_by(endpoint=section_endpoint).first()
        if not section:
            return jsonify({'success': False, 'error': 'Раздел не найден'})
        
        if not section.text:
            return jsonify({'success': True, 'message': 'Нет данных для очистки'})
        
        try:
            data = json.loads(section.text)
            if 'form_data' not in data or field_name not in data['form_data']:
                return jsonify({'success': True, 'message': 'Поле не найдено'})
            
            field_value = data['form_data'][field_name]
            if not field_value or not isinstance(field_value, str):
                return jsonify({'success': True, 'message': 'Поле пустое'})
            
            # Удаляем старые файлы из файловой системы
            cleaned_count = 0
            if field_value.startswith('/download_file/') or field_value.startswith('/info/download_file/'):
                # Одиночный файл
                old_filename = field_value.split('/')[-1]
                if file_manager.delete_file(old_filename, section_endpoint):
                    cleaned_count += 1
            elif ',' in field_value:
                # Несколько файлов
                old_files = [url.strip() for url in field_value.split(',') if url.strip()]
                for old_file_url in old_files:
                    if old_file_url.startswith('/download_file/') or old_file_url.startswith('/info/download_file/'):
                        old_filename = old_file_url.split('/')[-1]
                        if file_manager.delete_file(old_filename, section_endpoint):
                            cleaned_count += 1
            
            # Очищаем поле в базе данных
            data['form_data'][field_name] = ''
            section.text = json.dumps(data, ensure_ascii=False)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'cleaned_count': cleaned_count,
                'message': f'Очищено {cleaned_count} файлов из поля {field_name}'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Ошибка при очистке поля: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@info_bp.route('/force_cleanup', methods=['POST'])
@login_required
def force_cleanup():
    """Принудительная очистка несуществующих файлов"""
    try:
        uploads_root = os.path.join(current_app.root_path, 'static', 'uploads')
        uploads_info_root = os.path.join(uploads_root, 'info')

        sections = InfoSection.query.all()
        total_cleaned = 0
        processed_sections = 0
        
        for section in sections:
            if section.text:
                try:
                    data = json.loads(section.text)
                    if 'form_data' in data:
                        for field_name, field_value in data['form_data'].items():
                            if isinstance(field_value, str) and field_value.strip():
                                # Обрабатываем поля с файлами
                                file_urls = [url.strip() for url in field_value.split(',') if url.strip()]
                                valid_urls = []
                                
                                for file_url in file_urls:
                                    if '/info/download_file/' in file_url or '/download_file/' in file_url:
                                        filename = file_url.split('/')[-1]
                                        
                                        # Проверяем существование файла в разных структурах
                                        file_exists = False
                                        
                                        # Проверяем новую структуру info/год/раздел/
                                        for root, dirs, files in os.walk(uploads_info_root):
                                            if filename in files:
                                                file_exists = True
                                                break
                                        
                                        # Проверяем старую структуру
                                        if not file_exists:
                                            old_path = os.path.join(uploads_root, section.endpoint, filename)
                                            if os.path.exists(old_path):
                                                file_exists = True
                                        
                                        if file_exists:
                                            valid_urls.append(file_url)
                                            logger.debug(f"Файл существует: {filename}")
                                        else:
                                            logger.debug(f"Файл не найден: {filename}")
                                            total_cleaned += 1
                                    else:
                                        valid_urls.append(file_url)
                                
                                # Обновляем поле
                                data['form_data'][field_name] = ', '.join(valid_urls) if valid_urls else ''
                        
                        section.text = json.dumps(data, ensure_ascii=False)
                        processed_sections += 1
                        logger.info(f"Очищен раздел {section.endpoint}")
                
                except Exception as e:
                    logger.error(f"Ошибка при обработке раздела {section.endpoint}: {e}")
        
        if processed_sections > 0:
            db.session.commit()
            return jsonify({
                'success': True,
                'total_cleaned': total_cleaned,
                'processed_sections': processed_sections,
                'message': f'Очищено {total_cleaned} несуществующих файлов из {processed_sections} разделов'
            })
        else:
            return jsonify({
                'success': True,
                'total_cleaned': 0,
                'processed_sections': 0,
                'message': 'Нет файлов для очистки'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

