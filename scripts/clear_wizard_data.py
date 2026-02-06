#!/usr/bin/env python3
"""
Скрипт для полной очистки всех данных мастеров заполнения
Сохраняет все вкладки (разделы), но очищает их содержимое
"""

import os
import sys
import json

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from info.models import InfoSection
from models.models import InfoFile
from utils.logger import logger

def clear_all_wizard_data():
    """Очищает все данные мастеров заполнения, сохраняя структуру разделов"""
    app = create_app()
    
    with app.app_context():
        try:
            # Получаем все разделы
            sections = InfoSection.query.all()
            cleared_count = 0
            
            print(f"Найдено разделов: {len(sections)}")
            
            for section in sections:
                print(f"Очистка раздела: {section.endpoint} ({section.title})")
                
                # Очищаем содержимое, но сохраняем структуру
                # Оставляем только базовую структуру с пустыми данными
                empty_data = {
                    'text': '',
                    'form_data': {}
                }
                
                section.text = json.dumps(empty_data, ensure_ascii=False)
                section.content_blocks = None
                
                cleared_count += 1
            
            # Очищаем все файлы из БД (InfoFile)
            info_files = InfoFile.query.all()
            files_count = len(info_files)
            
            print(f"\nНайдено файлов в БД: {files_count}")
            
            for info_file in info_files:
                print(f"Удаление файла из БД: {info_file.filename} (раздел: {info_file.section_endpoint})")
                db.session.delete(info_file)
            
            # Сохраняем изменения
            db.session.commit()
            
            print(f"\n[OK] Успешно очищено:")
            print(f"   - Разделов: {cleared_count}")
            print(f"   - Файлов из БД: {files_count}")
            print(f"\nВсе вкладки (разделы) сохранены, но их содержимое очищено.")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при очистке данных: {e}")
            print(f"\n[ERROR] Ошибка при очистке данных: {e}")
            return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Очистка всех данных мастеров заполнения')
    parser.add_argument('--yes', '-y', action='store_true', help='Автоматически подтвердить очистку без запроса')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Очистка всех данных мастеров заполнения")
    print("=" * 60)
    print("\nВнимание: Это действие очистит все данные из разделов,")
    print("но сохранит структуру разделов (вкладки).")
    
    if not args.yes:
        print("\nПродолжить? (yes/no): ", end='')
        try:
            confirmation = input().strip().lower()
        except EOFError:
            print("\nОчистка отменена (нет интерактивного ввода).")
            print("Используйте флаг --yes для автоматического подтверждения.")
            sys.exit(0)
    else:
        confirmation = 'yes'
        print("\nАвтоматическое подтверждение (--yes)")
    
    if confirmation in ['yes', 'y', 'да', 'д']:
        print("\nНачинаем очистку...\n")
        success = clear_all_wizard_data()
        
        if success:
            print("\n" + "=" * 60)
            print("[OK] Очистка завершена успешно!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[ERROR] Очистка завершена с ошибками")
            print("=" * 60)
            sys.exit(1)
    else:
        print("\nОчистка отменена.")
        sys.exit(0)

