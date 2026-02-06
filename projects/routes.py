from flask import render_template, make_response
from . import projects_bp
from info.models import InfoSection
from database import db
import json
from datetime import datetime

@projects_bp.route('/')
def projects_list():
    section = InfoSection.query.filter_by(endpoint='projects').first()
    
    if not section:
        section = InfoSection(
            endpoint='projects',
            title='Проекты',
            url='/projects',
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

@projects_bp.route('/projects/<int:project_id>')
def project_detail(project_id):
    return render_template('projects/project_detail.html', project_id=project_id) 