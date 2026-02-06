from flask import render_template, make_response
from . import albums_bp
from info.models import InfoSection
from database import db
import json
from datetime import datetime

@albums_bp.route('/')
def albums_list():
    section = InfoSection.query.filter_by(endpoint='albums').first()
    
    if not section:
        section = InfoSection(
            endpoint='albums',
            title='Фотоальбомы',
            url='/albums',
            text=json.dumps({'text': '', 'form_data': {}}, ensure_ascii=False),
            content_blocks=json.dumps([], ensure_ascii=False)
        )
        db.session.add(section)
        db.session.commit()
    
    today = datetime.now().strftime('%d.%m.%Y')
    response = make_response(
        render_template(
            'info/section.html',
            section=section,
            children=[],
            today=today,
            is_sveden=False,
        )
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@albums_bp.route('/albums/<int:album_id>')
def album_detail(album_id):
    return render_template('albums/album_detail.html', album_id=album_id) 