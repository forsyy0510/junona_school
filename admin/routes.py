"""
Маршруты для административной панели
"""
from flask import render_template, request, jsonify, send_file
from flask_login import login_required
from . import admin_bp
from .backup_restore import (
    preview_folders_backup,
    export_folders_backup,
    import_folders_backup,
)
from info.models import InfoSection
from database import db
from utils.logger import logger
import json
import os
from io import BytesIO
from datetime import datetime


@admin_bp.route('/sitemap')
@login_required
def sitemap():
    """Карта сайта для управления страницами"""
    return render_template('admin/sitemap.html')


@admin_bp.route('/api/sections')
@login_required
def get_all_sections():
    """Получить разделы левого меню (sidebar) для карты сайта"""
    try:
        all_sections = InfoSection.query.all()
        sections = [s for s in all_sections if s.url and s.url.startswith('/sidebar/')]
        result = []
        
        for section in sections:
            # Парсим данные для определения родителя
            parent = None
            order = 0
            try:
                if section.text:
                    data = json.loads(section.text)
                    form_data = data.get('form_data', {}) if isinstance(data, dict) else {}
                    parent = form_data.get('parent')
                    # Нормализуем parent (убираем /sidebar/ если есть)
                    if parent and isinstance(parent, str) and parent.startswith('/sidebar/'):
                        parent = parent.replace('/sidebar/', '')
                    order = form_data.get('order', 0)
            except Exception:
                pass
            
            result.append({
                'id': section.id,
                'endpoint': section.endpoint,
                'title': section.title,
                'url': section.url,
                'parent': parent,
                'order': order,
                'has_children': False  # Определим позже
            })
        
        # Определяем дочерние элементы
        for item in result:
            for other in result:
                if other.get('parent') == item.get('endpoint'):
                    item['has_children'] = True
                    break
        
        return jsonify({'success': True, 'sections': result})
    except Exception as e:
        logger.error(f"Ошибка при получении разделов: {e}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/sections/order', methods=['POST'])
@login_required
def update_section_order():
    """Обновить порядок разделов"""
    try:
        data = request.get_json()
        updates = data.get('updates', [])
        
        for update in updates:
            section_id = update.get('id')
            new_order = update.get('order')
            parent = update.get('parent')
            
            section = InfoSection.query.get(section_id)
            if section:
                # Обновляем данные в text
                text_data = {}
                if section.text:
                    try:
                        text_data = json.loads(section.text)
                    except Exception:
                        text_data = {}
                
                if 'form_data' not in text_data:
                    text_data['form_data'] = {}
                
                text_data['form_data']['order'] = new_order
                if parent is not None:
                    if parent:
                        text_data['form_data']['parent'] = parent
                        text_data['form_data']['menu_parent'] = parent
                    else:
                        for key in ('parent', 'menu_parent'):
                            if key in text_data['form_data']:
                                del text_data['form_data'][key]
                
                section.text = json.dumps(text_data, ensure_ascii=False)
        
        db.session.commit()
        logger.info(f"Порядок разделов обновлен")
        return jsonify({'success': True, 'message': 'Порядок разделов обновлен'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении порядка разделов: {e}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/sections/<int:section_id>', methods=['PATCH'])
@login_required
def update_section(section_id):
    """Обновить раздел (название)"""
    try:
        section = InfoSection.query.get(section_id)
        if not section:
            return jsonify({'success': False, 'error': 'Раздел не найден'})
        data = request.get_json() or {}
        title = (data.get('title') or '').strip()
        if title:
            section.title = title
            db.session.commit()
            logger.info(f"Раздел {section.endpoint} обновлен")
            return jsonify({'success': True, 'section': {'id': section.id, 'endpoint': section.endpoint, 'title': section.title}})
        return jsonify({'success': False, 'error': 'Название не задано'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении раздела: {e}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/sections/<int:section_id>', methods=['DELETE'])
@login_required
def delete_section(section_id):
    """Удалить раздел"""
    try:
        section = InfoSection.query.get(section_id)
        if not section:
            return jsonify({'success': False, 'error': 'Раздел не найден'})
        
        # Проверяем, есть ли дочерние элементы
        all_sections = InfoSection.query.all()
        children = []
        for s in all_sections:
            if s.id == section_id:
                continue
            try:
                if s.text:
                    data = json.loads(s.text)
                    form_data = data.get('form_data', {}) if isinstance(data, dict) else {}
                else:
                    form_data = {}
                
                parent_val = form_data.get('parent')
                if parent_val:
                    # Нормализуем parent
                    if parent_val.startswith('/sidebar/'):
                        parent_val = parent_val.replace('/sidebar/', '')
                    if parent_val == section.endpoint:
                        children.append(s)
            except Exception as e:
                logger.warning(f"Ошибка при проверке раздела {s.id}: {e}")
                continue
        
        if children:
            child_titles = [c.title for c in children[:3]]  # Первые 3 для сообщения
            error_msg = f'Нельзя удалить раздел с подразделами ({len(children)} шт.). Сначала удалите подразделы: {", ".join(child_titles)}'
            if len(children) > 3:
                error_msg += f' и еще {len(children) - 3}...'
            return jsonify({'success': False, 'error': error_msg})
        
        # Удаляем связанные файлы из базы данных
        try:
            from models.models import InfoFile
            # Получаем все файлы раздела
            section_files = InfoFile.query.filter_by(section_endpoint=section.endpoint).all()
            for info_file in section_files:
                try:
                    if os.path.exists(info_file.file_path):
                        os.remove(info_file.file_path)
                        logger.debug(f"Файл удален с диска: {info_file.file_path}")
                    db.session.delete(info_file)
                    logger.debug(f"Запись о файле удалена из БД: {info_file.filename}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла {info_file.filename}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при удалении файлов раздела {section.endpoint}: {e}")
        
        db.session.delete(section)
        db.session.commit()
        logger.info(f"Раздел {section.endpoint} успешно удален")
        return jsonify({'success': True, 'message': 'Раздел успешно удален'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении раздела {section_id}: {e}")
        return jsonify({'success': False, 'error': f'Ошибка при удалении раздела: {str(e)}'})


@admin_bp.route('/api/sections/quick-create', methods=['POST'])
@login_required
def quick_create_section():
    """Быстрое создание нового раздела"""
    try:
        data = request.get_json()
        title = (data.get('title') or '').strip()
        endpoint = (data.get('endpoint') or '').strip().lower()
        parent = data.get('parent')
        
        if not title:
            return jsonify({'success': False, 'error': 'Название раздела обязательно'})
        
        if not endpoint:
            # Генерируем endpoint из названия
            import re
            endpoint = re.sub(r'[^\w\s-]', '', title.lower())
            endpoint = re.sub(r'[-\s]+', '-', endpoint)
            endpoint = endpoint.strip('-')
            if not endpoint:
                endpoint = 'new-section'
        
        # Проверяем уникальность
        existing = InfoSection.query.filter_by(endpoint=endpoint).first()
        if existing:
            return jsonify({'success': False, 'error': f'Раздел с URL "{endpoint}" уже существует'})
        
        # Создаем раздел
        text_data = {
            'text': '',
            'form_data': {}
        }
        
        if parent:
            text_data['form_data']['parent'] = parent
            text_data['form_data']['menu_parent'] = parent

        section = InfoSection(
            endpoint=endpoint,
            title=title,
            text=json.dumps(text_data, ensure_ascii=False),
            url=f'/sidebar/{endpoint}'
        )
        
        section.set_content_blocks([])
        db.session.add(section)
        db.session.commit()
        logger.info(f"Раздел {section.endpoint} успешно создан")
        
        return jsonify({
            'success': True,
            'section': {
                'id': section.id,
                'endpoint': section.endpoint,
                'title': section.title,
                'url': section.url,
                'parent': parent,
                'order': 0
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании раздела: {e}")
        return jsonify({'success': False, 'error': str(e)})


def _backup_paths():
    """Абсолютные пути к папкам instance и static/uploads."""
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return (
        os.path.join(project_root, 'instance'),
        os.path.join(project_root, 'static', 'uploads'),
    )


@admin_bp.route('/backup/export-preview')
@login_required
def backup_export_preview():
    """Предпросмотр: что попадёт в архив (instance + uploads)."""
    try:
        instance_path, uploads_path = _backup_paths()
        data = preview_folders_backup(instance_path, uploads_path)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Ошибка при предпросмотре выгрузки: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/backup/export')
@login_required
def backup_export():
    """Выгрузка резервной копии: ZIP с папками instance и uploads."""
    try:
        instance_path, uploads_path = _backup_paths()
        path = export_folders_backup(instance_path, uploads_path)
        filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        resp = send_file(
            path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename,
        )
        path_to_remove = path

        @resp.call_on_close
        def remove_temp_file():
            try:
                if path_to_remove and os.path.exists(path_to_remove):
                    os.unlink(path_to_remove)
            except OSError:
                pass

        return resp
    except Exception as e:
        logger.error(f"Ошибка при выгрузке резервной копии: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/backup/import', methods=['POST'])
@login_required
def backup_import():
    """Восстановление из ZIP (instance + uploads)."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
        f = request.files['file']
        if not f.filename or not f.filename.lower().endswith('.zip'):
            return jsonify({'success': False, 'error': 'Нужен файл .zip'}), 400
        raw = f.read()
        instance_path, uploads_path = _backup_paths()
        clear_before = request.form.get('clear_before', 'true').lower() in ('1', 'true', 'yes')
        import_folders_backup(raw, instance_path, uploads_path, clear_before=clear_before)
        logger.info("Восстановление из резервной копии выполнено успешно")
        return jsonify({'success': True, 'message': 'Резервная копия восстановлена (instance и загрузки)'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Ошибка при восстановлении из копии: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

