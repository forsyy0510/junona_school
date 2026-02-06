"""
Резервное копирование: выгрузка и загрузка папок instance (БД) и static/uploads (загрузки).
Один формат — ZIP с каталогами instance/ и uploads/.
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


def preview_folders_backup(instance_path, uploads_path):
    """
    Возвращает сводку для предпросмотра: что попадёт в выгрузку.
    - instance: список файлов с размерами (например site.db)
    - uploads: количество файлов и объём по подпапкам.
    """
    instance_files = []
    if os.path.isdir(instance_path):
        for name in os.listdir(instance_path):
            fpath = os.path.join(instance_path, name)
            if os.path.isfile(fpath):
                try:
                    instance_files.append({"name": name, "size": os.path.getsize(fpath)})
                except OSError:
                    instance_files.append({"name": name, "size": 0})

    uploads_sections = []
    total_files = 0
    total_size = 0
    if os.path.isdir(uploads_path):
        for root, _dirs, files in os.walk(uploads_path):
            rel_root = os.path.relpath(root, uploads_path)
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
                uploads_sections.append({"path": prefix or "(корень)", "count": count, "size": size})
                total_files += count
                total_size += size

    return {
        "instance": {"files": instance_files},
        "uploads": {
            "total_files": total_files,
            "total_size": total_size,
            "sections": uploads_sections,
        },
    }


def export_folders_backup(instance_path, uploads_path):
    """
    Создаёт ZIP-архив с содержимым instance/ и uploads/.
    Возвращает путь к временному ZIP-файлу (нужно удалить после отправки).
    """
    fd, path = tempfile.mkstemp(suffix=".zip")
    try:
        os.close(fd)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(instance_path):
                for root, _dirs, files in os.walk(instance_path):
                    for name in files:
                        fpath = os.path.join(root, name)
                        if not os.path.isfile(fpath):
                            continue
                        arcname = os.path.join("instance", os.path.relpath(fpath, instance_path))
                        arcname = arcname.replace("\\", "/")
                        try:
                            zf.write(fpath, arcname)
                        except (OSError, zipfile.LargeZipFile):
                            pass
            if os.path.isdir(uploads_path):
                for root, _dirs, files in os.walk(uploads_path, topdown=True, followlinks=True):
                    for name in files:
                        fpath = os.path.join(root, name)
                        if not os.path.isfile(fpath):
                            continue
                        arcname = os.path.join("uploads", os.path.relpath(fpath, uploads_path))
                        arcname = arcname.replace("\\", "/")
                        try:
                            zf.write(fpath, arcname)
                        except (OSError, zipfile.LargeZipFile):
                            pass
        return path
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


def import_folders_backup(zip_bytes, instance_path, uploads_path, clear_before=True):
    """
    Восстанавливает из ZIP: распаковывает instance/ в instance_path и uploads/ в uploads_path.
    zip_bytes — bytes или file-like с ZIP.
    Если clear_before=True, перед распаковкой очищаются целевые каталоги.
    """
    if not zip_bytes:
        raise ValueError("Файл архива не передан")
    zf = zipfile.ZipFile(
        BytesIO(zip_bytes) if isinstance(zip_bytes, bytes) else zip_bytes,
        "r",
    )
    names = zf.namelist()
    has_instance = any(n.startswith("instance/") and not n.endswith("/") for n in names)
    has_uploads = any(n.startswith("uploads/") and not n.endswith("/") for n in names)
    if not has_instance and not has_uploads:
        raise ValueError("В архиве нет каталогов instance/ или uploads/")

    instance_abs = os.path.abspath(instance_path)
    uploads_abs = os.path.abspath(uploads_path)

    if clear_before:
        if os.path.isdir(instance_path):
            for name in os.listdir(instance_path):
                p = os.path.join(instance_path, name)
                try:
                    if os.path.isfile(p):
                        os.unlink(p)
                    elif os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                except OSError:
                    pass
        if os.path.isdir(uploads_path):
            for name in os.listdir(uploads_path):
                p = os.path.join(uploads_path, name)
                try:
                    if os.path.isfile(p):
                        os.unlink(p)
                    elif os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                except OSError:
                    pass

    os.makedirs(instance_path, exist_ok=True)
    os.makedirs(uploads_path, exist_ok=True)

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
        elif name.startswith("uploads/"):
            rel = name[len("uploads/"):].lstrip("/")
            if not rel:
                continue
            target = _safe_join(uploads_path, rel)
            if not target or not target.startswith(uploads_abs):
                continue
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(zf.read(name))
            except (OSError, zipfile.BadZipFile):
                pass
