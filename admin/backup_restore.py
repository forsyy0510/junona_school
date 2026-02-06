"""
Резервное копирование: выгрузка и загрузка папок instance, static/uploads и uploads (корень).
ZIP содержит: instance/, static_uploads/ (содержимое static/uploads), uploads/ (корневая uploads).
"""

import os
import shutil
import tempfile
import zipfile
from io import BytesIO


def _safe_join(base_path, rel_path):
    """Проверяет, что результирующий путь внутри base_path (защита от path traversal)."""
    if not rel_path:
        return None
    rel_path = rel_path.replace("\\", os.sep).lstrip(os.sep)
    if ".." in os.path.normpath(rel_path).split(os.sep):
        return None
    base = os.path.abspath(base_path)
    target = os.path.abspath(os.path.join(base_path, rel_path))
    return target if target.startswith(base) else None


def _folder_summary(folder_path, label):
    """Сводка по одной папке: список файлов или подпапок с count/size."""
    files_list = []
    sections = []
    total_files = 0
    total_size = 0
    if not os.path.isdir(folder_path):
        return {"files": files_list, "total_files": 0, "total_size": 0, "sections": []}
    if label == "instance":
        for name in os.listdir(folder_path):
            fpath = os.path.join(folder_path, name)
            if os.path.isfile(fpath):
                try:
                    files_list.append({"name": name, "size": os.path.getsize(fpath)})
                except OSError:
                    files_list.append({"name": name, "size": 0})
        return {"files": files_list, "total_files": len(files_list), "total_size": sum(f.get("size", 0) for f in files_list), "sections": []}
    for root, _dirs, files in os.walk(folder_path):
        rel_root = os.path.relpath(root, folder_path)
        if rel_root == ".":
            rel_root = ""
        prefix = rel_root.replace("\\", "/")
        count = 0
        size = 0
        for name in files:
            fpath = os.path.join(root, name)
            if os.path.isfile(fpath):
                try:
                    size += os.path.getsize(fpath)
                except OSError:
                    pass
                count += 1
        if count > 0:
            sections.append({"path": prefix or "(корень)", "count": count, "size": size})
            total_files += count
            total_size += size
    return {"files": [], "total_files": total_files, "total_size": total_size, "sections": sections}


def preview_folders_backup(instance_path, static_uploads_path, uploads_root_path):
    """
    Возвращает сводку для предпросмотра: instance, static/uploads, uploads (корень).
    """
    return {
        "instance": _folder_summary(instance_path, "instance"),
        "static_uploads": _folder_summary(static_uploads_path, "uploads"),
        "uploads_root": _folder_summary(uploads_root_path, "uploads"),
    }


def _add_folder_to_zip(zf, folder_path, zip_prefix):
    """Добавляет содержимое папки в ZIP с префиксом zip_prefix."""
    if not os.path.isdir(folder_path):
        return
    for root, _dirs, files in os.walk(folder_path, topdown=True, followlinks=True):
        for name in files:
            fpath = os.path.join(root, name)
            if not os.path.isfile(fpath):
                continue
            arcname = os.path.join(zip_prefix, os.path.relpath(fpath, folder_path))
            arcname = arcname.replace("\\", "/")
            try:
                zf.write(fpath, arcname)
            except (OSError, zipfile.LargeZipFile):
                pass


def export_folders_backup(instance_path, static_uploads_path, uploads_root_path):
    """
    Создаёт ZIP с instance/, static_uploads/ (static/uploads), uploads/ (корневая uploads).
    Возвращает путь к временному ZIP-файлу (удалить после отправки).
    """
    fd, path = tempfile.mkstemp(suffix=".zip")
    try:
        os.close(fd)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            _add_folder_to_zip(zf, instance_path, "instance")
            _add_folder_to_zip(zf, static_uploads_path, "static_uploads")
            _add_folder_to_zip(zf, uploads_root_path, "uploads")
        return path
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


def import_folders_backup(zip_bytes, instance_path, static_uploads_path, uploads_root_path, clear_before=True):
    """
    Восстанавливает из ZIP: instance/ -> instance_path, static_uploads/ -> static_uploads_path, uploads/ -> uploads_root_path.
    """
    if not zip_bytes:
        raise ValueError("Файл архива не передан")
    zf = zipfile.ZipFile(
        BytesIO(zip_bytes) if isinstance(zip_bytes, bytes) else zip_bytes,
        "r",
    )
    names = zf.namelist()
    has_instance = any(n.startswith("instance/") and not n.endswith("/") for n in names)
    has_static_uploads = any(n.startswith("static_uploads/") and not n.endswith("/") for n in names)
    has_uploads = any(n.startswith("uploads/") and not n.endswith("/") for n in names)
    if not has_instance and not has_static_uploads and not has_uploads:
        raise ValueError("В архиве нет каталогов instance/, static_uploads/ или uploads/")
    # Старый формат: только uploads/ (содержимое static/uploads) — распаковываем в static_uploads_path
    uploads_means_static = has_uploads and not has_static_uploads

    instance_abs = os.path.abspath(instance_path)
    static_uploads_abs = os.path.abspath(static_uploads_path)
    uploads_root_abs = os.path.abspath(uploads_root_path)

    def clear_dir(d):
        if not os.path.isdir(d):
            return
        for name in os.listdir(d):
            p = os.path.join(d, name)
            try:
                if os.path.isfile(p):
                    os.unlink(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
            except OSError:
                pass

    if clear_before:
        clear_dir(instance_path)
        clear_dir(static_uploads_path)
        clear_dir(uploads_root_path)

    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(static_uploads_path, exist_ok=True)
    os.makedirs(uploads_root_path, exist_ok=True)

    for name in names:
        if name.endswith("/"):
            continue
        if name.startswith("instance/"):
            rel = name[len("instance/"):].lstrip("/")
            if not rel:
                continue
            target = _safe_join(instance_path, rel)
            if not target or not target.startswith(instance_abs):
                continue
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(zf.read(name))
            except (OSError, zipfile.BadZipFile):
                pass
        elif name.startswith("static_uploads/"):
            rel = name[len("static_uploads/"):].lstrip("/")
            if not rel:
                continue
            target = _safe_join(static_uploads_path, rel)
            if not target or not target.startswith(static_uploads_abs):
                continue
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(zf.read(name))
            except (OSError, zipfile.BadZipFile):
                pass
        elif name.startswith("uploads/"):
            rel = name[len("uploads/"):].lstrip("/")
            if not rel:
                continue
            dest = static_uploads_path if uploads_means_static else uploads_root_path
            dest_abs = static_uploads_abs if uploads_means_static else uploads_root_abs
            target = _safe_join(dest, rel)
            if not target or not target.startswith(dest_abs):
                continue
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(zf.read(name))
            except (OSError, zipfile.BadZipFile):
                pass
