"""
Экспорт и импорт данных сайта для резервного копирования и восстановления при глобальных изменениях.
Поддерживается полная выгрузка, выгрузка по типам (новости, основные разделы, боковое меню) и выборочная.
Структура content_blocks в InfoSection: блоки с type, title, rows, itemprop, row_itemprops и др.
"""

import json
import base64
import os
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO

from database import db
from models.models import (
    User,
    News,
    Announcement,
    File,
    InfoFile,
    PageContent,
)
from info.models import InfoSection


EXPORT_VERSION = 1
INSERT_ORDER = [User, News, Announcement, File, InfoSection, PageContent, InfoFile]
DELETE_ORDER = [InfoFile, File, News, Announcement, PageContent, InfoSection, User]

# Основные разделы сведений (/sveden/*)
SVEDEN_URL_PREFIX = '/sveden/'
# Разделы бокового меню
SIDEBAR_URL_PREFIX = '/sidebar/'


def _serialize_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def _deserialize_value(value, column_type):
    if value is None:
        return None
    type_name = type(column_type).__name__ if column_type else ""
    if "DateTime" in type_name:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if "LargeBinary" in type_name or "BLOB" in type_name:
        try:
            return base64.b64decode(value)
        except (ValueError, TypeError):
            return None
    return value


def _model_to_tablename(model):
    return model.__table__.name


def _export_model_rows(model, rows):
    """Преобразует список записей model в список словарей для JSON."""
    name = _model_to_tablename(model)
    columns = [c.name for c in model.__table__.columns]
    out = []
    for row in rows:
        record = {}
        for col in columns:
            try:
                val = getattr(row, col)
                record[col] = _serialize_value(val)
            except Exception:
                record[col] = None
        out.append(record)
    return name, out


def export_data():
    """Собирает все данные из БД в словарь, пригодный для JSON."""
    out = {
        "version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "tables": {},
    }
    for model in INSERT_ORDER:
        rows = model.query.all()
        name, records = _export_model_rows(model, rows)
        out["tables"][name] = records
    return out


def export_data_news():
    """Выгрузка только новостей и объявлений (News, Announcement, File привязанные к ним)."""
    files = File.query.filter(
        (File.news_id.isnot(None)) | (File.announcement_id.isnot(None))
    ).all()
    out = {
        "version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "export_type": "news",
        "tables": {},
    }
    _, out["tables"][_model_to_tablename(News)] = _export_model_rows(News, News.query.all())
    _, out["tables"][_model_to_tablename(Announcement)] = _export_model_rows(Announcement, Announcement.query.all())
    _, out["tables"][_model_to_tablename(File)] = _export_model_rows(File, files)
    return out


def _sveden_sections():
    """Разделы основных сведений: url начинается с /sveden/."""
    return InfoSection.query.filter(InfoSection.url.startswith(SVEDEN_URL_PREFIX)).all()


def _sidebar_sections():
    """Разделы бокового меню: url начинается с /sidebar/."""
    return InfoSection.query.filter(InfoSection.url.startswith(SIDEBAR_URL_PREFIX)).all()


def export_data_sveden():
    """Выгрузка только основных разделов сведений (InfoSection с /sveden/ + их InfoFile)."""
    sections = _sveden_sections()
    endpoints = {s.endpoint for s in sections}
    info_files = InfoFile.query.filter(InfoFile.section_endpoint.in_(endpoints)).all() if endpoints else []
    out = {
        "version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "export_type": "sveden",
        "tables": {},
    }
    _, out["tables"][_model_to_tablename(InfoSection)] = _export_model_rows(InfoSection, sections)
    _, out["tables"][_model_to_tablename(InfoFile)] = _export_model_rows(InfoFile, info_files)
    return out


def export_data_sidebar():
    """Выгрузка только разделов бокового меню (InfoSection с /sidebar/ + их InfoFile)."""
    sections = _sidebar_sections()
    endpoints = {s.endpoint for s in sections}
    info_files = InfoFile.query.filter(InfoFile.section_endpoint.in_(endpoints)).all() if endpoints else []
    out = {
        "version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "export_type": "sidebar",
        "tables": {},
    }
    _, out["tables"][_model_to_tablename(InfoSection)] = _export_model_rows(InfoSection, sections)
    _, out["tables"][_model_to_tablename(InfoFile)] = _export_model_rows(InfoFile, info_files)
    return out


def export_data_selective(include_news=False, include_sveden=False, include_sidebar=False,
                         include_page_content=False, include_other_sections=False, include_users=False):
    """
    Выборочная выгрузка: объединяет только выбранные части.
    include_other_sections: разделы, не входящие в /sveden/ и не в /sidebar/ (например /info/about).
    """
    out = {
        "version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "export_type": "selective",
        "tables": {},
    }
    tablename = _model_to_tablename

    if include_news:
        _, out["tables"][tablename(News)] = _export_model_rows(News, News.query.all())
        _, out["tables"][tablename(Announcement)] = _export_model_rows(Announcement, Announcement.query.all())
        files_news = File.query.filter(
            (File.news_id.isnot(None)) | (File.announcement_id.isnot(None))
        ).all()
        _, out["tables"][tablename(File)] = _export_model_rows(File, files_news)

    section_lists = []
    if include_sveden:
        section_lists.append(_sveden_sections())
    if include_sidebar:
        section_lists.append(_sidebar_sections())
    if include_other_sections:
        other = InfoSection.query.filter(
            ~InfoSection.url.startswith(SVEDEN_URL_PREFIX),
            ~InfoSection.url.startswith(SIDEBAR_URL_PREFIX),
        ).all()
        section_lists.append(other)

    if section_lists:
        all_sections = []
        seen_ids = set()
        for lst in section_lists:
            for s in lst:
                if s.id not in seen_ids:
                    seen_ids.add(s.id)
                    all_sections.append(s)
        endpoints = {s.endpoint for s in all_sections}
        info_files = InfoFile.query.filter(InfoFile.section_endpoint.in_(endpoints)).all() if endpoints else []
        _, out["tables"][tablename(InfoSection)] = _export_model_rows(InfoSection, all_sections)
        _, out["tables"][tablename(InfoFile)] = _export_model_rows(InfoFile, info_files)

    if include_page_content:
        _, out["tables"][tablename(PageContent)] = _export_model_rows(PageContent, PageContent.query.all())

    if include_users:
        _, out["tables"][tablename(User)] = _export_model_rows(User, User.query.all())

    return out


def import_data(data, clear_before=True):
    """
    Восстанавливает данные из словаря (результат export_data).
    Если clear_before=True — очищаются таблицы, затем вставляются все записи.
    Если clear_before=False — вставляются только записи с отсутствующим id (существующие пропускаются).
    """
    if not data or not isinstance(data, dict):
        raise ValueError("Некорректные данные для импорта")
    version = data.get("version")
    if version is None or version > EXPORT_VERSION:
        raise ValueError("Неподдерживаемая версия выгрузки")
    tables_data = data.get("tables") or {}

    if clear_before:
        for model in DELETE_ORDER:
            try:
                model.query.delete()
            except Exception:
                db.session.rollback()
                raise
        db.session.commit()

    for model in INSERT_ORDER:
        name = _model_to_tablename(model)
        rows_data = tables_data.get(name)
        if not rows_data or not isinstance(rows_data, list):
            continue
        columns = {c.name: c.type for c in model.__table__.columns}
        pk_columns = [c.name for c in model.__table__.primary_key.columns]
        for row_dict in rows_data:
            if not isinstance(row_dict, dict):
                continue
            if not clear_before and pk_columns:
                pk_vals = [row_dict.get(k) for k in pk_columns]
                if all(v is not None for v in pk_vals):
                    existing = model.query.get(pk_vals[0] if len(pk_vals) == 1 else tuple(pk_vals))
                    if existing is not None:
                        continue
            kwargs = {}
            for col_name, col_type in columns.items():
                if col_name not in row_dict:
                    continue
                kwargs[col_name] = _deserialize_value(row_dict[col_name], col_type)
            try:
                row = model(**kwargs)
                db.session.add(row)
            except Exception:
                db.session.rollback()
                raise
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    return True


def export_preview(uploads_dir):
    """
    Возвращает сводку того, что попадёт в выгрузку: количество записей по таблицам
    и список разделов в uploads с количеством файлов и объёмом.
    uploads_dir — абсолютный путь к static/uploads.
    """
    tables = {}
    for model in INSERT_ORDER:
        name = _model_to_tablename(model)
        tables[name] = model.query.count()
    _MAX_FILES_PER_SECTION = 500
    sections_map = {}
    if os.path.isdir(uploads_dir):
        for root, _dirs, files in os.walk(uploads_dir):
            rel_root = os.path.relpath(root, uploads_dir)
            if rel_root == ".":
                rel_root = ""
            prefix = rel_root.replace("\\", "/")
            for name in files:
                fpath = os.path.join(root, name)
                try:
                    size = os.path.getsize(fpath)
                except OSError:
                    size = 0
                key = prefix if prefix else "(корень)"
                if key not in sections_map:
                    sections_map[key] = {"count": 0, "size": 0, "files": []}
                sections_map[key]["count"] += 1
                sections_map[key]["size"] += size
                rel_path = (prefix + "/" + name) if prefix else name
                if len(sections_map[key]["files"]) < _MAX_FILES_PER_SECTION:
                    sections_map[key]["files"].append({"name": name, "path": rel_path, "size": size})
    section_list = []
    for path_key in sorted(sections_map.keys(), key=lambda x: (x.count("/") if "/" in x else 0, x)):
        sec = sections_map[path_key]
        count = sec["count"]
        size = sec["size"]
        files_list = sec.get("files", [])
        parts = path_key.split("/") if path_key != "(корень)" else []
        endpoint = parts[-1] if parts else ""
        title = None
        if endpoint:
            section = InfoSection.query.filter_by(endpoint=endpoint).first()
            if section:
                title = section.title
        section_list.append({
            "path": path_key,
            "endpoint": endpoint or path_key,
            "title": title,
            "count": count,
            "size": size,
            "files": files_list,
        })
    total_files = sum(s["count"] for s in section_list)
    total_size = sum(s["size"] for s in section_list)
    return {
        "tables": tables,
        "uploads": {
            "total_files": total_files,
            "total_size": total_size,
            "sections": section_list,
        },
    }


def export_full_site(uploads_dir):
    """
    Формирует ZIP-архив «сайт целиком»: все данные БД (JSON) + папка static/uploads.
    uploads_dir — абсолютный путь к папке static/uploads.
    Возвращает путь к временному ZIP-файлу (нужно удалить после отправки).
    Запись в файл вместо BytesIO обеспечивает корректный формат архива при большом объёме.
    """
    fd, path = tempfile.mkstemp(suffix='.zip')
    try:
        os.close(fd)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            data = export_data()
            zf.writestr(
                'data.json',
                json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            )
            if os.path.isdir(uploads_dir):
                for root, _dirs, files in os.walk(uploads_dir, topdown=True, followlinks=True):
                    for name in files:
                        fpath = os.path.join(root, name)
                        try:
                            if not os.path.isfile(fpath):
                                continue
                            arcname = os.path.join('uploads', os.path.relpath(fpath, uploads_dir))
                            arcname = arcname.replace('\\', '/')
                            zf.write(fpath, arcname)
                        except (OSError, zipfile.LargeZipFile):
                            pass
            for info_file in InfoFile.query.all():
                if not getattr(info_file, 'stored_in_db', False) or not getattr(info_file, 'file_data', None):
                    continue
                try:
                    year = (info_file.upload_date or datetime.utcnow()).strftime('%Y')
                    arcname = f"uploads/info/{year}/{info_file.section_endpoint}/{info_file.filename}"
                    arcname = arcname.replace('\\', '/')
                    zf.writestr(arcname, bytes(info_file.file_data))
                except (AttributeError, TypeError, zipfile.LargeZipFile):
                    pass
        return path
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


def import_full_site(zip_bytes, uploads_dir, clear_before=True):
    """
    Восстанавливает сайт из ZIP: импортирует data.json в БД и распаковывает uploads/ в uploads_dir.
    При clear_before=False в БД добавляются только записи с новым id; существующие файлы в uploads перезаписываются.
    zip_bytes — bytes или file-like с ZIP.
    uploads_dir — абсолютный путь к папке static/uploads.
    """
    with zipfile.ZipFile(BytesIO(zip_bytes) if isinstance(zip_bytes, bytes) else zip_bytes, 'r') as zf:
        names = zf.namelist()
        if 'data.json' not in names:
            raise ValueError("В архиве нет data.json")
        data = json.loads(zf.read('data.json').decode('utf-8'))
        import_data(data, clear_before=clear_before)
        os.makedirs(uploads_dir, exist_ok=True)
        for name in names:
            if name.startswith('uploads/') and not name.endswith('/'):
                try:
                    target = os.path.join(uploads_dir, os.path.relpath(name, 'uploads'))
                    target = os.path.normpath(target)
                    if not target.startswith(os.path.abspath(uploads_dir)):
                        continue
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with open(target, 'wb') as f:
                        f.write(zf.read(name))
                except (OSError, zipfile.BadZipFile):
                    pass
