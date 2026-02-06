from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from . import news_bp
from models.models import News
from database import db
from wtforms import StringField, TextAreaField, SubmitField, FileField, MultipleFileField, BooleanField, DateField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from datetime import datetime
from sqlalchemy import func, desc
from utils.file_helpers import save_image, save_document, get_content_folder_path, get_content_documents
from utils.logger import logger
import os
import mimetypes
import urllib.parse


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Содержимое', validators=[DataRequired()])
    images = MultipleFileField('Фотографии', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Разрешены только изображения!')])
    files = MultipleFileField('Документы', validators=[FileAllowed(['pdf', 'doc', 'docx', 'txt'], 'Разрешены только документы!')])
    publication_date = DateField('Дата публикации', format='%Y-%m-%d', default=None, validators=[])
    is_featured = BooleanField('Сделать главной')
    publish_now = BooleanField('Опубликовать сейчас')
    submit = SubmitField('Далее')




@news_bp.route('/')
def news_list():
    now = datetime.utcnow()
    published_dt = func.coalesce(News.publication_date, News.created_at)
    news = (News.query
                 .filter(News.is_published.is_(True))
                 .filter(published_dt <= now)
                 .order_by(desc(News.is_featured), desc(published_dt))
                 .all())
    return render_template('news/news_list.html', news=news)


@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    item = News.query.get_or_404(news_id)
    # Получаем документы из файловой системы
    doc_files = get_content_documents('news', news_id, item.publication_date)
    return render_template('news/news_detail.html', item=item, doc_files=doc_files)


@news_bp.route('/new', methods=['GET', 'POST'])
@login_required
def news_create():
    form = NewsForm()
    logger.debug(f'Form submitted: {form.is_submitted()}')
    logger.debug(f'Form valid: {form.validate()}')
    if form.errors:
        logger.debug(f'Form errors: {form.errors}')
    
    if form.is_submitted():
        publication_dt = None
        if form.publication_date.data:
            publication_dt = datetime.combine(form.publication_date.data, datetime.min.time())
        item = News(
            title=form.title.data.strip(), 
            content=form.content.data,
            publication_date=publication_dt,
            is_featured=bool(form.is_featured.data),
            is_published=False
        )
        db.session.add(item)
        db.session.flush()  # Получаем ID новости
        
        # Обработка изображений (не выбираем превью на этом шаге)
        if form.images.data:
            logger.debug(f'Processing {len(form.images.data)} images')
            for img in form.images.data:
                if img and img.filename:
                    logger.debug(f'Processing image: {img.filename}')
                    saved_name = save_image(img, 'news', item.id, publication_dt)
                    if saved_name:
                        try:
                            from models.models import File
                            file_obj = File(filename=saved_name, news_id=item.id, kind='image')
                            db.session.add(file_obj)
                            logger.debug(f'Added file {saved_name} for news {item.id}')
                        except Exception as e:
                            logger.error(f'Failed to add file {saved_name}: {e}')
                    else:
                        logger.error(f'Failed to save image {img.filename}')
                else:
                    logger.debug('Skipping empty image')

        # Обработка документов (сохраняем только в файловую систему, без БД)
        if form.files.data:
            logger.debug(f'Processing {len(form.files.data)} documents')
            for file in form.files.data:
                if file and file.filename:
                    logger.debug(f'Processing document: {file.filename}')
                    try:
                        saved_name = save_document(file, 'news', item.id, publication_dt)
                        if saved_name:
                            logger.debug(f'Saved document {saved_name} for news {item.id} (file system only)')
                        else:
                            logger.error(f'Failed to save document {file.filename}')
                    except Exception as e:
                        logger.error(f'Failed to save document {file.filename}: {e}')
                else:
                    logger.debug('Skipping empty document')
        
        try:
            db.session.commit()
            logger.info(f'Successfully committed news {item.id}')
            
            # Проверяем, что файлы действительно сохранились
            from models.models import File
            saved_files = File.query.filter_by(news_id=item.id).all()
            logger.debug(f'Files in database for news {item.id}: {len(saved_files)}')
            for f in saved_files:
                logger.debug(f'File: {f.filename}, kind: {f.kind}')
            
            flash('Новость создана. Шаг 2: выберите превью и опубликуйте.')
            return redirect(url_for('news_bp.news_review', news_id=item.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to commit news {item.id}: {e}')
            flash(f'Ошибка при создании новости: {e}', 'error')
            return render_template('news/news_form.html', form=form, page_title='Новая новость (шаг 1)')
    return render_template('news/news_form.html', form=form, page_title='Новая новость (шаг 1)')


@news_bp.route('/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
def news_edit(news_id):
    item = News.query.get_or_404(news_id)
    # Предзаполняем дату публикации только датой
    form = NewsForm(obj=item)
    if item.publication_date:
        form.publication_date.data = item.publication_date.date()
    if form.validate_on_submit():
        item.title = form.title.data.strip()
        item.content = form.content.data
        # Обновляем дату публикации и флаг
        if form.publication_date.data:
            item.publication_date = datetime.combine(form.publication_date.data, datetime.min.time())
        else:
            item.publication_date = None
        item.is_featured = bool(form.is_featured.data)

        # Доп. загрузка изображений
        if getattr(form, 'images', None) and form.images.data:
            # Используем актуальную дату публикации для структуры путей
            publication_dt = item.publication_date
            for img in form.images.data:
                if img and img.filename:
                    saved_name = save_image(img, 'news', item.id, publication_dt)
                    if saved_name:
                        from models.models import File
                        db.session.add(File(filename=saved_name, news_id=item.id, kind='image'))
        
        try:
            db.session.commit()
            # Обработка выбора превью
            preview_name = request.form.get('preview_image')
            if preview_name:
                from models.models import File
                file_obj = File.query.filter_by(news_id=item.id, filename=preview_name, kind='image').first()
                if file_obj:
                    # Снимаем прежний флаг
                    File.query.filter_by(news_id=item.id, kind='image', is_preview=True).update({File.is_preview: False})
                    file_obj.is_preview = True
                    item.image = preview_name
            # Публикация
            if bool(form.publish_now.data):
                item.is_published = True
            db.session.commit()
            logger.info(f'Successfully updated news {item.id}')
            flash('Новость обновлена')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to update news {item.id}: {e}')
            flash(f'Ошибка при обновлении новости: {e}', 'error')
        
        # Если это AJAX запрос, возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Новость обновлена',
                'redirect': url_for('news_bp.news_detail', news_id=item.id)
            })
        
        return redirect(url_for('news_bp.news_detail', news_id=item.id))
    # Передать связанные изображения для выбора превью
    from models.models import File
    images = File.query.filter_by(news_id=item.id, kind='image').all()
    
    # Если запрашивается содержимое для модального окна
    if request.args.get('modal') == 'true':
        return render_template('news/news_form_modal.html', form=form, page_title='Редактировать новость', images=images, item=item)
    
    return render_template('news/news_form.html', form=form, page_title='Редактировать новость', images=images, item=item)


@news_bp.route('/<int:news_id>/review', methods=['GET', 'POST'])
@login_required
def news_review(news_id):
    from models.models import File, News
    item = News.query.get_or_404(news_id)
    images = File.query.filter_by(news_id=item.id, kind='image').all()
    if request.method == 'POST':
        publish_without_photo = request.form.get('publish_without_photo') in ('1', 'true', 'on', 'yes')
        preview_name = request.form.get('preview_image')
        if publish_without_photo:
            # Оставляем поле превью пустым
            File.query.filter_by(news_id=item.id, kind='image', is_preview=True).update({File.is_preview: False})
            item.image = None
        elif preview_name:
            file_obj = File.query.filter_by(news_id=item.id, filename=preview_name, kind='image').first()
            if file_obj:
                File.query.filter_by(news_id=item.id, kind='image', is_preview=True).update({File.is_preview: False})
                file_obj.is_preview = True
                item.image = preview_name
        else:
            # Без выбора превью и без явного разрешения публиковать без фото — не публикуем
            flash('Выберите изображение для превью или включите "Опубликовать без фото".', 'error')
            return render_template('news/news_review.html', item=item, images=images)
        item.is_published = True
        try:
            db.session.commit()
            logger.info(f'Successfully published news {item.id}')
            flash('Новость опубликована')
            return redirect(url_for('news_bp.news_detail', news_id=item.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to publish news {item.id}: {e}')
            flash(f'Ошибка при публикации новости: {e}', 'error')
            return render_template('news/news_review.html', item=item, images=images)
    return render_template('news/news_review.html', item=item, images=images)


@news_bp.route('/<int:news_id>/delete', methods=['POST'])
@login_required
def news_delete(news_id):
    item = News.query.get_or_404(news_id)
    try:
        db.session.delete(item)
        db.session.commit()
        logger.info(f'Successfully deleted news {news_id}')
        flash('Новость удалена')
        return redirect(url_for('news_bp.news_list'))
    except Exception as e:
        db.session.rollback()
        logger.error(f'Failed to delete news {news_id}: {e}')
        flash(f'Ошибка при удалении новости: {e}', 'error')
        return redirect(url_for('news_bp.news_list'))


@news_bp.route('/download/<int:news_id>/<filename>')
def download_file(news_id, filename):
    """Скачивание файла новости"""
    try:
        item = News.query.get_or_404(news_id)
        
        # Определяем путь к файлу
        publication_date = item.publication_date if item.publication_date else item.created_at
        folder_path = get_content_folder_path('news', news_id, publication_date)
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.exists(file_path):
            flash('Файл не найден', 'error')
            return redirect(url_for('news_bp.news_detail', news_id=news_id))
        
        # Определяем MIME-тип
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            mimetype = 'application/octet-stream'
        
        # Кодируем имя файла
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
        
        # Создаем response
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
        # Устанавливаем заголовки
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла {filename} из новости {news_id}: {e}")
        flash('Ошибка при скачивании файла', 'error')
        return redirect(url_for('news_bp.news_detail', news_id=news_id))
