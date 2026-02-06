"""
Простой диагностический скрипт для проверки структуры БД и ключевых таблиц.

Запуск (из корня проекта):
    py scripts/inspect_db.py

Скрипт НИЧЕГО не меняет в базе, только читает и печатает информацию.
"""

from __future__ import annotations

from typing import List

from sqlalchemy import inspect, text

from app import app
from database import db


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def inspect_schema() -> None:
    """Печатает список таблиц и их колонки."""
    insp = inspect(db.engine)
    tables: List[str] = sorted(insp.get_table_names())

    _print_header("Список таблиц в базе данных")
    for name in tables:
        print(f"- {name}")

    important_tables = [
        "info_file",
        "info_section",
        "news",
        "announcement",
        "file",
        "page_content",
        "user",
    ]

    _print_header("Подробная информация по ключевым таблицам")
    for table in important_tables:
        if table not in tables:
            print(f"[WARNING] Таблица '{table}' отсутствует")
            continue
        try:
            cols = insp.get_columns(table)
            col_names = [c["name"] for c in cols]
            print(f"\nТаблица '{table}':")
            print("  Колонки:", ", ".join(col_names))
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] Не удалось получить колонки для '{table}': {e}")


def inspect_info_file_columns() -> None:
    """Проверяет наличие критичных колонок в info_file."""
    insp = inspect(db.engine)
    if "info_file" not in insp.get_table_names():
        _print_header("Проверка info_file")
        print("[WARNING] Таблица 'info_file' не найдена")
        return

    cols = insp.get_columns("info_file")
    col_names = {c["name"] for c in cols}

    required = {
        "id",
        "filename",
        "original_filename",
        "file_path",
        "section_endpoint",
        "field_name",
        "file_size",
        "mime_type",
        "is_image",
        "upload_date",
        "display_name",
        "file_data",
        "stored_in_db",
    }

    _print_header("Проверка структуры таблицы info_file")
    missing = sorted(required - col_names)
    extra = sorted(col_names - required)

    print("Имеющиеся колонки:", ", ".join(sorted(col_names)))
    if missing:
        print("[PROBLEM] Отсутствуют обязательные колонки:", ", ".join(missing))
    else:
        print("OK: все ожидаемые колонки присутствуют.")

    if extra:
        print("Дополнительные (неиспользуемые) колонки:", ", ".join(extra))


def quick_counts() -> None:
    """Выводит количество записей в ключевых таблицах (для понимания, что в БД есть данные)."""
    from models.models import (  # type: ignore  # импорт только для диагностики
        Announcement,
        InfoFile,
        News,
        PageContent,
        User,
    )
    from info.models import InfoSection  # type: ignore

    _print_header("Краткая статистика по таблицам")
    try:
        print(f"News:          {News.query.count()}")
        print(f"Announcement:  {Announcement.query.count()}")
        print(f"File:          {db.session.execute(text('SELECT COUNT(*) FROM file')).scalar()}")
        print(f"InfoFile:      {InfoFile.query.count()}")
        print(f"InfoSection:   {InfoSection.query.count()}")
        print(f"PageContent:   {PageContent.query.count()}")
        print(f"User:          {User.query.count()}")
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Ошибка при подсчёте строк: {e}")


def main() -> None:
    with app.app_context():
        inspect_schema()
        inspect_info_file_columns()
        quick_counts()


if __name__ == "__main__":
    main()

