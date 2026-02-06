from flask import render_template, request, redirect, url_for, flash, jsonify, abort, make_response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import main_bp
from models.models import News, Announcement, PageContent
from database import db
from datetime import datetime
from sqlalchemy import func, desc
import json
import re
import os
import uuid


def _slugify_segment(segment: str) -> str:
    """Простой slugify для URL/endpoint: латиница+цифры+дефис. Остальное выкидываем.
    Используется только для служебных идентификаторов, не для пользовательского текста.
    """
    if not isinstance(segment, str):
        return ''
    s = segment.strip().lower()
    # заменяем все не [a-z0-9-] на дефис
    s = re.sub(r'[^a-z0-9-]+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s


def _normalize_page_slug(slug: str) -> str:
    """Нормализует path slug для URL: позволяет вложенность через '/'."""
    if not isinstance(slug, str):
        return ''
    parts = [p for p in (slug or '').split('/') if p and p.strip()]
    out = []
    for p in parts:
        sp = _slugify_segment(p)
        if sp:
            out.append(sp)
    return '/'.join(out)


def _make_unique_info_endpoint(base_endpoint: str) -> str:
    """Гарантирует уникальный endpoint для InfoSection (<= 100 символов)."""
    base_endpoint = (base_endpoint or '').strip()
    if not base_endpoint:
        return ''
    base_endpoint = base_endpoint[:100]
    # Ленивый импорт, чтобы не создавать циклы импорта при старте
    from info.models import InfoSection
    if not InfoSection.query.filter_by(endpoint=base_endpoint).first():
        return base_endpoint
    suffix = 2
    while suffix < 1000:
        cand = f"{base_endpoint[:95]}-{suffix}"
        if not InfoSection.query.filter_by(endpoint=cand).first():
            return cand
        suffix += 1
    return ''

@main_bp.route('/')
def index():
    now = datetime.utcnow()
    news_dt = func.coalesce(News.publication_date, News.created_at)
    ann_dt = func.coalesce(Announcement.publication_date, Announcement.created_at)
    news = (News.query
                .filter(News.is_published.is_(True))
                .filter(news_dt <= now)
                .order_by(desc(News.is_featured), desc(news_dt))
                .limit(12)
                .all())
    announcements = (Announcement.query
                        .filter(Announcement.is_published.is_(True))
                        .filter(ann_dt <= now)
                        .order_by(desc(Announcement.is_featured), desc(ann_dt))
                        .limit(3)
                        .all())
    
    # Получаем редактируемый контент главной страницы
    default_block_order = ['header', 'slider', 'announcements', 'news', 'school_info', 'directions', 'events_achievements']
    page_content = PageContent.get_or_create('index', {
        'block_order': default_block_order,
        'slider_images': [],
        'header_title': 'МБОУ "ИТ Гимназия "Юнона"',
        'header_subtitle': 'при ВИТИ НИЯУ МИФИ г. Волгодонска',
        'header_tags': ['🚀 Инновационное образование', '💻 IT-технологии', '🔬 Научные исследования'],
        'achievements': [
            'Победители и призёры олимпиад',
            'Участники всероссийских конкурсов',
            'Высокие результаты ЕГЭ и ОГЭ'
        ],
        'it_infrastructure': [
            'Собственная IT-лаборатория',
            'Современный медиацентр',
            'Цифровые образовательные ресурсы'
        ],
        'teachers': [
            'Профессиональный коллектив',
            'Высшая квалификационная категория',
            'Постоянное повышение квалификации'
        ],
        'partnership': [
            'ВИТИ НИЯУ МИФИ',
            'Ведущие IT-компании',
            'Научно-исследовательские центры'
        ],
        'directions': [
            {'title': 'IT-Направление', 'desc': 'Программирование, веб-разработка, кибербезопасность, искусственный интеллект'},
            {'title': 'Естественные науки', 'desc': 'Физика, химия, биология, математика с углублённым изучением'},
            {'title': 'Гуманитарные науки', 'desc': 'Русский язык, литература, история, обществознание'},
            {'title': 'Творческое развитие', 'desc': 'Искусство, музыка, театр, медиа-творчество'}
        ],
        'events': [
            {'date': 'Сентябрь 2024', 'text': 'Начало нового учебного года'},
            {'date': 'Октябрь 2024', 'text': 'IT-конференция для учащихся'},
            {'date': 'Ноябрь 2024', 'text': 'Научно-практическая конференция'},
            {'date': 'Декабрь 2024', 'text': 'Новогодний IT-фестиваль'}
        ],
        'achievements_list': [
            '🥇 1 место в региональной олимпиаде по программированию',
            '🥈 2 место в конкурсе "IT-проект года"',
            '🥉 3 место в научно-технической конференции',
            '⭐ Сертификация по кибербезопасности'
        ],
        'partners': [
            'ВИТИ НИЯУ МИФИ',
            'IT-компании региона',
            'Научные центры'
        ]
    })
    
    content_data = page_content.get_content()
    if 'header_tags' not in content_data and content_data.get('header_tagline'):
        content_data['header_tags'] = [t.strip() for t in content_data['header_tagline'].split('•') if t.strip()]
    block_order = content_data.get('block_order', default_block_order)
    if isinstance(block_order, list) and 'slider' not in block_order:
        if 'header' in block_order:
            idx = block_order.index('header') + 1
            block_order = block_order[:idx] + ['slider'] + block_order[idx:]
        else:
            block_order = ['slider'] + block_order
        content_data['block_order'] = block_order
    return render_template('main/index.html', news=news, announcements=announcements, page_content=content_data)


ALLOWED_SLIDER_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def _allowed_slider_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_SLIDER_EXTENSIONS


@main_bp.route('/edit/index/slider-upload', methods=['POST'])
@login_required
def slider_upload():
    """Загрузка изображений для слайдера главной страницы."""
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Нет файлов'}), 400
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'main', 'slider')
    os.makedirs(upload_dir, exist_ok=True)
    urls = []
    files = request.files.getlist('files') if request.files.getlist('files') else [request.files.get('file')]
    for f in files:
        if not f or not f.filename:
            continue
        if not _allowed_slider_file(f.filename):
            continue
        ext = f.filename.rsplit('.', 1)[1].lower()
        name = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(upload_dir, name)
        try:
            f.save(path)
            urls.append(f"/static/uploads/main/slider/{name}")
        except Exception:
            continue
    return jsonify({'success': True, 'urls': urls})


@main_bp.route('/contacts')
def contacts():
    page_content = PageContent.get_or_create('contacts', {
        'address': '347389, Ростовская обл, Волгодонск, ул. К.Маркса, 64А',
        'phone': '8 (8639) 27-97-76',
        'email': 'junona@rostovschool.ru',
        'work_hours': 'Пн-Пт 8:00–17:00'
    })
    content_data = page_content.get_content()
    return render_template('main/contacts.html', page_content=content_data)

@main_bp.route('/search')
def search():
    return render_template('main/search.html')

@main_bp.route('/sitemap')
def sitemap():
    return render_template('main/sitemap.html')

@main_bp.route('/info')
def info():
    page_content = PageContent.get_or_create('info', {
        'parent_links': [
            {'text': 'Расписание занятий', 'url': '/schedule'},
            {'text': 'Электронный дневник', 'url': 'https://dnevnik.ru'},
            {'text': 'Питание в школе', 'url': '/sveden/catering'}
        ],
        'student_links': [
            {'text': 'Кружки и секции', 'url': '/clubs'},
            {'text': 'Олимпиады и конкурсы', 'url': '/olympiads'},
            {'text': 'Библиотека', 'url': '/library'}
        ],
        'document_links': [
            {'text': 'Устав образовательной организации', 'url': '/sveden/document'},
            {'text': 'Лицензия на осуществление образовательной деятельности', 'url': '/sveden/document'},
            {'text': 'Локальные нормативные акты', 'url': '/sveden/document'}
        ],
        'contact_address': 'Адрес: ул. К.Маркса, 64А, Волгодонск',
        'contact_phone': 'Телефон: 8 (8639) 27-97-76',
        'contact_email': 'junona@rostovschool.ru',
        'resource_links': [
            {'text': 'Министерство просвещения РФ', 'url': 'https://edu.gov.ru'},
            {'text': 'Федеральный портал "Российское образование"', 'url': 'http://www.edu.ru'},
            {'text': 'Единое окно доступа к образовательным ресурсам', 'url': 'http://window.edu.ru'}
        ],
        'staff_links': [
            {'text': 'Электронный журнал', 'url': 'https://elj.ru'},
            {'text': 'Методические материалы', 'url': '/methodology'},
            {'text': 'Повышение квалификации', 'url': '/professional-development'}
        ]
    })
    content_data = page_content.get_content()
    return render_template('main/info.html', page_content=content_data)

@main_bp.route('/about')
def about():
    page_content = PageContent.get_or_create('about', {
        'history': 'Гимназия "Юнона" основана в 1995 году. За годы работы школа стала одним из лидеров в области IT-образования в регионе.',
        'mission': 'Создание условий для развития талантов, воспитание патриотизма, формирование современных компетенций у учащихся.',
        'achievements': [
            'Победы в региональных и всероссийских олимпиадах',
            'Участие в международных проектах',
            'Собственная IT-лаборатория и медиацентр'
        ]
    })
    content_data = page_content.get_content()
    return render_template('main/about.html', page_content=content_data)

@main_bp.route('/p/<path:slug>')
def public_page(slug):
    """Пользовательская страница (пустая по умолчанию) с блоками контента.

    - URL: /p/<slug>
    - Хранение: InfoSection (content_blocks + text/form_data)
    - Создание записи: автоматически при первом заходе админом
    """
    from info.models import InfoSection

    slug_norm = _normalize_page_slug(slug)
    if not slug_norm:
        abort(404)

    url = f"/p/{slug_norm}"
    endpoint_base = f"page-{slug_norm.replace('/', '-')}"
    endpoint_base = endpoint_base[:100]

    section = InfoSection.query.filter_by(url=url).first()
    if not section:
        # Фолбэк: если страницу уже создали по endpoint, но URL отличается — подцепим её и обновим URL.
        section = InfoSection.query.filter_by(endpoint=endpoint_base).first()
        if section and section.url != url:
            try:
                section.url = url
                db.session.commit()
            except Exception:
                db.session.rollback()

    # Если страницы нет — создаём только для админа; для посетителя показываем "пустышку" без сохранения
    if not section:
        if current_user.is_authenticated:
            try:
                endpoint = _make_unique_info_endpoint(endpoint_base) or endpoint_base
                title = slug_norm.split('/')[-1].replace('-', ' ').title()
                section = InfoSection(
                    endpoint=endpoint,
                    url=url,
                    title=title or 'Страница',
                    text=json.dumps({'text': '', 'form_data': {}}, ensure_ascii=False),
                )
                section.set_content_blocks([])
                db.session.add(section)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при создании страницы: {e}', 'error')
                return redirect(url_for('main.index'))
        else:
            class TempSection:
                def __init__(self, endpoint, title, url):
                    self.id = None
                    self.endpoint = endpoint
                    self.title = title
                    self.url = url
                    self.text = json.dumps({'text': '', 'form_data': {}}, ensure_ascii=False)

                def get_content_blocks(self):
                    return []

            title = slug_norm.split('/')[-1].replace('-', ' ').title()
            section = TempSection(endpoint_base, title or 'Страница', url)

    today = datetime.now().strftime('%d.%m.%Y')
    response = make_response(render_template('info/section.html', section=section, children=[], today=today))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# Маршруты редактирования
@main_bp.route('/edit/<page_key>', methods=['GET', 'POST'])
@login_required
def edit_page(page_key):
    """Редактирование страницы"""
    allowed_pages = ['index', 'events', 'info', 'projects', 'albums', 'contacts', 'about']
    if page_key not in allowed_pages:
        flash('Страница не найдена', 'error')
        return redirect(url_for('main.index'))
    
    page_content = PageContent.get_or_create(page_key)
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            # Обрабатываем данные в зависимости от типа страницы
            if page_key == 'index':
                block_order = data.get('block_order')
                if isinstance(block_order, str):
                    try:
                        block_order = json.loads(block_order)
                    except Exception:
                        block_order = ['header', 'slider', 'announcements', 'news', 'school_info', 'directions', 'events_achievements']
                if not isinstance(block_order, list) or len(block_order) == 0:
                    block_order = ['header', 'slider', 'announcements', 'news', 'school_info', 'directions', 'events_achievements']
                slider_imgs = data.get('slider_images', [])
                if isinstance(slider_imgs, str):
                    try:
                        slider_imgs = json.loads(slider_imgs)
                    except Exception:
                        slider_imgs = []
                if not isinstance(slider_imgs, list):
                    slider_imgs = []
                content = {
                    'block_order': block_order,
                    'slider_images': slider_imgs,
                    'header_title': data.get('header_title', ''),
                    'header_subtitle': data.get('header_subtitle', ''),
                    'header_tags': [str(t).strip() for t in (json.loads(data.get('header_tags', '[]')) if isinstance(data.get('header_tags'), str) else data.get('header_tags', [])) if str(t).strip()],
                    'achievements': json.loads(data.get('achievements', '[]')) if isinstance(data.get('achievements'), str) else data.get('achievements', []),
                    'it_infrastructure': json.loads(data.get('it_infrastructure', '[]')) if isinstance(data.get('it_infrastructure'), str) else data.get('it_infrastructure', []),
                    'teachers': json.loads(data.get('teachers', '[]')) if isinstance(data.get('teachers'), str) else data.get('teachers', []),
                    'partnership': json.loads(data.get('partnership', '[]')) if isinstance(data.get('partnership'), str) else data.get('partnership', []),
                    'directions': json.loads(data.get('directions', '[]')) if isinstance(data.get('directions'), str) else data.get('directions', []),
                    'events': json.loads(data.get('events', '[]')) if isinstance(data.get('events'), str) else data.get('events', []),
                    'achievements_list': json.loads(data.get('achievements_list', '[]')) if isinstance(data.get('achievements_list'), str) else data.get('achievements_list', []),
                    'partners': json.loads(data.get('partners', '[]')) if isinstance(data.get('partners'), str) else data.get('partners', [])
                }
            elif page_key == 'contacts':
                content = {
                    'address': data.get('address', ''),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'work_hours': data.get('work_hours', '')
                }
            elif page_key == 'about':
                content = {
                    'history': data.get('history', ''),
                    'mission': data.get('mission', ''),
                    'achievements': json.loads(data.get('achievements', '[]')) if isinstance(data.get('achievements'), str) else data.get('achievements', [])
                }
            elif page_key == 'projects':
                projects_data = data.get('projects', [])
                if isinstance(projects_data, str):
                    try:
                        projects_data = json.loads(projects_data)
                    except:
                        projects_data = []
                if not isinstance(projects_data, list):
                    projects_data = []
                content = {'projects': projects_data}
            elif page_key == 'albums':
                albums_data = data.get('albums', [])
                if isinstance(albums_data, str):
                    try:
                        albums_data = json.loads(albums_data)
                    except:
                        albums_data = []
                if not isinstance(albums_data, list):
                    albums_data = []
                content = {'albums': albums_data}
            elif page_key == 'events':
                # События сохраняются в контент главной страницы
                events_data = data.get('events', [])
                if isinstance(events_data, str):
                    try:
                        events_data = json.loads(events_data)
                    except:
                        events_data = []
                if not isinstance(events_data, list):
                    events_data = []
                # Обновляем события в главной странице
                index_page = PageContent.get_or_create('index')
                index_content = index_page.get_content()
                index_content['events'] = events_data
                index_page.set_content(index_content)
                db.session.commit()
                if request.is_json:
                    return jsonify({'success': True, 'message': 'События успешно сохранены'})
                flash('События успешно сохранены', 'success')
                return redirect(url_for('main.index'))
            else:
                content = data
            
            page_content.set_content(content)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Страница успешно сохранена'})
            flash('Страница успешно сохранена', 'success')
            return redirect(url_for(f'main.{page_key}' if page_key != 'index' else 'main.index'))
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)})
            flash(f'Ошибка при сохранении: {str(e)}', 'error')
    
    # Для событий получаем данные из главной страницы
    if page_key == 'events':
        index_page = PageContent.get_or_create('index')
        index_content = index_page.get_content()
        content_data = {'events': index_content.get('events', [])}
    else:
        content_data = page_content.get_content()
    if page_key == 'index':
        default_order = ['header', 'slider', 'announcements', 'news', 'school_info', 'directions', 'events_achievements']
        block_order = content_data.get('block_order', default_order)
        if isinstance(block_order, list) and 'slider' not in block_order:
            if 'header' in block_order:
                idx = block_order.index('header') + 1
                block_order = block_order[:idx] + ['slider'] + block_order[idx:]
            else:
                block_order = ['slider'] + block_order
            content_data['block_order'] = block_order
        content_data['block_order_json'] = json.dumps(content_data.get('block_order', default_order), ensure_ascii=False)
        content_data['slider_images_json'] = json.dumps(content_data.get('slider_images', []), ensure_ascii=False)
        if 'header_tags' not in content_data and content_data.get('header_tagline'):
            content_data['header_tags'] = [t.strip() for t in content_data['header_tagline'].split('•') if t.strip()]
    return render_template(f'main/edit_{page_key}.html', page_key=page_key, page_content=content_data) 