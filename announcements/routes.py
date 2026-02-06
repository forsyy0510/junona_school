from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required
from . import announcements_bp
from models.models import Announcement
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


class AnnouncementForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Содержимое', validators=[DataRequired()])
    images = MultipleFileField('Фотографии', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Разрешены только изображения!')])
    files = MultipleFileField('Документы', validators=[FileAllowed(['pdf', 'doc', 'docx', 'txt'], 'Разрешены только документы!')])
    publication_date = DateField('Дата публикации', format='%Y-%m-%d', default=None, validators=[])
    is_featured = BooleanField('Сделать главным объявлением')
    publish_now = BooleanField('Опубликовать сейчас')
    submit = SubmitField('Далее')




@announcements_bp.route('/')
def announcements_list():
    now = datetime.utcnow()
    published_dt = func.coalesce(Announcement.publication_date, Announcement.created_at)
    announcements = (Announcement.query
                        .filter(Announcement.is_published.is_(True))
                        .filter(published_dt <= now)
                        .order_by(desc(Announcement.is_featured), desc(published_dt))
                        .all())
    return render_template('announcements/announcements_list.html', announcements=announcements)


@announcements_bp.route('/<int:announcement_id>')
def announcement_detail(announcement_id):
    item = Announcement.query.get_or_404(announcement_id)
    # Получаем документы из файловой системы
    doc_files = get_content_documents('announcements', announcement_id, item.publication_date)
    return render_template('announcements/announcement_detail.html', item=item, doc_files=doc_files)


@announcements_bp.route('/new', methods=['GET', 'POST'])
@login_required
def announcement_create():
    form = AnnouncementForm()
    if form.validate_on_submit():
        publication_dt = None
        if form.publication_date.data:
            publication_dt = datetime.combine(form.publication_date.data, datetime.min.time())
        item = Announcement(
            title=form.title.data.strip(), 
            content=form.content.data,
            publication_date=publication_dt,
            is_featured=bool(form.is_featured.data),
            is_published=False
        )
        db.session.add(item)
        db.session.flush()  # Получаем ID объявления
        
        # Обработка изображений
        if form.images.data:
            for img in form.images.data:
                if img and img.filename:
                    saved_name = save_image(img, 'announcements', item.id, publication_dt)
                    if saved_name:
                        try:
                            from models.models import File
                            file_obj = File(filename=saved_name, announcement_id=item.id, kind='image')
                            db.session.add(file_obj)
                            logger.debug(f'Added file {saved_name} for announcement {item.id}')
                        except Exception as e:
                            logger.error(f'Failed to add file {saved_name}: {e}')

        # Обработка документов (сохраняем только в файловую систему, без БД)
        if form.files.data:
            for file in form.files.data:
                if file and file.filename:
                    try:
                        saved_name = save_document(file, 'announcements', item.id, publication_dt)
                        if saved_name:
                            logger.debug(f'Saved document {saved_name} for announcement {item.id} (file system only)')
                    except Exception as e:
                        logger.error(f'Failed to save document {file.filename}: {e}')
        
        try:
            db.session.commit()
            logger.info(f'Successfully committed announcement {item.id}')
            flash('Объявление создано. Шаг 2: выберите превью и опубликуйте.')
            return redirect(url_for('announcements.announcement_review', announcement_id=item.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to commit announcement {item.id}: {e}')
            flash(f'Ошибка при создании объявления: {e}', 'error')
            return render_template('announcements/announcement_form.html', form=form, page_title='Новое объявление (шаг 1)')
    return render_template('announcements/announcement_form.html', form=form, page_title='Новое объявление (шаг 1)')


@announcements_bp.route('/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
def announcement_edit(announcement_id):
    item = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm(obj=item)
    if item.publication_date:
        form.publication_date.data = item.publication_date.date()
    if form.validate_on_submit():
        item.title = form.title.data.strip()
        item.content = form.content.data
        if form.publication_date.data:
            item.publication_date = datetime.combine(form.publication_date.data, datetime.min.time())
        else:
            item.publication_date = None
        item.is_featured = bool(form.is_featured.data)
        
        # Доп. загрузка изображений
        if form.images.data:
            for img in form.images.data:
                if img and img.filename:
                    saved_name = save_image(img, 'announcements', item.id, item.publication_date)
                    if saved_name:
                        try:
                            from models.models import File
                            file_obj = File(filename=saved_name, announcement_id=item.id, kind='image')
                            db.session.add(file_obj)
                            logger.debug(f'Added file {saved_name} for announcement {item.id}')
                        except Exception as e:
                            logger.error(f'Failed to add file {saved_name}: {e}')
        
        # Доп. загрузка документов (сохраняем только в файловую систему, без БД)
        if form.files.data:
            for file in form.files.data:
                if file and file.filename:
                    try:
                        saved_name = save_document(file, 'announcements', item.id, item.publication_date)
                        if saved_name:
                            logger.debug(f'Saved document {saved_name} for announcement {item.id} (file system only)')
                    except Exception as e:
                        logger.error(f'Failed to save document {file.filename}: {e}')
        
        # Выбор превью
        preview_name = request.form.get('preview_image')
        if preview_name:
            from models.models import File
            file_obj = File.query.filter_by(announcement_id=item.id, filename=preview_name, kind='image').first()
            if file_obj:
                File.query.filter_by(announcement_id=item.id, kind='image', is_preview=True).update({File.is_preview: False})
                file_obj.is_preview = True
                item.image = preview_name
        
        # Публикация
        if bool(form.publish_now.data):
            item.is_published = True
        
        try:
            db.session.commit()
            logger.info(f'Successfully updated announcement {item.id}')
            flash('Объявление обновлено')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to update announcement {item.id}: {e}')
            flash(f'Ошибка при обновлении объявления: {e}', 'error')
        
        # Если это AJAX запрос, возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Объявление обновлено',
                'redirect': url_for('announcements.announcement_detail', announcement_id=item.id)
            })
        
        return redirect(url_for('announcements.announcement_detail', announcement_id=item.id))
    from models.models import File
    images = File.query.filter_by(announcement_id=item.id, kind='image').all()
    
    # Если запрашивается содержимое для модального окна
    if request.args.get('modal') == 'true':
        return render_template('announcements/announcement_form_modal.html', form=form, page_title='Редактировать объявление', images=images, item=item)
    
    return render_template('announcements/announcement_form.html', form=form, page_title='Редактировать объявление', images=images)


@announcements_bp.route('/<int:announcement_id>/review', methods=['GET', 'POST'])
@login_required
def announcement_review(announcement_id):
    from models.models import File
    item = Announcement.query.get_or_404(announcement_id)
    images = File.query.filter_by(announcement_id=item.id, kind='image').all()
    if request.method == 'POST':
        publish_without_photo = request.form.get('publish_without_photo') in ('1', 'true', 'on', 'yes')
        preview_name = request.form.get('preview_image')
        if publish_without_photo:
            File.query.filter_by(announcement_id=item.id, kind='image', is_preview=True).update({File.is_preview: False})
            item.image = None
        elif preview_name:
            file_obj = File.query.filter_by(announcement_id=item.id, filename=preview_name, kind='image').first()
            if file_obj:
                File.query.filter_by(announcement_id=item.id, kind='image', is_preview=True).update({File.is_preview: False})
                file_obj.is_preview = True
                item.image = preview_name
        else:
            flash('Выберите изображение для превью или включите "Опубликовать без фото".', 'error')
            return render_template('announcements/announcement_review.html', item=item, images=images)
        item.is_published = True
        try:
            db.session.commit()
            logger.info(f'Successfully published announcement {item.id}')
            flash('Объявление опубликовано')
            return redirect(url_for('announcements.announcement_detail', announcement_id=item.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to publish announcement {item.id}: {e}')
            flash(f'Ошибка при публикации объявления: {e}', 'error')
            return render_template('announcements/announcement_review.html', item=item, images=images)
    return render_template('announcements/announcement_review.html', item=item, images=images)


@announcements_bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
def announcement_delete(announcement_id):
    item = Announcement.query.get_or_404(announcement_id)
    try:
        db.session.delete(item)
        db.session.commit()
        logger.info(f'Successfully deleted announcement {announcement_id}')
        flash('Объявление удалено')
        return redirect(url_for('announcements.announcements_list'))
    except Exception as e:
        db.session.rollback()
        logger.error(f'Failed to delete announcement {announcement_id}: {e}')
        flash(f'Ошибка при удалении объявления: {e}', 'error')
        return redirect(url_for('announcements.announcements_list'))


@announcements_bp.route('/download/<int:announcement_id>/<filename>')
def download_file(announcement_id, filename):
    """Скачивание файла объявления"""
    try:
        item = Announcement.query.get_or_404(announcement_id)
        
        # Определяем путь к файлу
        publication_date = item.publication_date if item.publication_date else item.created_at
        folder_path = get_content_folder_path('announcements', announcement_id, publication_date)
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.exists(file_path):
            flash('Файл не найден', 'error')
            return redirect(url_for('announcements.announcement_detail', announcement_id=announcement_id))
        
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
        logger.error(f"Ошибка при скачивании файла {filename} из объявления {announcement_id}: {e}")
        flash('Ошибка при скачивании файла', 'error')
        return redirect(url_for('announcements.announcement_detail', announcement_id=announcement_id)) 