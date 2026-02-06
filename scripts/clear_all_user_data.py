#!/usr/bin/env python3
"""
Скрипт для полной очистки всех пользовательских данных
- Очищает все разделы (InfoSection) - тексты, form_data, content_blocks
- Удаляет все файлы из БД (InfoFile, File)
- Удаляет все новости (News)
- Удаляет все объявления (Announcement)
- Очищает контент редактируемых страниц (PageContent)
- Удаляет все файлы из папки static/uploads
"""

import os
import sys
import json
import shutil

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from info.models import InfoSection
from models.models import InfoFile, File, News, Announcement, PageContent
from utils.logger import logger
from sqlalchemy import text

def clear_all_user_data():
    """Полная очистка всех пользовательских данных"""
    app = create_app()
    
    with app.app_context():
        try:
            total_cleared = {
                'sections': 0,
                'info_files': 0,
                'files': 0,
                'news': 0,
                'announcements': 0,
                'pages': 0,
                'file_system_files': 0
            }
            
            print("=" * 70)
            print("ПОЛНАЯ ОЧИСТКА ВСЕХ ПОЛЬЗОВАТЕЛЬСКИХ ДАННЫХ")
            print("=" * 70)
            print()
            
            # 1. Очистка разделов (InfoSection)
            print("1. Очистка разделов (InfoSection)...")
            sections = InfoSection.query.all()
            total_cleared['sections'] = len(sections)
            
            for section in sections:
                print(f"   - Очистка раздела: {section.endpoint} ({section.title})")
                empty_data = {
                    'text': '',
                    'form_data': {}
                }
                section.text = json.dumps(empty_data, ensure_ascii=False)
                section.content_blocks = None
            
            print(f"   [OK] Очищено разделов: {total_cleared['sections']}")
            print()
            
            # 2. Удаление файлов из БД (InfoFile)
            print("2. Удаление файлов из БД (InfoFile)...")
            try:
                # Пробуем использовать ORM
                info_files = InfoFile.query.all()
                total_cleared['info_files'] = len(info_files)
                
                for info_file in info_files:
                    print(f"   - Удаление: {info_file.filename} (раздел: {info_file.section_endpoint})")
                    db.session.delete(info_file)
            except Exception as e:
                # Если ORM не работает (нет колонок file_data/stored_in_db), используем прямой SQL
                if 'no such column' in str(e).lower() or 'file_data' in str(e).lower():
                    print("   [INFO] Используем прямой SQL запрос (модель содержит поля, которых нет в БД)")
                    result = db.session.execute(text("SELECT COUNT(*) FROM info_file"))
                    count = result.scalar()
                    total_cleared['info_files'] = count if count else 0
                    
                    if total_cleared['info_files'] > 0:
                        db.session.execute(text("DELETE FROM info_file"))
                        print(f"   - Удалено записей: {total_cleared['info_files']}")
                else:
                    raise
            
            print(f"   [OK] Удалено файлов из БД: {total_cleared['info_files']}")
            print()
            
            # 3. Удаление файлов новостей/объявлений (File)
            print("3. Удаление файлов новостей/объявлений (File)...")
            files = File.query.all()
            total_cleared['files'] = len(files)
            
            for file in files:
                print(f"   - Удаление: {file.filename}")
                db.session.delete(file)
            
            print(f"   [OK] Удалено файлов: {total_cleared['files']}")
            print()
            
            # 4. Удаление новостей (News)
            print("4. Удаление новостей (News)...")
            news_items = News.query.all()
            total_cleared['news'] = len(news_items)
            
            for news in news_items:
                print(f"   - Удаление новости: {news.title}")
                db.session.delete(news)
            
            print(f"   [OK] Удалено новостей: {total_cleared['news']}")
            print()
            
            # 5. Удаление объявлений (Announcement)
            print("5. Удаление объявлений (Announcement)...")
            announcements = Announcement.query.all()
            total_cleared['announcements'] = len(announcements)
            
            for announcement in announcements:
                print(f"   - Удаление объявления: {announcement.title}")
                db.session.delete(announcement)
            
            print(f"   [OK] Удалено объявлений: {total_cleared['announcements']}")
            print()
            
            # 6. Очистка контента редактируемых страниц (PageContent)
            print("6. Очистка контента редактируемых страниц (PageContent)...")
            pages = PageContent.query.all()
            total_cleared['pages'] = len(pages)
            
            for page in pages:
                print(f"   - Очистка страницы: {page.page_key}")
                page.content = json.dumps({}, ensure_ascii=False)
            
            print(f"   [OK] Очищено страниц: {total_cleared['pages']}")
            print()
            
            # 7. Удаление файлов из файловой системы
            print("7. Удаление файлов из файловой системы (static/uploads)...")
            uploads_dir = os.path.join('static', 'uploads')
            
            if os.path.exists(uploads_dir):
                file_count = 0
                dir_count = 0
                
                # Подсчитываем файлы и папки
                for root, dirs, files in os.walk(uploads_dir):
                    file_count += len(files)
                    dir_count += len(dirs)
                
                print(f"   Найдено файлов: {file_count}, папок: {dir_count}")
                
                # Удаляем все содержимое папки uploads
                for item in os.listdir(uploads_dir):
                    item_path = os.path.join(uploads_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            print(f"   - Удалена папка: {item}")
                        else:
                            os.remove(item_path)
                            print(f"   - Удален файл: {item}")
                            file_count += 1
                    except Exception as e:
                        print(f"   [WARNING] Не удалось удалить {item_path}: {e}")
                
                total_cleared['file_system_files'] = file_count
                print(f"   [OK] Удалено файлов из файловой системы: {file_count}")
            else:
                print(f"   [INFO] Папка {uploads_dir} не существует")
            
            print()
            
            # Сохраняем все изменения в БД
            print("Сохранение изменений в базе данных...")
            db.session.commit()
            print("[OK] Изменения сохранены")
            print()
            
            # Итоговая статистика
            print("=" * 70)
            print("ИТОГОВАЯ СТАТИСТИКА")
            print("=" * 70)
            print(f"Очищено разделов:           {total_cleared['sections']}")
            print(f"Удалено InfoFile из БД:      {total_cleared['info_files']}")
            print(f"Удалено File из БД:          {total_cleared['files']}")
            print(f"Удалено новостей:            {total_cleared['news']}")
            print(f"Удалено объявлений:         {total_cleared['announcements']}")
            print(f"Очищено страниц:             {total_cleared['pages']}")
            print(f"Удалено файлов с диска:     {total_cleared['file_system_files']}")
            print("=" * 70)
            print()
            print("[OK] Полная очистка завершена успешно!")
            print()
            print("ВНИМАНИЕ:")
            print("- Все разделы сохранены, но их содержимое очищено")
            print("- Все файлы удалены из БД и файловой системы")
            print("- Все новости и объявления удалены")
            print("- Контент редактируемых страниц очищен")
            print()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при очистке данных: {e}")
            import traceback
            print(f"\n[ERROR] Ошибка при очистке данных: {e}")
            print("\nТрассировка:")
            traceback.print_exc()
            return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Полная очистка всех пользовательских данных')
    parser.add_argument('--yes', '-y', action='store_true', help='Автоматически подтвердить очистку без запроса')
    args = parser.parse_args()
    
    print("=" * 70)
    print("ПОЛНАЯ ОЧИСТКА ВСЕХ ПОЛЬЗОВАТЕЛЬСКИХ ДАННЫХ")
    print("=" * 70)
    print()
    print("ВНИМАНИЕ: Это действие удалит:")
    print("  - Все тексты и данные из разделов (InfoSection)")
    print("  - Все файлы из базы данных (InfoFile, File)")
    print("  - Все новости (News)")
    print("  - Все объявления (Announcement)")
    print("  - Весь контент редактируемых страниц (PageContent)")
    print("  - Все файлы из папки static/uploads")
    print()
    print("Структура разделов (вкладки) будет сохранена, но пуста.")
    print()
    
    if not args.yes:
        print("Продолжить? (yes/no): ", end='')
        try:
            confirmation = input().strip().lower()
        except EOFError:
            print("\nОчистка отменена (нет интерактивного ввода).")
            print("Используйте флаг --yes для автоматического подтверждения.")
            sys.exit(0)
    else:
        confirmation = 'yes'
        print("Автоматическое подтверждение (--yes)")
    
    if confirmation in ['yes', 'y', 'да', 'д']:
        print("\nНачинаем полную очистку...\n")
        success = clear_all_user_data()
        
        if success:
            print("\n" + "=" * 70)
            print("[OK] Полная очистка завершена успешно!")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("[ERROR] Очистка завершена с ошибками")
            print("=" * 70)
            sys.exit(1)
    else:
        print("\nОчистка отменена.")
        sys.exit(0)

