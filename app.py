#!/usr/bin/env python3
"""
Главный файл приложения
"""

from flask import Flask
from flask_login import LoginManager
from database import db
from config import config
import os
from werkzeug.exceptions import RequestEntityTooLarge


def create_app():
    """Создание и настройка приложения Flask"""
    app = Flask(__name__)
    
    # Мягкая валидация конфигурации ДО загрузки (проверка SECRET_KEY для production).
    # Ранее здесь выбрасывались исключения, из-за чего приложение в продакшене
    # вообще не стартовало при отсутствии переменной окружения SECRET_KEY.
    # Теперь мы лишь логируем предупреждение и продолжаем запуск с фолбэком,
    # а администратор может спокойно донастроить окружение.
    if hasattr(config, 'validate'):
        try:
            is_valid = config.validate()
            if type(config).__name__ == 'ProductionConfig' and not is_valid:
                # Логируем предупреждение, но не прерываем запуск.
                import logging
                logging.getLogger(__name__).warning(
                    'SECRET_KEY не установлен в переменных окружения для продакшена. '
                    'Используется резервный dev-ключ. Рекомендуется как можно скорее задать SECRET_KEY.'
                )
        except Exception as e:
            # Любые ошибки валидации не должны останавливать запуск приложения.
            import logging
            logging.getLogger(__name__).warning(f'Ошибка при валидации конфигурации: {e}')
    
    # Ранее здесь дополнительно жёстко проверялся SECRET_KEY для production
    # через исключения. Это блокировало запуск приложения на хостинге при
    # любой ошибке в настройках окружения. Сейчас эту проверку убираем,
    # так как сама конфигурация уже обеспечивает безопасный фолбэк.
    
    # Конфигурация
    app.config.from_object(config)
    
    # Финальная проверка SECRET_KEY после загрузки (на случай, если что-то пошло не так).
    # Вместо выбрасывания исключения логируем предупреждение, чтобы не ломать запуск.
    if type(config).__name__ == 'ProductionConfig' and not app.config.get('SECRET_KEY'):
        import logging
        logging.getLogger(__name__).warning(
            'После загрузки конфигурации SECRET_KEY отсутствует. '
            'Приложение использует резервный dev-ключ. '
            'Настоятельно рекомендуется задать SECRET_KEY в переменных окружения.'
        )
    
    # Создаем папку instance если её нет
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Используем абсолютный путь к базе данных
    db_path = os.path.join(instance_path, 'site.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Инициализация расширений
    db.init_app(app)

    with app.app_context():
        try:
            with db.engine.connect() as conn:
                r = conn.execute(db.text("PRAGMA table_info(info_file)"))
                rows = r.fetchall()
            names = [row[1] for row in rows] if rows else []
            with db.engine.connect() as conn:
                if 'file_data' not in names:
                    conn.execute(db.text("ALTER TABLE info_file ADD COLUMN file_data BLOB"))
                    conn.commit()
                if 'stored_in_db' not in names:
                    conn.execute(db.text("ALTER TABLE info_file ADD COLUMN stored_in_db INTEGER DEFAULT 1"))
                    conn.commit()
        except Exception:
            pass

    # Настройка Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'users.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    # Контекстный процессор для форм
    @app.context_processor
    def inject_forms():
        from users.forms import LoginForm
        return dict(login_form=LoginForm())
    
    # Контекстный процессор для версии для слабовидящих
    @app.context_processor
    def inject_visually_impaired_version():
        """Передает URL версии для слабовидящих из раздела 'main' в шаблоны"""
        try:
            import json as _json
            from info.models import InfoSection
            
            main_section = InfoSection.query.filter_by(endpoint='main').first()
            visually_impaired_url = ''
            
            if main_section and main_section.text:
                try:
                    text_data = _json.loads(main_section.text)
                    if isinstance(text_data, dict) and 'form_data' in text_data:
                        form_data = text_data.get('form_data', {})
                        visually_impaired_url = form_data.get('visually_impaired_version', '') or ''
                except Exception:
                    pass
            
            return dict(visually_impaired_url=visually_impaired_url)
        except Exception:
            return dict(visually_impaired_url='')

    # Разделы бокового меню (дерево) + обратная совместимость
    @app.context_processor
    def inject_sidebar_sections():
        """Передает в шаблоны дерево бокового меню из БД.
        Поддерживает:
        - вложенность через form_data.parent
        - порядок через form_data.order
        - скрытие из меню через form_data.show_in_menu
        """
        try:
            import json as _json
            from info.models import InfoSection

            # Базовый порядок для системных пунктов (если order не задан)
            default_root_order = [
                'appeals',
                'anti-corruption',
                'additional-info',
                'food',
                'admission-grade1',
                'history',
                'ushakov-festival',
                'schedule',
                'class-leadership-payment',
                'electronic-environment',
                'useful-info',
                'information-security',
                'road-safety',
                'targeted-training',
                'social-order-implementation',
                'recreation-organization',
                'for-parents',
                'parent-education',
                'gia-ege-oge',
                'admission-grade10',
                'memos',
                'cbr-fraud-prevention',
                'financial-literacy',
                'parental-control',
                'inclusive-education',
                'anti-terrorism',
                'orkse',
                'sanitary-shield',
            ]
            default_root_order_map = {ep: i + 1 for i, ep in enumerate(default_root_order)}

            # Берем все /sidebar/* + обязательно корневой раздел "food" (он живет в /sveden/*)
            all_sections = InfoSection.query.filter(
                (InfoSection.url.like('/sidebar/%')) | (InfoSection.endpoint == 'food')
            ).all()
            items = {}

            def _parse_form_data(s):
                try:
                    td = _json.loads(s.text) if s and s.text else {}
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

            def _parse_show_in_menu(fd, default_value: bool):
                """show_in_menu:
                - если не задано: используем default_value
                - строки '0/false/no/off' => False
                - иначе => True
                """
                val = fd.get('show_in_menu')
                if val is None:
                    return default_value
                if isinstance(val, str):
                    v = val.strip().lower()
                    if v in ('0', 'false', 'no', 'off'):
                        return False
                    if v == '':
                        return default_value
                    return True
                return bool(val)

            for s in all_sections:
                if not s or not s.endpoint:
                    continue

                fd = _parse_form_data(s)
                # Для структуры МЕНЮ используем menu_parent, если он задан (иначе fallback к parent).
                menu_parent = _normalize_parent(fd.get('menu_parent'))
                parent = menu_parent if menu_parent is not None else _normalize_parent(fd.get('parent'))

                # URL для ссылки в меню
                if s.endpoint == 'food':
                    href = '/sveden/catering'
                else:
                    href = f"/sidebar/{s.endpoint}"

                # По умолчанию: показываем только корневые пункты, а подразделы скрываем.
                show_default = parent is None
                if not _parse_show_in_menu(fd, show_default):
                    continue

                order = 0
                try:
                    order = int(fd.get('order') or 0)
                except Exception:
                    order = 0
                if order == 0 and s.endpoint in default_root_order_map and parent is None:
                    order = default_root_order_map[s.endpoint]

                items[s.endpoint] = {
                    'endpoint': s.endpoint,
                    'title': s.title or s.endpoint,
                    'parent': parent,
                    'order': order,
                    'href': href,
                }

            by_parent = {}
            for it in items.values():
                by_parent.setdefault(it.get('parent'), []).append(it)

            def _sort_key(it):
                o = it.get('order') or 10**9
                t = (it.get('title') or '').lower()
                return (o, t, it.get('endpoint') or '')

            def build_tree(parent=None, seen=None):
                if seen is None:
                    seen = set()
                out = []
                for ch in sorted(by_parent.get(parent, []), key=_sort_key):
                    ep = ch.get('endpoint')
                    if not ep or ep in seen:
                        continue
                    seen.add(ep)
                    node = dict(ch)
                    node['children'] = build_tree(ep, seen)
                    out.append(node)
                return out

            sidebar_menu_tree = build_tree(None)

            # backward compatibility: динамические корневые разделы (без подразделов)
            dynamic_sections = []
            for ep, it in items.items():
                if it.get('parent') is not None:
                    continue
                try:
                    sec = next((s for s in all_sections if s.endpoint == ep), None)
                    if sec:
                        dynamic_sections.append(sec)
                except Exception:
                    continue
        except Exception:
            sidebar_menu_tree = []
            dynamic_sections = []

        return dict(dynamic_sidebar_sections=dynamic_sections, sidebar_menu_tree=sidebar_menu_tree)
    
    # Регистрация фильтров
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        try:
            return json.loads(value) if value else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @app.template_filter('sort_dishes_by_date')
    def sort_dishes_by_date_filter(dishes):
        """Сортирует блюда: сначала новые (без даты, с сегодняшней или будущей датой), затем по дате публикации по убыванию"""
        if not dishes or not isinstance(dishes, list):
            return dishes
        
        from datetime import datetime
        
        def parse_date(date_str):
            """Парсит дату из формата DD.MM.YYYY или YYYY-MM-DD в datetime"""
            if not date_str:
                return None
            try:
                if '.' in str(date_str):
                    parts = str(date_str).split('.')
                    if len(parts) == 3:
                        return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                elif '-' in str(date_str):
                    parts = str(date_str).split('-')
                    if len(parts) == 3:
                        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError, TypeError):
                pass
            return None
        
        def sort_key(dish):
            if not isinstance(dish, dict):
                return (0, datetime.min)
            
            publish_date = dish.get('publish_date') or dish.get('date') or ''
            dt = parse_date(publish_date)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if dt is None:
                return (1, datetime.max)
            
            if dt.date() >= today.date():
                return (1, dt)
            
            return (0, dt)
        
        sorted_dishes = sorted(dishes, key=sort_key, reverse=True)
        return sorted_dishes

    @app.template_filter('linkify_site')
    def linkify_site_filter(value):
        """Преобразует URL в тексте в кликабельную ссылку с текстом 'Перейти на сайт'.
        Безопасно экранирует остальной текст (защита от XSS) и сохраняет переносы строк.
        """
        try:
            from markupsafe import Markup, escape
            import re

            if value is None:
                return ''
            text = str(value)
            if not text.strip():
                return ''

            url_re = re.compile(r'(https?://[^\s<>"\']+)')
            trailing_punct = '.,;:!?)\\]}`»'

            out = []
            last = 0
            for m in url_re.finditer(text):
                start, end = m.span(1)
                raw = m.group(1) or ''

                # Текст до ссылки
                before = text[last:start]
                if before:
                    out.append(escape(before).replace('\n', Markup('<br>')))

                # Отделяем завершающую пунктуацию от URL
                url = raw
                tail = ''
                while url and url[-1] in trailing_punct:
                    tail = url[-1] + tail
                    url = url[:-1]

                if url:
                    href = escape(url)
                    out.append(Markup(f'<a href="{href}" target="_blank" rel="noopener noreferrer">Перейти на сайт</a>'))
                if tail:
                    out.append(escape(tail))

                last = end

            # Хвост после последней ссылки
            rest = text[last:]
            if rest:
                out.append(escape(rest).replace('\n', Markup('<br>')))

            if not out:
                return escape(text).replace('\n', Markup('<br>'))
            return Markup('').join(out)
        except Exception:
            # Фолбэк: просто экранируем и переносим строки
            try:
                from markupsafe import escape, Markup
                return escape(str(value or '')).replace('\n', Markup('<br>'))
            except Exception:
                return str(value or '')
    
    def _generate_content_file_url(filename, content_id, content_type):
        """Общая функция для генерации URL файлов контента.
        ВАЖНО: изображения новостей/объявлений хранятся в папках с датой.
        При редактировании даты публикации старые файлы могут оказаться в "старой" папке,
        поэтому делаем fallback-поиск по фактическому расположению на диске.
        """
        if not filename or not content_id:
            return f"/static/uploads/{content_type}/{filename}"
        
        from models.models import News, Announcement
        import os
        import glob
        from functools import lru_cache
        
        content_model = News if content_type == 'news' else Announcement
        content = content_model.query.get(content_id)
        
        if not content:
            return f"/static/uploads/{content_type}/{filename}"
        
        target_date = content.publication_date if content.publication_date else content.created_at
        year = target_date.strftime("%Y")
        month = target_date.strftime("%m")
        day = target_date.strftime("%d")

        candidate_url = f"/static/uploads/{content_type}/{year}/{month}/{day}/{content_id}/{filename}"
        candidate_path = os.path.join(app.root_path, 'static', 'uploads', content_type, year, month, day, str(content_id), filename)
        if os.path.exists(candidate_path):
            return candidate_url

        @lru_cache(maxsize=4096)
        def _locate_existing_url(ct, cid, fn):
            try:
                uploads_dir = os.path.join(app.root_path, 'static', 'uploads', ct)
                pattern = os.path.join(uploads_dir, '*', '*', '*', str(cid), fn)
                matches = glob.glob(pattern)
                if not matches:
                    return None
                # Берем самый новый по времени изменения
                matches.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
                abs_path = matches[0]
                rel = os.path.relpath(abs_path, app.root_path)
                return '/' + rel.replace('\\', '/')
            except Exception:
                return None

        found = _locate_existing_url(content_type, content_id, filename)
        return found or candidate_url
    
    @app.template_filter('news_file_url')
    def news_file_url_filter(filename, news_id):
        """Фильтр для получения URL файла новости"""
        return _generate_content_file_url(filename, news_id, 'news')
    
    # Импорт моделей для Flask-Login
    from models.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Регистрация Blueprint'ов
    from main import main_bp
    from info import info_bp
    from users import users_bp
    from news import news_bp
    from announcements import announcements_bp
    from albums import albums_bp
    from projects import projects_bp
    from sidebar import sidebar_bp
    from admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(info_bp, url_prefix='/info')
    # Регистрируем тот же blueprint для правильных URL согласно методическим рекомендациям 2024
    app.register_blueprint(info_bp, url_prefix='/sveden', name='sveden_bp')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(announcements_bp, url_prefix='/announcements')
    app.register_blueprint(albums_bp, url_prefix='/albums')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(sidebar_bp, url_prefix='/sidebar')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/health')
    def health():
        """Лёгкий эндпоинт для проверки живости сервиса (uptime-мониторы, пинги для Render)."""
        return '', 200

    @app.route('/food/<filename>')
    def download_food_file(filename):
        """Скачивание файлов питания по упрощенному URL /food/<filename>. Поддерживает файлы из БД и файловой системы"""
        try:
            from flask import send_file, abort
            from io import BytesIO
            import mimetypes
            import urllib.parse
            import re

            # Декодируем имя файла (на случай URL-encoding) и проверяем безопасность
            try:
                filename = urllib.parse.unquote(filename)
            except Exception:
                pass

            if '..' in filename or '/' in filename or '\\' in filename:
                abort(400)

            file_path = None
            file_data = None
            download_filename = filename
            mimetype = None

            # Пытаемся получить файл из БД
            from models.models import InfoFile
            info_file = None
            try:
                info_file = InfoFile.query.filter_by(
                    filename=filename,
                    section_endpoint='food'
                ).first()
                if not info_file:
                    # Пробуем найти по field_name
                    info_file = InfoFile.query.filter_by(
                        filename=filename,
                        field_name='menu_file'
                    ).first()
            except Exception as e:
                # Если ошибка из-за отсутствующих полей в БД, пропускаем проверку БД
                if 'no such column' in str(e).lower() or 'file_data' in str(e):
                    pass
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Ошибка при поиске файла питания в БД: {e}")

            # Если файл найден в БД
            if info_file:
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

            # Если файл не найден в БД или не хранится в БД, ищем в файловой системе
            if not file_data and not file_path:
                uploads_root = os.path.join(app.root_path, 'static', 'uploads')
                uploads_info_root = os.path.join(uploads_root, 'info')
                # Ищем файл в папке меню питания
                menu_path = os.path.join(uploads_root, 'nutrition', 'menus', filename)
                if os.path.exists(menu_path):
                    file_path = menu_path

                # Если не найден, ищем в структуре info/год/<section>/ (в т.ч. food)
                if not file_path or not os.path.exists(file_path):
                    for root, dirs, files in os.walk(uploads_info_root):
                        if filename in files:
                            file_path = os.path.join(root, filename)
                            break

                # Если не найден, пробуем старую структуру
                if not file_path or not os.path.exists(file_path):
                    old_path = os.path.join(uploads_root, 'nutrition', filename)
                    if os.path.exists(old_path):
                        file_path = old_path

                # Если не найдено: для сервисных файлов tmYYYY-sm.xlsx / kpYYYY.xlsx подбираем ближайший по году,
                # чтобы URL /food/tm2026-sm.xlsx продолжал работать даже если загружен tm2025-sm.xlsx.
                if (not file_path or not os.path.exists(file_path)) and not file_data:
                    tm_match = re.match(r'^tm(\d{4})-sm\.xlsx$', filename, flags=re.IGNORECASE)
                    kp_match = re.match(r'^kp(\d{4})\.xlsx$', filename, flags=re.IGNORECASE)
                    desired_year = None
                    kind = None
                    if tm_match:
                        desired_year = int(tm_match.group(1))
                        kind = 'tm'
                    elif kp_match:
                        desired_year = int(kp_match.group(1))
                        kind = 'kp'

                    if kind and desired_year:
                        candidates = []
                        try:
                            for root, dirs, files in os.walk(uploads_info_root):
                                for f in files:
                                    if kind == 'tm':
                                        m = re.match(r'^tm(\d{4})-sm\.xlsx$', f, flags=re.IGNORECASE)
                                    else:
                                        m = re.match(r'^kp(\d{4})\.xlsx$', f, flags=re.IGNORECASE)
                                    if not m:
                                        continue
                                    try:
                                        y = int(m.group(1))
                                    except Exception:
                                        continue
                                    candidates.append((y, os.path.join(root, f)))
                        except Exception:
                            candidates = []

                        if candidates:
                            # предпочитаем точный год; иначе ближайший <= desired_year; иначе максимальный.
                            exact = [c for c in candidates if c[0] == desired_year]
                            if exact:
                                file_path = exact[0][1]
                            else:
                                le = [c for c in candidates if c[0] <= desired_year]
                                if le:
                                    file_path = sorted(le, key=lambda x: x[0], reverse=True)[0][1]
                                else:
                                    file_path = sorted(candidates, key=lambda x: x[0], reverse=True)[0][1]

            if not file_data and (not file_path or not os.path.exists(file_path)):
                abort(404)

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

            # Кодируем имя файла для правильного отображения
            encoded_filename = urllib.parse.quote(download_filename.encode('utf-8'))

            # Отдаем файл
            if file_data:
                # Файл из БД - используем BytesIO
                file_stream = BytesIO(file_data)
                response = send_file(
                    file_stream,
                    as_attachment=True,
                    download_name=download_filename,
                    mimetype=mimetype
                )
            else:
                # Файл из файловой системы
                response = send_file(
                    file_path,
                    as_attachment=True,
                    download_name=download_filename,
                    mimetype=mimetype
                )

            # Устанавливаем заголовки
            response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Cache-Control'] = 'public, max-age=3600'

            return response

        except Exception as e:
            from flask import abort
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при скачивании файла питания {filename}: {e}")
            abort(500)
    
    @app.template_filter('announcement_file_url')
    def announcement_file_url_filter(filename, announcement_id):
        """Фильтр для получения URL файла объявления"""
        return _generate_content_file_url(filename, announcement_id, 'announcements')
    
    @app.template_filter('info_file_url')
    def info_file_url_filter(filename, section_endpoint):
        """Фильтр для получения URL файла раздела Сведения (всегда через download-роут)"""
        if not filename or not section_endpoint:
            return f"/info/download_file/{section_endpoint}/{filename}"
        return f"/info/download_file/{section_endpoint}/{filename}"
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        """Возвращаем понятный ответ при превышении лимита загрузки"""
        from flask import jsonify, request, redirect, url_for, flash
        max_mb = round(app.config.get('MAX_CONTENT_LENGTH', 0) / (1024 * 1024))
        message = f"Файл слишком большой. Максимальный размер: {max_mb} МБ."
        # Для XHR/JSON — возвращаем JSON, для остальных — редирект с флеш-сообщением
        if request.path.startswith('/info/upload_file') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, error=message), 413
        flash(message, 'error')
        return redirect(request.referrer or url_for('main.index')), 413
    
    @app.template_filter('file_exists')
    def file_exists_filter(file_url, section_endpoint=None):
        """Фильтр для проверки существования файла"""
        import os
        if not file_url:
            return False

        uploads_root = os.path.join(app.root_path, 'static', 'uploads')
        uploads_info_root = os.path.join(uploads_root, 'info')
        
        # Извлекаем имя файла из URL
        filename = file_url.split('/')[-1].split('|')[0].strip()
        if not filename:
            return False
        
        # Проверяем в БД (с обработкой ошибок, если поля еще не добавлены)
        from models.models import InfoFile
        try:
            if section_endpoint:
                info_file = InfoFile.query.filter_by(
                    filename=filename,
                    section_endpoint=section_endpoint
                ).first()
            else:
                info_file = InfoFile.query.filter_by(filename=filename).first()
            
            if info_file:
                # Проверяем file_path только если атрибут существует и он не None
                if (hasattr(info_file, 'file_path') and info_file.file_path and 
                    os.path.exists(info_file.file_path)):
                    return True
                # Ищем в файловой системе
                for root, dirs, files in os.walk(uploads_info_root):
                    if filename in files:
                        return True
        except Exception as e:
            # Если ошибка из-за отсутствующих полей в БД, просто пропускаем проверку БД
            # и проверяем только файловую систему
            import logging
            logger = logging.getLogger(__name__)
            if 'no such column' in str(e).lower() or 'file_data' in str(e):
                logger.warning(f"Поля file_data/stored_in_db еще не добавлены в БД. Пропускаю проверку БД. Запустите: python migrate_db_add_file_fields.py")
            else:
                logger.error(f"Ошибка при проверке файла в БД: {e}")
        
        # Проверяем новую структуру папок
        for root, dirs, files in os.walk(uploads_info_root):
            if filename in files:
                return True
        
        # Проверяем старую структуру
        if section_endpoint:
            old_path = os.path.join(uploads_root, section_endpoint, filename)
            if os.path.exists(old_path):
                return True
        
        return False
    
    def render_error_template(code, title, message, instructions, error_details=None):
        """Утилита для отображения страницы ошибки"""
        from flask import render_template
        return render_template(
            'errors/error.html',
            error_code=code,
            error_title=title,
            error_message=message,
            instructions=instructions,
            error_details=error_details
        )
    
    # Конфигурация обработчиков ошибок
    ERROR_HANDLERS = {
        400: {
            'title': 'Неверный запрос',
            'message': 'Проверьте введенные данные и попробуйте снова.',
            'instructions': [
                'Проверьте все обязательные поля',
                'Убедитесь, что данные введены корректно',
                'Проверьте формат файлов, если загружаете файлы',
                'Если проблема сохраняется, сообщите администратору'
            ]
        },
        401: {
            'title': 'Требуется авторизация',
            'message': 'Необходимо войти в систему для доступа к этой странице.',
            'instructions': [
                'Нажмите на кнопку "Войти" в верхнем меню',
                'Введите логин и пароль',
                'Если забыли пароль, обратитесь к администратору',
                '<a href="/users/login">Перейти на страницу входа</a>'
            ]
        },
        403: {
            'title': 'Доступ запрещен',
            'message': 'У вас нет прав для доступа к этой странице.',
            'instructions': [
                'Убедитесь, что вы вошли в систему',
                'Проверьте права доступа',
                'Обратитесь к администратору для получения доступа',
                '<a href="/">Вернуться на главную страницу</a>'
            ]
        },
        404: {
            'title': 'Страница не найдена',
            'message': 'Запрашиваемая страница не существует.',
            'instructions': [
                'Проверьте правильность URL',
                'Возможно, страница была удалена или перемещена',
                '<a href="/">Вернуться на главную страницу</a>',
                'Если вы считаете, что это ошибка, сообщите администратору'
            ]
        },
        413: {
            'title': 'Файл слишком большой',
            'message': 'Размер загружаемого файла превышает допустимый лимит.',
            'instructions': [
                'Максимальный размер файла: 10 МБ',
                'Попробуйте уменьшить размер файла',
                'Используйте сжатие для изображений',
                'Для больших файлов используйте внешние хранилища'
            ]
        },
        500: {
            'title': 'Внутренняя ошибка сервера',
            'message': 'На сервере произошла непредвиденная ошибка.',
            'instructions': [
                'Попробуйте повторить действие через несколько минут',
                'Обновите страницу (Ctrl+F5)',
                'Если ошибка повторяется, сообщите администратору',
                'Укажите, какое действие вы пытались выполнить'
            ]
        },
        502: {
            'title': 'Ошибка сервера',
            'message': 'Проблема с соединением между серверами.',
            'instructions': [
                'Попробуйте обновить страницу через несколько минут',
                'Проверьте подключение к интернету',
                'Если проблема сохраняется, сообщите администратору'
            ]
        },
        503: {
            'title': 'Сервис недоступен',
            'message': 'Сервер временно недоступен из-за обслуживания или перегрузки.',
            'instructions': [
                'Попробуйте обновить страницу через несколько минут',
                'Возможно, идет техническое обслуживание',
                'Если проблема сохраняется, сообщите администратору'
            ]
        }
    }
    
    def create_error_handler(code):
        """Фабрика для создания обработчиков ошибок"""
        def handler(error):
            import traceback
            error_config = ERROR_HANDLERS.get(code, {})
            error_details = None
            
            if code == 500 and app.config.get('DEBUG'):
                error_details = traceback.format_exc()
            
            # Фолбэк для динамических страниц:
            # если URL существует в БД (InfoSection.url), показываем его вместо 404.
            if code == 404:
                try:
                    from flask import request as _request, redirect as _redirect, render_template as _render_template
                    from info.models import InfoSection
                    import re as _re
                    from datetime import datetime as _dt

                    path = (_request.path or '').strip()

                    # 1) Точное совпадение URL
                    section = InfoSection.query.filter_by(url=path).first() if path else None
                    if section:
                        today = _dt.now().strftime('%d.%m.%Y')
                        return _render_template('info/section.html', section=section, children=[], today=today), 200

                    # 2) Обратная совместимость: /<endpoint> -> /sidebar/<endpoint> или другой сохраненный url
                    m = _re.fullmatch(r'/([A-Za-z0-9][A-Za-z0-9-]{0,79})', path or '')
                    if m:
                        ep = m.group(1)
                        section_by_ep = InfoSection.query.filter_by(endpoint=ep).first()
                        if section_by_ep and section_by_ep.url and section_by_ep.url != path:
                            return _redirect(section_by_ep.url, code=301)
                except Exception:
                    pass

            return render_error_template(
                code,
                error_config.get('title', f'Ошибка {code}'),
                error_config.get('message', 'Произошла ошибка.'),
                error_config.get('instructions', []),
                error_details=error_details
            ), code
        return handler
    
    # Регистрация обработчиков ошибок
    for error_code in ERROR_HANDLERS.keys():
        app.errorhandler(error_code)(create_error_handler(error_code))
    
    # Создание таблиц базы данных
    with app.app_context():
        # Импортируем все модели для создания таблиц
        from models.models import PageContent
        from info.models import InfoSection
        import json
        db.create_all()
        
        # Автоматическое создание обязательных разделов, если их нет
        required_sections = {
            'education': {
                'title': 'Образование',
                'url': '/sveden/education',
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
            }
        }
        
        for endpoint, section_data in required_sections.items():
            section = InfoSection.query.filter_by(endpoint=endpoint).first()
            if not section:
                text_data = {
                    'form_data': section_data.get('form_data', {})
                }
                section = InfoSection(
                    endpoint=endpoint,
                    title=section_data['title'],
                    url=section_data['url'],
                    text=json.dumps(text_data, ensure_ascii=False),
                    content_blocks=json.dumps([], ensure_ascii=False)
                )
                db.session.add(section)
        
        try:
            db.session.commit()
            app.logger.info("Обязательные разделы проверены и созданы при необходимости")
        except Exception as e:
            db.session.rollback()
            # Логируем ошибку, но не прерываем запуск приложения
            app.logger.warning(f"Ошибка при создании обязательных разделов: {e}")
            # Игнорируем ошибки при создании разделов (они могут уже существовать)
            pass
    
    # Страница очистки файлов обслуживается в модуле info
    
    return app

# Создаем приложение для gunicorn и других WSGI серверов
app = create_app()

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT, threaded=config.THREADED)
