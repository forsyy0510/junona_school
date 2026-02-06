from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required
from . import sidebar_bp
from info.models import InfoSection
from database import db
import json
import os
import re
from datetime import datetime
from file_manager import file_manager
from utils.logger import logger


def _sidebar_file_exists(filename: str) -> bool:
    """Проверяет существование файла по имени в uploads (через БД или поиск на диске).
    Возвращает True, если файл найден, иначе False.
    """
    try:
        if not filename or not isinstance(filename, str):
            return False
        filename = filename.strip()
        if not filename:
            return False

        # filename can be URL-encoded (%20, %D0...), decode it for filesystem checks
        try:
            import urllib.parse
            decoded = urllib.parse.unquote(filename)
            filename_candidates = [filename, decoded] if decoded and decoded != filename else [filename]
        except Exception:
            filename_candidates = [filename]

        uploads_root = os.path.join(file_manager.base_upload_path)
        uploads_info_root = os.path.join(uploads_root, 'info')

        # 1) Пытаемся через БД
        try:
            from models.models import InfoFile
            info_file = InfoFile.query.filter_by(filename=filename).first()
            if info_file:
                fp = getattr(info_file, 'file_path', None)
                if fp and os.path.exists(fp):
                    return True
        except Exception:
            pass

        # 2) Ищем на диске (info/*/* и общий uploads)
        for cand in filename_candidates:
            for root, _dirs, files in os.walk(uploads_info_root):
                if cand in files:
                    return True
            for root, _dirs, files in os.walk(uploads_root):
                if cand in files:
                    return True

        return False
    except Exception:
        return False


def _clean_sidebar_content_blocks_files(blocks):
    """Удаляет из content_blocks ссылки на файлы, которых нет на диске/в БД.
    Поддерживает: block.photos (text/photos), block.documents, person.photo, dishes.photo.
    Возвращает (cleaned_blocks, removed_count).
    """
    removed = 0

    def is_file_url(u: str) -> bool:
        return isinstance(u, str) and (
            u.startswith('/info/download_file/') or
            u.startswith('/download_file/') or
            u.startswith('/sidebar/download_file/') or
            u.startswith('/static/uploads/') or
            u.startswith('/food/')
        )

    def filename_from_url(u: str) -> str:
        try:
            url_clean = u.split('|')[0].strip() if '|' in u else u.strip()
            fn = url_clean.split('/')[-1].strip()
            try:
                import urllib.parse
                return urllib.parse.unquote(fn)
            except Exception:
                return fn
        except Exception:
            return ''

    def clean_url_list(urls):
        nonlocal removed
        if not isinstance(urls, list):
            return urls
        out = []
        for u in urls:
            if is_file_url(u):
                fn = filename_from_url(u)
                if fn and _sidebar_file_exists(fn):
                    out.append(u)
                else:
                    removed += 1
            else:
                out.append(u)
        return out

    def clean_docs_list(docs):
        nonlocal removed
        if not isinstance(docs, list):
            return docs
        out = []
        for d in docs:
            if isinstance(d, dict):
                u = d.get('url')
                if is_file_url(u):
                    fn = filename_from_url(u)
                    if fn and _sidebar_file_exists(fn):
                        out.append(d)
                    else:
                        removed += 1
                else:
                    out.append(d)
            elif is_file_url(d):
                fn = filename_from_url(d)
                if fn and _sidebar_file_exists(fn):
                    out.append(d)
                else:
                    removed += 1
            else:
                out.append(d)
        return out

    if not isinstance(blocks, list):
        return blocks, 0

    for b in blocks:
        if not isinstance(b, dict):
            continue
        btype = b.get('type')

        if btype in ('text', 'photos'):
            if 'photos' in b:
                b['photos'] = clean_url_list(b.get('photos', []))
            if 'documents' in b:
                b['documents'] = clean_docs_list(b.get('documents', []))

        if btype == 'person':
            persons = b.get('persons')
            if isinstance(persons, list):
                for p in persons:
                    if isinstance(p, dict) and is_file_url(p.get('photo', '')):
                        fn = filename_from_url(p.get('photo', ''))
                        if not (fn and _sidebar_file_exists(fn)):
                            p['photo'] = ''
                            removed += 1

        if btype == 'dishes':
            dishes = b.get('dishes')
            if isinstance(dishes, list):
                for dish in dishes:
                    if isinstance(dish, dict) and is_file_url(dish.get('photo', '')):
                        fn = filename_from_url(dish.get('photo', ''))
                        if not (fn and _sidebar_file_exists(fn)):
                            dish['photo'] = ''
                            removed += 1

    return blocks, removed


def _clean_sidebar_form_data_files(section: InfoSection) -> int:
    """Удаляет из section.text.form_data ссылки на отсутствующие файлы.
    Возвращает количество удаленных ссылок.
    """
    try:
        if not section or not section.text:
            return 0
        td = json.loads(section.text)
        if not isinstance(td, dict):
            return 0
        form_data = td.get('form_data', {})
        if not isinstance(form_data, dict):
            return 0

        def is_file_url(u: str) -> bool:
            return isinstance(u, str) and (
                u.startswith('/info/download_file/') or
                u.startswith('/download_file/') or
                u.startswith('/static/uploads/') or
                u.startswith('/food/') or
                u.startswith('/sidebar/download_file/')
            )

        def filename_from_url(u: str) -> str:
            try:
                u = u.split('|')[0].strip() if '|' in u else u.strip()
                fn = u.split('/')[-1].strip()
                try:
                    import urllib.parse
                    return urllib.parse.unquote(fn)
                except Exception:
                    return fn
            except Exception:
                return ''

        removed = 0
        updated = False

        for key, value in list(form_data.items()):
            if not isinstance(value, str) or not value.strip():
                continue

            # Поле может хранить один URL или несколько через запятую (и опционально url|display_name)
            items = [x.strip() for x in value.split(',') if x.strip()]
            if not items:
                continue

            # Если это не файл-URL — пропускаем поле
            if not any(is_file_url(x.split('|')[0].strip()) for x in items):
                continue

            kept = []
            for item in items:
                url_part = item.split('|')[0].strip() if '|' in item else item.strip()
                if is_file_url(url_part):
                    fn = filename_from_url(url_part)
                    if fn and _sidebar_file_exists(fn):
                        kept.append(item)
                    else:
                        removed += 1
                        updated = True
                else:
                    kept.append(item)

            new_val = ', '.join(kept)
            if new_val != value:
                form_data[key] = new_val
                updated = True

        if updated:
            td['form_data'] = form_data
            section.text = json.dumps(td, ensure_ascii=False)

        return removed
    except Exception:
        return 0

def render_sidebar_section(endpoint, template_name):
    """Отображает sidebar раздел с поддержкой редактирования через InfoSection"""
    section = InfoSection.query.filter_by(endpoint=endpoint).first()
    if section:
        # Чистим content_blocks от ссылок на отсутствующие файлы (иначе появляются "пустые" плитки)
        try:
            blocks = section.get_content_blocks()
            cleaned_blocks, removed = _clean_sidebar_content_blocks_files(blocks)
            if removed > 0:
                section.set_content_blocks(cleaned_blocks)
                db.session.commit()
        except Exception:
            pass

        # Чистим form_data от битых ссылок (в т.ч. поле images)
        try:
            removed_fd = _clean_sidebar_form_data_files(section)
            if removed_fd > 0:
                db.session.commit()
        except Exception:
            pass

        # Находим дочерние разделы (только прямые дети, вложенные будут отображаться рекурсивно в шаблоне)
        def find_direct_children(parent_endpoint):
            """Находит только прямые дочерние разделы (не рекурсивно)"""
            direct_children = []
            all_sections = InfoSection.query.all()
            
            # Специальная проверка для статического подраздела "Архив блюд"
            if parent_endpoint == 'food':
                archive_section = InfoSection.query.filter_by(endpoint='nutrition-dishes-archive').first()
                if archive_section:
                    direct_children.append(archive_section)
            
            for s in all_sections:
                if s.endpoint == parent_endpoint:
                    continue
                
                # Пропускаем "Архив блюд", так как он уже добавлен выше
                if s.endpoint == 'nutrition-dishes-archive' and parent_endpoint == 'food':
                    continue
                    
                try:
                    form = {}
                    if s.text:
                        try:
                            td = json.loads(s.text)
                            form = td.get('form_data', {}) if isinstance(td, dict) else {}
                        except Exception:
                            form = {}
                    
                    parent_val = form.get('parent')
                    if parent_val:
                        # Нормализуем parent_val
                        if parent_val.startswith('/sidebar/'):
                            parent_val = parent_val.replace('/sidebar/', '')
                        if parent_val == parent_endpoint:
                            # Проверяем, не добавлен ли уже этот подраздел
                            if s not in direct_children:
                                direct_children.append(s)
                except Exception:
                    continue
            
            return direct_children
        
        # Для отображения нужно передать не только детей, но и все разделы для поиска вложенных
        children = []
        all_sections_for_template = []
        try:
            children = find_direct_children(section.endpoint)
            # Передаем все разделы в шаблон для рекурсивного поиска вложенных
            all_sections_for_template = InfoSection.query.all()
            # Найдено подразделов
        except Exception as e:
            # Ошибка при поиске подразделов - логируем только при необходимости
            children = []

        # Если раздел есть в БД, отображаем его через info/section.html (даже если text пустой)
        # Передаем текущую дату для фильтрации блюд в архиве
        today = datetime.now().strftime('%d.%m.%Y')
        response = make_response(render_template('info/section.html', section=section, children=children, all_sections=all_sections_for_template, today=today))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    # Если раздела нет в БД, рендерим через общий шаблон info/section.html,
    # создавая временный объект с минимальными полями, чтобы была доступна кнопка "Редактировать"
    class TempSection:
        def __init__(self, endpoint, title, url):
            self.id = None
            self.endpoint = endpoint
            self.title = title
            self.url = url
            self.text = json.dumps({'text': '', 'form_data': {}}, ensure_ascii=False)
        def get_content_blocks(self):
            return []

    temp = TempSection(endpoint, template_name.replace('_', ' ').title(), f'/sidebar/{endpoint}')

    # для единообразия передаем пустые списки детей
    response = make_response(render_template('info/section.html', section=temp, children=[], all_sections=[]))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Основные пункты меню
@sidebar_bp.route('/appeals')
def appeals():
    return render_sidebar_section('appeals', 'appeals')

@sidebar_bp.route('/anti-corruption')
def anti_corruption():
    return render_sidebar_section('anti-corruption', 'anti_corruption')

@sidebar_bp.route('/additional-info')
def additional_info():
    return render_sidebar_section('additional-info', 'additional_info')

@sidebar_bp.route('/nutrition')
def nutrition():
    """Исторически существовал sidebar-раздел 'nutrition' с заголовком 'Питание'.
    Сейчас основной контент 'Питание' живет в /sveden/food, поэтому чтобы не было
    дублей страниц — ведем пользователя на официальный раздел.
    """
    return redirect('/sveden/food')

@sidebar_bp.route('/food')
def food():
    """Не дублируем /sveden/food (InfoSection endpoint='food')."""
    return redirect('/sveden/food')

@sidebar_bp.route('/nutrition-dishes-archive')
def nutrition_dishes_archive():
    return render_sidebar_section('nutrition-dishes-archive', 'nutrition_dishes_archive')

@sidebar_bp.route('/admission-grade1')
def admission_grade1():
    return render_sidebar_section('admission-grade1', 'admission_grade1')

@sidebar_bp.route('/history')
def history():
    return render_sidebar_section('history', 'history')

# Дополнительные пункты меню
@sidebar_bp.route('/ushakov-festival')
def ushakov_festival():
    return render_sidebar_section('ushakov-festival', 'ushakov_festival')

@sidebar_bp.route('/schedule')
def schedule():
    return render_sidebar_section('schedule', 'schedule')

@sidebar_bp.route('/class-leadership-payment')
def class_leadership_payment():
    return render_sidebar_section('class-leadership-payment', 'class_leadership_payment')

@sidebar_bp.route('/electronic-environment')
def electronic_environment():
    return render_sidebar_section('electronic-environment', 'electronic_environment')

@sidebar_bp.route('/useful-info')
def useful_info():
    return render_sidebar_section('useful-info', 'useful_info')

@sidebar_bp.route('/information-security')
def information_security():
    return render_sidebar_section('information-security', 'information_security')

@sidebar_bp.route('/road-safety')
def road_safety():
    return render_sidebar_section('road-safety', 'road_safety')

@sidebar_bp.route('/targeted-training')
def targeted_training():
    return render_sidebar_section('targeted-training', 'targeted_training')

@sidebar_bp.route('/social-order-implementation')
def social_order_implementation():
    return render_sidebar_section('social-order-implementation', 'social_order_implementation')

@sidebar_bp.route('/recreation-organization')
def recreation_organization():
    return render_sidebar_section('recreation-organization', 'recreation_organization')

@sidebar_bp.route('/for-parents')
def for_parents():
    return render_sidebar_section('for-parents', 'for_parents')

@sidebar_bp.route('/parent-education')
def parent_education():
    return render_sidebar_section('parent-education', 'parent_education')

@sidebar_bp.route('/gia-ege-oge')
def gia_ege_oge():
    return render_sidebar_section('gia-ege-oge', 'gia_ege_oge')

@sidebar_bp.route('/admission-grade10')
def admission_grade10():
    return render_sidebar_section('admission-grade10', 'admission_grade10')

@sidebar_bp.route('/memos')
def memos():
    return render_sidebar_section('memos', 'memos')

@sidebar_bp.route('/cbr-fraud-prevention')
def cbr_fraud_prevention():
    return render_sidebar_section('cbr-fraud-prevention', 'cbr_fraud_prevention')

@sidebar_bp.route('/financial-literacy')
def financial_literacy():
    return render_sidebar_section('financial-literacy', 'financial_literacy')

@sidebar_bp.route('/parental-control')
def parental_control():
    return render_sidebar_section('parental-control', 'parental_control')

# Новые недостающие разделы
@sidebar_bp.route('/inclusive-education')
def inclusive_education():
    return render_sidebar_section('inclusive-education', 'inclusive_education')

@sidebar_bp.route('/anti-terrorism')
def anti_terrorism():
    return render_sidebar_section('anti-terrorism', 'anti_terrorism')

@sidebar_bp.route('/orkse')
def orkse():
    return render_sidebar_section('orkse', 'orkse')

@sidebar_bp.route('/sanitary-shield')
def sanitary_shield():
    return render_sidebar_section('sanitary-shield', 'sanitary_shield')

# Универсальный маршрут для динамически созданных разделов
# Должен быть ПОСЛЕ всех конкретных маршрутов
@sidebar_bp.route('/api/nutrition/menu-files')
def get_nutrition_menu_files():
    """Получить список Excel файлов меню с фильтрацией по датам"""
    try:
        from models.models import InfoFile
        import urllib.parse
        
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        day = request.args.get('day', type=int)
        
        files_list = []
        
        # Сначала ищем файлы в БД
        db_files = []
        try:
            query = InfoFile.query.filter(
                (InfoFile.section_endpoint == 'food') | (InfoFile.field_name == 'menu_file')
            ).filter(
                (InfoFile.filename.like('%.xlsx')) | (InfoFile.filename.like('%.xls'))
            )
            
            db_files = query.all()
        except Exception as e:
            # Если ошибка из-за отсутствующих колонок в БД, пропускаем поиск в БД
            if 'no such column' in str(e).lower() or 'file_data' in str(e).lower():
                # Пропускаем поиск в БД, будем искать только в файловой системе
                pass
            else:
                # Другая ошибка - пробрасываем дальше
                raise
        
        for info_file in db_files:
            filename = info_file.filename
            
            # Извлекаем дату из имени файла (формат: YYYY-MM-DD-sm.xlsx)
            try:
                date_part = filename.split('-')[0:3]  # Год, месяц, день
                if len(date_part) >= 3:
                    file_year = int(date_part[0])
                    file_month = int(date_part[1])
                    file_day = int(date_part[2])
                    
                    # Фильтруем по датам если указаны
                    if year and file_year != year:
                        continue
                    if month and file_month != month:
                        continue
                    if day and file_day != day:
                        continue
                    
                    files_list.append({
                        'filename': filename,
                        'url': f"/food/{urllib.parse.quote(filename)}",  # всегда через /food/<filename> (URL-encoded)
                        'date': f'{file_year}-{file_month:02d}-{file_day:02d}',
                        'year': file_year,
                        'month': file_month,
                        'day': file_day,
                        'size': info_file.file_size
                    })
            except (ValueError, IndexError):
                # Если не удалось извлечь дату, пропускаем файл
                continue
        
        # Также проверяем файловую систему для обратной совместимости.
        # ВАЖНО: upload-menu сохраняет файлы через file_manager.save_info_file(..., 'food', 'menu_file'),
        # т.е. они оказываются в static/uploads/info/<YEAR>/food/, поэтому ищем и там тоже.
        existing_filenames = {f.get('filename') for f in files_list if isinstance(f, dict)}

        def try_add_file(file_path, filename):
            if not filename:
                return
            lower = filename.lower()
            if not (lower.endswith('.xlsx') or lower.endswith('.xls')):
                return
            if filename in existing_filenames:
                return

            # Извлекаем дату из имени файла (формат: YYYY-MM-DD-*.xlsx)
            try:
                date_part = filename.split('-')[0:3]  # Год, месяц, день
                if len(date_part) < 3:
                    return
                file_year = int(date_part[0])
                file_month = int(date_part[1])
                file_day = int(date_part[2])
            except (ValueError, IndexError):
                return

            # Фильтруем по датам если указаны
            if year and file_year != year:
                return
            if month and file_month != month:
                return
            if day and file_day != day:
                return

            try:
                stat = os.stat(file_path)
                file_size = stat.st_size
            except OSError:
                file_size = 0

            files_list.append({
                'filename': filename,
                'url': f"/food/{urllib.parse.quote(filename)}",  # всегда через /food/<filename> (URL-encoded)
                'date': f'{file_year}-{file_month:02d}-{file_day:02d}',
                'year': file_year,
                'month': file_month,
                'day': file_day,
                'size': file_size
            })
            existing_filenames.add(filename)

        # 1) Старый путь (если где-то остался)
        menu_dir = os.path.join(file_manager.base_upload_path, 'nutrition', 'menus')
        if os.path.exists(menu_dir):
            for filename in os.listdir(menu_dir):
                try_add_file(os.path.join(menu_dir, filename), filename)

        # 2) Актуальный путь file_manager для 'food': static/uploads/info/<YEAR>/food/
        info_root = os.path.join(file_manager.base_upload_path, 'info')
        if os.path.exists(info_root):
            for root, _dirs, filenames in os.walk(info_root):
                if os.path.basename(root) != 'food':
                    continue
                for filename in filenames:
                    try_add_file(os.path.join(root, filename), filename)
        
        # Сортируем по дате (новые сначала)
        files_list.sort(key=lambda x: (x['year'], x['month'], x['day']), reverse=True)
        
        return jsonify({
            'success': True,
            'files': files_list,
            'total': len(files_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'instructions': [
                'Проверьте правильность параметров фильтрации',
                'Убедитесь, что папка с файлами существует',
                'Если проблема сохраняется, сообщите администратору'
            ]
        }), 500


@sidebar_bp.route('/api/nutrition/upload-menu', methods=['POST'])
@login_required
def upload_nutrition_menu():
    """Загрузить Excel файл меню"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Файл не найден',
                'instructions': [
                    'Выберите файл для загрузки',
                    'Поддерживаются только файлы формата Excel (.xlsx, .xls)'
                ]
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Файл не выбран',
                'instructions': [
                    'Выберите файл для загрузки',
                    'Поддерживаются только файлы формата Excel (.xlsx, .xls)'
                ]
            }), 400
        
        # Проверяем расширение файла
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            return jsonify({
                'success': False,
                'error': 'Неверный формат файла',
                'instructions': [
                    'Поддерживаются только файлы Excel (.xlsx, .xls)',
                    'Проверьте расширение загружаемого файла'
                ]
            }), 400
        
        # Поддерживаем 2 формата:
        # 1) Файлы меню с датой: YYYY-MM-DD-sm.xlsx
        # 2) Шаблоны/доп. файлы: tmYYYY-sm.xlsx, kpYYYY.xlsx, findex.xlsx
        filename = file.filename or ''
        date_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})', filename)
        file_date = None
        is_template = False

        if date_match:
            year = date_match.group(1)
            month = date_match.group(2)
            day = date_match.group(3)

            # Проверяем корректность даты
            try:
                file_date = datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Неверная дата в имени файла',
                    'instructions': [
                        'Проверьте дату в имени файла',
                        'Формат должен быть: YYYY-MM-DD-sm.xlsx',
                        'Например: 2025-10-02-sm.xlsx'
                    ]
                }), 400
        else:
            lower = filename.lower()
            if re.match(r'^tm\d{4}-sm\.xlsx$', lower) or re.match(r'^kp\d{4}\.xlsx$', lower) or lower == 'findex.xlsx':
                is_template = True
            else:
                return jsonify({
                    'success': False,
                    'error': 'Неверный формат имени файла',
                    'instructions': [
                        'Для меню на день: YYYY-MM-DD-sm.xlsx (например: 2025-10-02-sm.xlsx)',
                        'Для доп. файлов: tmYYYY-sm.xlsx, kpYYYY.xlsx, findex.xlsx',
                        'Поддерживаются только .xlsx/.xls'
                    ]
                }), 400
        
        # Используем file_manager для сохранения в файловую систему
        file_info = file_manager.save_info_file(file, 'food', 'menu_file')
        
        if not file_info:
            return jsonify({
                'success': False,
                'error': 'Ошибка при сохранении файла',
                'instructions': [
                    'Проверьте формат файла',
                    'Убедитесь, что файл не поврежден',
                    'Если проблема сохраняется, сообщите администратору'
                ]
            }), 500
        
        # Сохраняем файл в базу данных
        from models.models import InfoFile
        
        try:
            # Читаем данные файла для сохранения в БД
            file.seek(0)  # Возвращаемся в начало файла
            file_data = file.read()
            
            # Проверяем, существует ли уже такой файл в БД
            existing_file = InfoFile.query.filter_by(
                filename=file_info['filename'],
                section_endpoint='food',
                field_name='menu_file'
            ).first()
            
            if existing_file:
                # Обновляем существующий файл
                existing_file.original_filename = file_info['original_name']
                existing_file.file_path = file_info['file_path']
                existing_file.file_size = file_info['size']
                existing_file.mime_type = file_info['mime_type']
                existing_file.is_image = file_info['is_image']
                existing_file.display_name = file_info['original_name']
                existing_file.file_data = file_data
                existing_file.stored_in_db = True
                existing_file.upload_date = datetime.now()
            else:
                # Создаем новую запись в БД
                info_file = InfoFile(
                    filename=file_info['filename'],
                    original_filename=file_info['original_name'],
                    file_path=file_info['file_path'],
                    section_endpoint='food',
                    field_name='menu_file',
                    file_size=file_info['size'],
                    mime_type=file_info['mime_type'],
                    is_image=file_info['is_image'],
                    display_name=file_info['original_name'],
                    file_data=file_data,
                    stored_in_db=True
                )
                db.session.add(info_file)
            
            db.session.commit()
        except Exception as db_error:
            # Если ошибка из-за отсутствующих колонок в БД, просто логируем
            if 'no such column' in str(db_error).lower() or 'file_data' in str(db_error).lower():
                logger.warning(
                    "Поля file_data/stored_in_db еще не добавлены в БД. "
                    "Файл сохранен только в файловую систему."
                )
            else:
                logger.error(f"Ошибка при сохранении файла в БД: {db_error}")
                db.session.rollback()
        
        return jsonify({
            'success': True,
            'message': 'Файл меню успешно загружен',
            'filename': file_info['filename'],
            'url': f'/food/{file_info["filename"]}',  # Используем специальный URL для питания
            'date': file_date.strftime('%Y-%m-%d') if file_date else '',
            'is_template': is_template
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка при загрузке файла: {str(e)}',
            'instructions': [
                'Проверьте формат файла',
                'Убедитесь, что файл не поврежден',
                'Попробуйте загрузить файл снова',
                'Если проблема сохраняется, сообщите администратору'
            ]
        }), 500


@sidebar_bp.route('/<section_endpoint>')
def dynamic_sidebar_section(section_endpoint):
    """Универсальный маршрут для отображения любых sidebar разделов"""
    # Исключаем служебные маршруты
    if section_endpoint in ['create', 'section', 'wizard_save', 'upload_file', 'delete_file', 'get_section_files', 'download_file']:
        # Эти маршруты обрабатываются отдельно
        return redirect(url_for('main.index'))
    
    # Проверяем, есть ли раздел в базе данных
    section = InfoSection.query.filter_by(endpoint=section_endpoint).first()
    
    if section:
        # Чистим content_blocks от ссылок на отсутствующие файлы
        try:
            blocks = section.get_content_blocks()
            cleaned_blocks, removed = _clean_sidebar_content_blocks_files(blocks)
            if removed > 0:
                section.set_content_blocks(cleaned_blocks)
                db.session.commit()
        except Exception:
            pass

        # Чистим form_data от битых ссылок
        try:
            removed_fd = _clean_sidebar_form_data_files(section)
            if removed_fd > 0:
                db.session.commit()
        except Exception:
            pass

        # Используем ту же функцию поиска прямых детей, что и в render_sidebar_section
        def find_direct_children(parent_endpoint):
            """Находит только прямые дочерние разделы"""
            direct_children = []
            all_sections = InfoSection.query.all()
            
            # Специальная проверка для статического подраздела "Архив блюд"
            if parent_endpoint == 'food':
                archive_section = InfoSection.query.filter_by(endpoint='nutrition-dishes-archive').first()
                if archive_section:
                    direct_children.append(archive_section)
            
            for s in all_sections:
                if s.endpoint == parent_endpoint:
                    continue
                
                # Пропускаем "Архив блюд", так как он уже добавлен выше
                if s.endpoint == 'nutrition-dishes-archive' and parent_endpoint == 'food':
                    continue
                    
                try:
                    form = {}
                    if s.text:
                        try:
                            td = json.loads(s.text)
                            form = td.get('form_data', {}) if isinstance(td, dict) else {}
                        except Exception:
                            form = {}
                    
                    parent_val = form.get('parent')
                    if parent_val:
                        if parent_val.startswith('/sidebar/'):
                            parent_val = parent_val.replace('/sidebar/', '')
                        if parent_val == parent_endpoint:
                            # Проверяем, не добавлен ли уже этот подраздел
                            if s not in direct_children:
                                direct_children.append(s)
                except Exception:
                    continue
            
            return direct_children
        
        children = []
        all_sections_for_template = []
        try:
            children = find_direct_children(section.endpoint)
            all_sections_for_template = InfoSection.query.all()
        except Exception as e:
            # Ошибка при поиске подразделов
            pass
        
        try:
            # Передаем текущую дату для фильтрации блюд в архиве
            today = datetime.now().strftime('%d.%m.%Y')
            response = make_response(render_template('info/section.html', section=section, children=children, all_sections=all_sections_for_template, today=today))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        except Exception as e:
            # Ошибка при отображении раздела
            flash(f'Ошибка при отображении раздела: {str(e)}', 'error')
            return redirect(url_for('main.index'))
    else:
        # Если раздела нет, проверяем, есть ли шаблон по умолчанию
        # Для новых разделов возвращаем 404, но с информативным сообщением
        flash(f'Раздел "{section_endpoint}" не найден. Возможно, он был удален или еще не создан.', 'error')
        return redirect(url_for('main.index'))

# API эндпоинты для работы с мастером заполнения
@sidebar_bp.route('/get_all_sections')
def get_all_sections():
    """Получить все sidebar разделы для мастера бокового меню"""
    try:
        # В мастере бокового меню управляем не только /sidebar/*,
        # но и разделом "Питание" (endpoint='food') и его подразделами (food-sub-*, daily menu),
        # так как он отображается в боковом меню и имеет вложенность.
        all_sections = InfoSection.query.all()
        sections_data = []
        
        for section in all_sections:
            try:
                if not section or not section.endpoint:
                    continue
                text_data = json.loads(section.text) if section.text else {}
                form_data = text_data.get('form_data', {})

                parent_val = None
                try:
                    parent_val = form_data.get('parent') if isinstance(form_data, dict) else None
                    if isinstance(parent_val, str) and parent_val.startswith('/sidebar/'):
                        parent_val = parent_val.replace('/sidebar/', '')
                except Exception:
                    parent_val = None

                # Берем:
                # - все /sidebar/*
                # - 'food' (хотя url у него не /sidebar)
                # - все подразделы food (parent == 'food')
                is_sidebar = bool(section.url and str(section.url).startswith('/sidebar/'))
                is_food_root = section.endpoint == 'food'
                is_food_child = parent_val == 'food'
                if not (is_sidebar or is_food_root or is_food_child):
                    continue
                
                sections_data.append({
                    'id': section.id,
                    'endpoint': section.endpoint,
                    'title': section.title,
                    'url': section.url,
                    'parent': parent_val,
                    'menu_parent': (form_data.get('menu_parent') if isinstance(form_data, dict) else None),
                    'order': form_data.get('order', 0),
                    'show_in_menu': form_data.get('show_in_menu', None),
                })
            except Exception as e:
                # Если не удалось распарсить text, пропускаем раздел
                continue
        
        return jsonify({
            'success': True,
            'sections': sections_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@sidebar_bp.route('/reorder_sections', methods=['POST'])
@login_required
def reorder_sections():
    """Обновить порядок разделов в боковом меню (в пределах одного parent).
    Ожидает JSON:
      - parent: endpoint родителя или null/'' для корня
      - ordered_endpoints: массив endpoint'ов в нужном порядке
    Сохраняет порядок в form_data.order (1..N).
    """
    try:
        data = request.get_json() or {}
        parent = data.get('parent')
        ordered_endpoints = data.get('ordered_endpoints')

        if isinstance(parent, str):
            parent = parent.strip()
            if parent.startswith('/sidebar/'):
                parent = parent.replace('/sidebar/', '')
            if parent == '':
                parent = None
        elif parent is None:
            parent = None
        else:
            parent = None

        if not isinstance(ordered_endpoints, list) or not ordered_endpoints:
            return jsonify({'success': False, 'error': 'ordered_endpoints должен быть непустым списком'}), 400

        cleaned = []
        for ep in ordered_endpoints:
            if isinstance(ep, str):
                e = ep.strip()
                if e and e not in cleaned:
                    cleaned.append(e)

        if not cleaned:
            return jsonify({'success': False, 'error': 'ordered_endpoints пуст'}), 400

        sections = InfoSection.query.filter(InfoSection.endpoint.in_(cleaned)).all()
        by_ep = {s.endpoint: s for s in sections if s and s.endpoint}

        for idx, ep in enumerate(cleaned):
            section = by_ep.get(ep)
            if not section:
                continue
            try:
                td = json.loads(section.text) if section.text else {}
            except Exception:
                td = {}
            if not isinstance(td, dict):
                td = {}
            fd = td.get('form_data', {})
            if not isinstance(fd, dict):
                fd = {}

            if fd.get('parent') is None and parent is not None:
                fd['parent'] = parent

            fd['order'] = idx + 1
            td['form_data'] = fd
            if 'text' not in td:
                td['text'] = ''
            section.text = json.dumps(td, ensure_ascii=False)

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500

@sidebar_bp.route('/section/<section_endpoint>')
def get_section_data(section_endpoint):
    """Получить данные раздела в JSON формате"""
    section = InfoSection.query.filter_by(endpoint=section_endpoint).first()
    
    if not section:
        # Если раздела нет, возвращаем пустые данные для нового раздела
        return jsonify({
            'success': True,
            'section': {
                'id': None,
                'endpoint': section_endpoint,
                'title': section_endpoint.replace('-', ' ').title(),
                'text': json.dumps({'text': '', 'form_data': {}}),
                'content_blocks': [],
                'form_data': {}
            }
        })
    
    form_data = {}
    try:
        if section.text:
            text_data = json.loads(section.text)
            if isinstance(text_data, dict) and 'form_data' in text_data:
                form_data = text_data['form_data']
    except Exception as e:
        pass
    
    # Рекурсивная функция для нормализации блоков
    def normalize_blocks_recursive(blocks_list):
        normalized_blocks = []
        for block in blocks_list:
            if isinstance(block, dict):
                # Проверяем, есть ли внутри блока content_blocks
                if 'content_blocks' in block and isinstance(block['content_blocks'], list):
                    # Если есть, добавляем только вложенные блоки, сам блок не добавляем
                    normalized_blocks.extend(normalize_blocks_recursive(block['content_blocks']))
                else:
                    # Убираем вложенные content_blocks из блока
                    normalized_block = {k: v for k, v in block.items() if k != 'content_blocks'}
                    normalized_blocks.append(normalized_block)
            elif isinstance(block, list):
                # Если блок - это массив, рекурсивно обрабатываем его
                normalized_blocks.extend(normalize_blocks_recursive(block))
            else:
                normalized_blocks.append(block)
        return normalized_blocks
    
    # Нормализуем блоки при загрузке из базы данных
    content_blocks = section.get_content_blocks()
    if isinstance(content_blocks, list):
        content_blocks = normalize_blocks_recursive(content_blocks)

    # Чистим блоки от ссылок на отсутствующие файлы (для стабильного UI в мастере)
    try:
        content_blocks, removed = _clean_sidebar_content_blocks_files(content_blocks)
        if removed > 0:
            section.set_content_blocks(content_blocks)
            db.session.commit()
    except Exception:
        pass

    # Чистим form_data от битых ссылок (в т.ч. images/documents)
    try:
        removed_fd = _clean_sidebar_form_data_files(section)
        if removed_fd > 0:
            db.session.commit()
    except Exception:
        pass
    
    return jsonify({
        'success': True,
        'section': {
            'id': section.id,
            'endpoint': section.endpoint,
            'title': section.title,
            'text': section.text,
            'content_blocks': content_blocks,
            'form_data': form_data
        }
    })

@sidebar_bp.route('/wizard_save', methods=['POST'])
@login_required
def wizard_save():
    """Сохранение данных мастера заполнения для sidebar разделов"""
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
                # Обновляем существующий раздел
                section.title = section_data.get('title', section.title)
                
                form_data = {}
                excluded_keys = ['title', 'text', 'content_blocks']
                
                for key, value in section_data.items():
                    if key not in excluded_keys:
                        # Очищаем поле content от HTML-тегов и JSON-строк
                        if key == 'content' and isinstance(value, str):
                            # Удаляем HTML-теги из поля content
                            value = re.sub(r'<[^>]+>', '', value)
                            # Удаляем JSON-строки, если они есть
                            if value.strip().startswith('{') and value.strip().endswith('}'):
                                try:
                                    json_data = json.loads(value)
                                    # Если это JSON, извлекаем только текстовое содержимое
                                    if isinstance(json_data, dict):
                                        value = json_data.get('text', '') or json_data.get('content', '') or ''
                                    else:
                                        value = ''
                                except:
                                    pass
                        form_data[key] = value
                
                existing_text_data = {}
                if section.text:
                    try:
                        existing_text_data = json.loads(section.text)
                    except:
                        existing_text_data = {}
                existing_form_data = existing_text_data.get('form_data', {}) if isinstance(existing_text_data, dict) else {}
                
                # Для "nutrition-dishes-archive" не тащим весь старый form_data (это мешало чистить контент),
                # но критичные служебные поля меню (parent/order/show_in_menu) сохраняем всегда.
                if section_id != 'nutrition-dishes-archive':
                    for k, v in existing_form_data.items():
                        if k not in form_data:
                            form_data[k] = v
                else:
                    for k in ('parent', 'menu_parent', 'order', 'show_in_menu'):
                        if k not in form_data and k in existing_form_data:
                            form_data[k] = existing_form_data.get(k)

                try:
                    # Простая и надежная версия без сложного маппинга ключей:
                    # склеиваем все block_*_photos/documents в images/documents если они пустые.
                    if not (isinstance(form_data.get('images'), str) and form_data.get('images', '').strip()):
                        photo_values = []
                        for k, v in form_data.items():
                            if isinstance(k, str) and re.match(r'^block_\\d+_photos$', k) and isinstance(v, str) and v.strip():
                                photo_values.append(v.strip())
                        if photo_values:
                            form_data['images'] = ', '.join(photo_values)

                    if not (isinstance(form_data.get('documents'), str) and form_data.get('documents', '').strip()):
                        doc_values = []
                        for k, v in form_data.items():
                            if isinstance(k, str) and re.match(r'^block_\\d+_documents$', k) and isinstance(v, str) and v.strip():
                                doc_values.append(v.strip())
                        if doc_values:
                            form_data['documents'] = ', '.join(doc_values)
                except Exception:
                    pass
                
                text_data = {
                    # Для "nutrition-dishes-archive" всегда берем text из запроса (обычно пустой),
                    # чтобы можно было очищать значение и не дублировать контент.
                    'text': (section_data.get('text', '') if section_id == 'nutrition-dishes-archive'
                             else existing_text_data.get('text', section_data.get('text', ''))),
                    'form_data': form_data
                }
                
                section.text = json.dumps(text_data, ensure_ascii=False)
                
                if 'content_blocks' in section_data:
                    # Рекурсивная функция для нормализации блоков
                    def normalize_blocks_recursive(blocks_list):
                        normalized_blocks = []
                        for block in blocks_list:
                            if isinstance(block, dict):
                                # Проверяем, есть ли внутри блока content_blocks
                                if 'content_blocks' in block and isinstance(block['content_blocks'], list):
                                    # Если есть, добавляем только вложенные блоки, сам блок не добавляем
                                    normalized_blocks.extend(normalize_blocks_recursive(block['content_blocks']))
                                else:
                                    # Убираем вложенные content_blocks из блока
                                    normalized_block = {k: v for k, v in block.items() if k != 'content_blocks'}
                                    normalized_blocks.append(normalized_block)
                            elif isinstance(block, list):
                                # Если блок - это массив, рекурсивно обрабатываем его
                                normalized_blocks.extend(normalize_blocks_recursive(block))
                            else:
                                normalized_blocks.append(block)
                        return normalized_blocks
                    
                    # Нормализуем структуру блоков - убираем вложенные блоки
                    content_blocks = section_data['content_blocks']
                    if isinstance(content_blocks, list):
                        content_blocks = normalize_blocks_recursive(content_blocks)
                    
                    # ВАЖНО: ранее для "nutrition-dishes-archive" была логика с merge, которая мешала
                    # удалять блоки (при пустом списке блоков возвращались существующие).
                    # Сейчас считаем, что content_blocks в запросе — источник истины (после normalize).
                    
                    # Если это раздел "food" (питание) и есть блоки типа "daily-dish", копируем их в "nutrition-dishes-archive"
                    if section_id == 'food' or section_id == 'nutrition':
                        archive_section = InfoSection.query.filter_by(endpoint='nutrition-dishes-archive').first()
                        if archive_section:
                            archive_blocks = archive_section.get_content_blocks() or []
                            
                            # Ищем или создаем блок "dishes" с названием "Ежедневное меню" в архиве
                            dishes_block = None
                            for archive_block in archive_blocks:
                                if isinstance(archive_block, dict) and archive_block.get('type') == 'dishes' and archive_block.get('title') == 'Ежедневное меню':
                                    dishes_block = archive_block
                                    break
                            
                            if not dishes_block:
                                dishes_block = {
                                    'type': 'dishes',
                                    'title': 'Ежедневное меню',
                                    'dishes': []
                                }
                                archive_blocks.append(dishes_block)
                            
                            # Ищем блоки типа "daily-dish" в разделе питания
                            for block in content_blocks:
                                if isinstance(block, dict) and block.get('type') == 'daily-dish' and block.get('dish'):
                                    dish = block.get('dish')
                                    # Проверяем, нет ли уже такого блюда в архиве (по дате)
                                    dish_date = dish.get('date', '')
                                    existing_dish = None
                                    dishes_list = dishes_block.get('dishes', [])
                                    for existing_d in dishes_list:
                                        if existing_d.get('date') == dish_date:
                                            existing_dish = existing_d
                                            break
                                    
                                    # Если блюдо уже есть, обновляем его, иначе добавляем новое
                                    if existing_dish:
                                        existing_dish.update({
                                            'title': dish.get('title', ''),
                                            'publish_date': dish.get('publish_date', ''),
                                            'photo': dish.get('photo', '')
                                        })
                                    else:
                                        dishes_block['dishes'].append({
                                            'title': dish.get('title', ''),
                                            'date': dish_date,
                                            'publish_date': dish.get('publish_date', ''),
                                            'photo': dish.get('photo', '')
                                        })
                            
                            # Обновляем блок в архиве
                            archive_section.set_content_blocks(archive_blocks)
                            
                            # Примечание: Статический блок "Ежедневное меню" отображается автоматически
                            # в шаблоне templates/info/section.html и не редактируется через мастер
                    
                    section.set_content_blocks(content_blocks)
            else:
                # Создаем новый раздел
                form_data = {}
                excluded_keys = ['title', 'text', 'content_blocks']
                
                for key, value in section_data.items():
                    if key not in excluded_keys:
                        # Очищаем поле content от HTML-тегов и JSON-строк
                        if key == 'content' and isinstance(value, str):
                            # Удаляем HTML-теги из поля content
                            value = re.sub(r'<[^>]+>', '', value)
                            # Удаляем JSON-строки, если они есть
                            if value.strip().startswith('{') and value.strip().endswith('}'):
                                try:
                                    json_data = json.loads(value)
                                    # Если это JSON, извлекаем только текстовое содержимое
                                    if isinstance(json_data, dict):
                                        value = json_data.get('text', '') or json_data.get('content', '') or ''
                                    else:
                                        value = ''
                                except:
                                    pass
                        form_data[key] = value
                
                text_data = {
                    'text': section_data.get('text', ''),
                    'form_data': form_data
                }
                
                section = InfoSection(
                    endpoint=section_id,
                    title=section_data.get('title', ''),
                    text=json.dumps(text_data, ensure_ascii=False),
                    url=f'/sidebar/{section_id}'
                )
                
                # Рекурсивная функция для нормализации блоков
                def normalize_blocks_recursive(blocks_list):
                    normalized_blocks = []
                    for block in blocks_list:
                        if isinstance(block, dict):
                            # Проверяем, есть ли внутри блока content_blocks
                            if 'content_blocks' in block and isinstance(block['content_blocks'], list):
                                # Если есть, добавляем только вложенные блоки, сам блок не добавляем
                                normalized_blocks.extend(normalize_blocks_recursive(block['content_blocks']))
                            else:
                                # Убираем вложенные content_blocks из блока
                                normalized_block = {k: v for k, v in block.items() if k != 'content_blocks'}
                                normalized_blocks.append(normalized_block)
                        elif isinstance(block, list):
                            # Если блок - это массив, рекурсивно обрабатываем его
                            normalized_blocks.extend(normalize_blocks_recursive(block))
                        else:
                            normalized_blocks.append(block)
                    return normalized_blocks
                
                # Нормализуем структуру блоков - убираем вложенные блоки
                content_blocks = section_data.get('content_blocks', [])
                if isinstance(content_blocks, list):
                    content_blocks = normalize_blocks_recursive(content_blocks)
                section.set_content_blocks(content_blocks)
                db.session.add(section)
        
        db.session.commit()
        
        message = 'Шаг успешно сохранен' if save_single else 'Все данные успешно сохранены'
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@sidebar_bp.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    """Загрузка файла на сервер с сохранением в базе данных"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не найден'})
        
        file = request.files['file']
        section = request.form.get('section', 'general')
        field_name = request.form.get('field_name')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        section_obj = InfoSection.query.filter_by(endpoint=section).first()
        if not section_obj:
            # Создаем раздел, если его нет
            section_obj = InfoSection(
                endpoint=section,
                title=section,
                text=json.dumps({'form_data': {}}),
                url=f'/sidebar/{section}'
            )
            db.session.add(section_obj)
            db.session.commit()
        
        file_info = file_manager.save_info_file(file, section, field_name)
        
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
                # Если в БД нет колонок file_data/stored_in_db – просто пропускаем сохранение в БД
                if 'no such column' in str(e).lower() or 'file_data' in str(e).lower():
                    logger.warning(
                        "Поля file_data/stored_in_db еще не добавлены в БД. "
                        "Пропускаю сохранение файла в InfoFile. Имя будет взято из запроса."
                    )
                    db_file = None
                    if db.session.is_active:
                        db.session.rollback()
                else:
                    logger.error(f"Ошибка при сохранении файла в InfoFile: {e}")
                    db_file = None
                    if db.session.is_active:
                        db.session.rollback()
            
            try:
                if section_obj.text:
                    data = json.loads(section_obj.text)
                else:
                    data = {'form_data': {}}
                
                if field_name:
                    # Для множественных полей (images/documents) — добавляем в список, а не перезаписываем,
                    # чтобы при загрузке нескольких файлов они все сохранялись.
                    try:
                        multi_fields = {'images', 'documents'}
                        url_value = file_info['url']
                        display_name = file_info.get('original_name') or file_info.get('filename')
                        new_entry = f"{url_value}|{display_name}" if display_name else url_value

                        if field_name in multi_fields:
                            existing_value = data['form_data'].get(field_name) or ''
                            existing_items = [x.strip() for x in str(existing_value).split(',') if x.strip()]

                            def entry_key(item: str) -> str:
                                item_clean = item.split('|')[0].strip() if '|' in item else item.strip()
                                return item_clean.split('/')[-1].strip().lower()

                            seen = {entry_key(x) for x in existing_items}
                            if entry_key(new_entry) not in seen:
                                existing_items.append(new_entry)

                            data['form_data'][field_name] = ', '.join(existing_items)
                        else:
                            # Одиночные поля — перезаписываем как раньше
                            data['form_data'][field_name] = new_entry
                    except Exception:
                        data['form_data'][field_name] = file_info['url']
                else:
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
                # Ошибка при обновлении данных раздела
                logger.warning(f"Ошибка при обновлении данных раздела: {e}")
            
            # Определяем правильный URL для sidebar разделов
            download_url = file_info['url']
            try:
                # Проверяем, является ли раздел sidebar разделом
                if section_obj.url and section_obj.url.startswith('/sidebar/'):
                    # Если URL еще не правильный, исправляем его
                    if not download_url.startswith('/sidebar/download_file/'):
                        download_url = f'/sidebar/download_file/{section}/{file_info["filename"]}'
            except Exception:
                pass
            
            return jsonify({
                'success': True,
                'filename': file_info['filename'],
                'original_name': file_info['original_name'],
                'original_filename': file_info.get('original_name') or file_info.get('original_filename') or file_info['filename'],
                'url': download_url,
                'is_image': file_info['is_image'],
                'size': file_info['size'],
                'mime_type': file_info['mime_type'],
                'id': db_file.id if db_file else None
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка при сохранении файла'})
            
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка при загрузке файла: {str(e)}'})

@sidebar_bp.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    """Удаление файла с сервера и из базы данных"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        section = data.get('section')
        field_name = data.get('field_name')
        
        if not all([filename, section]):
            return jsonify({'success': False, 'error': 'Недостаточно данных для удаления'})
        
        success = file_manager.delete_file(filename, section, field_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Файл удален'})
        else:
            return jsonify({'success': True, 'message': 'Файл не найден (возможно, уже удален)'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@sidebar_bp.route('/delete_subsection', methods=['POST'])
@login_required
def delete_subsection():
    """Удаление раздела или подраздела"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return jsonify({'success': False, 'error': 'Не указан endpoint раздела'})
        
        # Список статических разделов, которые нельзя удалить
        # Статическими являются только разделы до "food" включительно + "nutrition-dishes-archive"
        # Все разделы после "food" можно удалять
        static_sections = [
            'nutrition-dishes-archive',  # Статический подраздел питания
            'appeals', 'anti-corruption', 'nutrition', 'food'  # Разделы до питания включительно
        ]
        
        # Проверяем, что это не статический раздел
        if endpoint in static_sections:
            return jsonify({'success': False, 'error': f'Нельзя удалить статический раздел "{endpoint}"'})
        
        section = InfoSection.query.filter_by(endpoint=endpoint).first()
        if not section:
            return jsonify({'success': False, 'error': 'Раздел не найден'})
        
        # Проверяем, есть ли дочерние элементы
        all_sections = InfoSection.query.all()
        children = []
        for s in all_sections:
            if s.id == section.id:
                continue
            try:
                if s.text:
                    text_data = json.loads(s.text)
                    form_data = text_data.get('form_data', {}) if isinstance(text_data, dict) else {}
                else:
                    form_data = {}
                
                parent_val = form_data.get('parent')
                if parent_val:
                    if parent_val.startswith('/sidebar/'):
                        parent_val = parent_val.replace('/sidebar/', '')
                    if parent_val == section.endpoint:
                        children.append(s)
            except Exception:
                continue
        
        if children:
            child_titles = [c.title for c in children[:3]]
            error_msg = f'Нельзя удалить раздел с дочерними элементами ({len(children)} шт.). Сначала удалите дочерние элементы: {", ".join(child_titles)}'
            if len(children) > 3:
                error_msg += '...'
            return jsonify({'success': False, 'error': error_msg})
        
        # Удаляем связанные файлы из базы данных
        try:
            from models.models import InfoFile
            section_files = InfoFile.query.filter_by(section_endpoint=endpoint).all()
            for info_file in section_files:
                try:
                    if os.path.exists(info_file.file_path):
                        os.remove(info_file.file_path)
                    db.session.delete(info_file)
                except Exception:
                    pass
        except Exception:
            pass
        
        # Удаляем раздел
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Раздел успешно удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Ошибка при удалении раздела: {str(e)}'})

@sidebar_bp.route('/get_section_files/<section_endpoint>')
@login_required
def get_section_files(section_endpoint):
    """Получить список файлов раздела (только существующие файлы)"""
    try:
        field_name = request.args.get('field_name')
        # Используем метод, который проверяет существование файлов и возвращает только существующие
        # ПРИМЕЧАНИЕ: Метод не удаляет записи из БД (read-only), несуществующие файлы просто не включаются в результат
        files = file_manager.get_section_files_from_db(section_endpoint, field_name)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении файлов раздела {section_endpoint}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@sidebar_bp.route('/download_file/<section>/<filename>')
@sidebar_bp.route('/sidebar/download_file/<section>/<filename>')
def download_file(section, filename):
    """Скачивание файла пользователем для sidebar разделов. Поддерживает файлы из БД и файловой системы"""
    try:
        from flask import send_file, abort
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
            if 'no such column' in str(e).lower() or 'file_data' in str(e):
                pass
            else:
                logger.error(f"Ошибка при поиске файла sidebar в БД: {e}")
        
        # Если файл найден в БД
        if info_file:
            download_filename = info_file.original_filename or info_file.display_name or filename
            
            # Проверяем наличие обоих атрибутов перед доступом
            # ВАЖНО: Проверяем file_data is not None, а не truthiness,
            # так как пустые файлы (b'') являются falsy, но валидны
            if (hasattr(info_file, 'stored_in_db') and hasattr(info_file, 'file_data') and 
                info_file.stored_in_db and info_file.file_data is not None):
                # Файл хранится в БД - используем данные из БД
                # Пустые файлы (0 байт) также валидны и должны быть отданы
                file_data = info_file.file_data
                mimetype = info_file.mime_type
            elif info_file.file_path and os.path.exists(info_file.file_path):
                file_path = info_file.file_path
                mimetype = info_file.mime_type
        
        # Если файл не найден в БД, ищем в файловой системе
        if not file_data and not file_path:
            uploads_root = os.path.join(file_manager.base_upload_path)
            uploads_info_root = os.path.join(uploads_root, 'info')
            # Ищем в структуре info/год/раздел/
            for root, dirs, files in os.walk(uploads_info_root):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    break
            
            # Если не найден, пробуем общий поиск
            if not file_path or not os.path.exists(file_path):
                for root, dirs, files in os.walk(uploads_root):
                    if filename in files:
                        file_path = os.path.join(root, filename)
                        if os.path.exists(file_path):
                            break
            
            # Если не найден, пробуем старую структуру
            if not file_path or not os.path.exists(file_path):
                file_path = os.path.join(uploads_root, section, filename)
                if not os.path.exists(file_path):
                    file_path = os.path.join(uploads_root, 'pages', section, filename)
        
        if not file_data and (not file_path or not os.path.exists(file_path)):
            flash('Файл не найден', 'error')
            return redirect(url_for('main.index'))
        
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
        
        encoded_filename = urllib.parse.quote(download_filename.encode('utf-8'))

        is_image = False
        try:
            is_image = bool(mimetype) and str(mimetype).lower().startswith('image/')
        except Exception:
            is_image = False
        
        if file_data:
            file_stream = BytesIO(file_data)
            response = send_file(
                file_stream,
                as_attachment=not is_image,
                download_name=download_filename,
                mimetype=mimetype
            )
        else:
            response = send_file(
                file_path,
                as_attachment=not is_image,
                download_name=download_filename,
                mimetype=mimetype
            )
        
        disposition = 'inline' if is_image else 'attachment'
        response.headers['Content-Disposition'] = f"{disposition}; filename*=UTF-8''{encoded_filename}"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла sidebar {filename}: {e}")
        flash('Ошибка при скачивании файла', 'error')
        return redirect(url_for('main.index'))

@sidebar_bp.route('/delete_dish', methods=['POST'])
@login_required
def delete_dish():
    """Удалить блюдо из архива ежедневного меню"""
    try:
        data = request.get_json()
        dish_date = data.get('dish_date')
        dish_title = data.get('dish_title')
        
        if not dish_date:
            return jsonify({'success': False, 'error': 'Не указана дата блюда'})
        
        archive_section = InfoSection.query.filter_by(endpoint='nutrition-dishes-archive').first()
        if not archive_section:
            return jsonify({'success': False, 'error': 'Раздел архива не найден'})
        
        archive_blocks = archive_section.get_content_blocks() or []
        
        # Ищем блок "dishes" с названием "Ежедневное меню"
        dishes_block = None
        for block in archive_blocks:
            if isinstance(block, dict) and block.get('type') == 'dishes' and block.get('title') == 'Ежедневное меню':
                dishes_block = block
                break
        
        if not dishes_block:
            return jsonify({'success': False, 'error': 'Блок блюд не найден'})
        
        dishes_list = dishes_block.get('dishes', [])
        original_count = len(dishes_list)
        
        # Удаляем блюдо по дате публикации (и по заголовку, если указан)
        dishes_block['dishes'] = [
            d for d in dishes_list 
            if not ((d.get('publish_date') == dish_date or d.get('date') == dish_date) and (not dish_title or d.get('title') == dish_title))
        ]
        
        if len(dishes_block['dishes']) == original_count:
            return jsonify({'success': False, 'error': 'Блюдо не найдено'})
        
        # Обновляем блок в архиве
        archive_section.set_content_blocks(archive_blocks)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Блюдо успешно удалено'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении блюда: {e}")
        return jsonify({'success': False, 'error': f'Ошибка при удалении блюда: {str(e)}'})

@sidebar_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_section():
    """Создать новый раздел бокового меню"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            title = (data.get('title') or '').strip()
            # endpoint всегда генерируем автоматически (ручной ввод отключен)
            endpoint = ''
            
            if not title:
                return jsonify({'success': False, 'error': 'Название раздела обязательно'})
            
            # Генерируем endpoint из названия (и гарантируем уникальность)
            import re
            import uuid
            slug = re.sub(r'[^\w\s-]', '', title.lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            if not slug:
                slug = f"section-{uuid.uuid4().hex[:8]}"

            endpoint = slug
            suffix = 2
            while InfoSection.query.filter_by(endpoint=endpoint).first():
                # section-title-2, section-title-3, ...; если slug очень длинный/пустой — fallback to uuid
                if len(slug) > 64:
                    slug = slug[:64].rstrip('-')
                endpoint = f"{slug}-{suffix}"
                suffix += 1
            
            # Создаем новый раздел
            text_data = {
                'text': data.get('content') or '',
                'form_data': {}
            }
            # Сохраняем родителя при создании подраздела
            parent_endpoint = (data.get('parent') or '').strip()
            if parent_endpoint:
                # Нормализуем parent (убираем /sidebar/ если есть, оставляем только endpoint)
                if parent_endpoint.startswith('/sidebar/'):
                    parent_endpoint = parent_endpoint.replace('/sidebar/', '')
                text_data['form_data']['parent'] = parent_endpoint
                # Создаем подраздел
            # else: создаем раздел
            
            section = InfoSection(
                endpoint=endpoint,
                title=title,
                text=json.dumps(text_data, ensure_ascii=False),
                url=f'/sidebar/{endpoint}'
            )
            
            section.set_content_blocks([])
            db.session.add(section)
            
            try:
                db.session.commit()
                # После commit обновляем объект для получения ID
                db.session.refresh(section)
                
                # Проверяем, что раздел действительно создан
                created_section = InfoSection.query.filter_by(endpoint=endpoint).first()
                
                if not created_section:
                    # Раздел не найден после создания
                    return jsonify({'success': False, 'error': 'Ошибка при создании раздела в базе данных'})
                
                # Раздел успешно создан
                
                return jsonify({
                    'success': True,
                    'message': 'Раздел успешно создан',
                    'section': {
                        'id': created_section.id,
                        'endpoint': created_section.endpoint,
                        'title': created_section.title,
                        'url': created_section.url
                    }
                })
            except Exception as commit_error:
                db.session.rollback()
                # Ошибка при commit
                return jsonify({'success': False, 'error': f'Ошибка при сохранении раздела в базу данных: {str(commit_error)}'})
            
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            # Ошибка при создании раздела
            return jsonify({'success': False, 'error': f'Ошибка при создании раздела: {error_msg}'})
    
    # Шаблон больше не нужен, так как создание происходит через API
    return jsonify({'success': False, 'error': 'Используйте POST запрос для создания раздела'})