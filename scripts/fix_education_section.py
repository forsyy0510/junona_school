#!/usr/bin/env python3
"""
Скрипт для проверки и создания раздела "Образование"
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from info.models import InfoSection

def fix_education_section():
    """Проверяет и создает раздел 'Образование' если его нет"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Проверка и создание раздела 'Образование'")
        print("=" * 60)
        print()
        
        # Проверяем наличие раздела
        section = InfoSection.query.filter_by(endpoint='education').first()
        
        if section:
            print(f"✅ Раздел 'Образование' уже существует:")
            print(f"   ID: {section.id}")
            print(f"   Endpoint: {section.endpoint}")
            print(f"   URL: {section.url}")
            print(f"   Title: {section.title}")
            print()
            
            # Проверяем, правильный ли URL
            if section.url != '/sveden/education':
                print(f"⚠️  URL раздела неверный: {section.url}")
                print("   Исправляю URL...")
                section.url = '/sveden/education'
                db.session.commit()
                print("   ✅ URL исправлен")
                print()
            
            return True
        else:
            print("❌ Раздел 'Образование' не найден")
            print("   Создаю раздел...")
            print()
            
            # Создаем раздел
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
            
            try:
                db.session.commit()
                print("✅ Раздел 'Образование' успешно создан!")
                print(f"   ID: {section.id}")
                print(f"   Endpoint: {section.endpoint}")
                print(f"   URL: {section.url}")
                print()
                return True
            except Exception as e:
                db.session.rollback()
                print(f"❌ Ошибка при создании раздела: {e}")
                print()
                return False

if __name__ == '__main__':
    success = fix_education_section()
    
    if success:
        print("=" * 60)
        print("✅ Готово! Раздел 'Образование' доступен по URL:")
        print("   /sveden/education")
        print("   /info/education (редирект)")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ Ошибка при создании раздела")
        print("=" * 60)
        sys.exit(1)

