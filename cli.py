import click
from flask.cli import with_appcontext
from database import db
from info.models import InfoSection
import json
import logging

logger = logging.getLogger(__name__)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    # db.create_all() # Usually we might want to just ensure tables, not drop. 
    # But wait, create_all does not drop. 
    # Let's just run create_all safely.
    
    # Импортируем все модели для создания таблиц
    # Note: imports should be inside the function or at top level if no circular deps
    from models.models import PageContent, User, News, Announcement, File, InfoFile
    
    db.create_all()
    click.echo('Initialized the database.')
    
    # Автоматическое создание обязательных разделов
    _ensure_required_sections()

def _ensure_required_sections():
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
            click.echo(f"Created required section: {endpoint}")
    
    try:
        db.session.commit()
        click.echo("Required sections check completed.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error checking required sections: {e}")
