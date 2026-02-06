# Аудит: загрузка, удаление, хранение и отображение файлов

## 1. Загрузка файлов

### Эндпоинты
- **`POST /info/upload_file`** — загрузка в разделы Сведения (мастер заполнения, поля `file_with_name`, `file`).
- **`POST /info/upload_main_file`** — загрузка в раздел «Главная» (список файлов).
- **`POST /sidebar/upload_file`** — загрузка в боковые разделы.

### Процесс (info)
1. **Клиент** (`templates/base.html`):
   - Мастер: `handleFileWithName(event, fieldName)` — отправляет `FormData` с `file`, `section` (step.endpoint || step.id), `field_name`.
   - Поле `file`: `uploadFiles(files, fieldName, stepId)` — то же для полей типа `file`.
2. **Сервер** (`info/routes.py`, `upload_file`):
   - Проверка: файл в запросе, размер (MAX_CONTENT_LENGTH), расширение (allowed_ext).
   - Раздел: `InfoSection` по `section` (endpoint); при отсутствии создаётся с пустым `form_data`.
   - Сохранение на диск: `file_manager.save_info_file(file, section, field_name)` → путь `static/uploads/info/ГОД/РАЗДЕЛ/` (для Сведений).
   - Запись в БД: `InfoFile` (filename, original_filename, file_path, section_endpoint, field_name, display_name, при необходимости file_data/stored_in_db).
   - Обновление form_data: в `section.text` (JSON) в `form_data[field_name]` записывается строка `url|displayName` (одиночный файл) или дополняется список через запятую.

### Форматы в form_data после загрузки через upload_file
- Один файл в поле: **строка** `"/info/download_file/education/имя.pdf|Отображаемое имя.pdf"`.
- Несколько (через запятую): строка с перечислением таких же `url|displayName`.

### Важно для мастера
- При открытии мастера данные приходят из `GET /info/section/{endpoint}`; в form_data поле может быть **строкой** (если файл добавлен через upload_file и раздел ещё не сохраняли из мастера).
- В мастере для полей `file_with_name` значение теперь нормализуется: если пришла строка вида `url|displayName`, она парсится в массив из одного объекта `[{ url, displayName, filename }]`, чтобы файл отображался в списке и корректно удалялся.

---

## 2. Удаление файлов

### Эндпоинты
- **`POST /info/delete_file`** — удаление файла раздела Сведения (JSON: `filename`, `section`, `field_name`).
- **`POST /info/delete_main_file`** — удаление из раздела «Главная».
- **`POST /sidebar/delete_file`** — удаление в боковых разделах.

### Процесс (info delete_file)
1. **Клиент** (`base.html`):
   - `removeFileWithNameMulti(fieldName, index)` — для полей `file_with_name`. Имя файла берётся из `fileData.filename` или из `fileData.url` (последний сегмент пути), затем отправляется запрос, из локального массива элемент удаляется, UI обновляется через `updateFileWithNameUI`.
   - `removeFileWithName(fieldName)` — для одиночного file_with_name; та же логика имени файла.
   - `removeFile(fieldName, index)` — для полей типа `file` (список URL).
2. **Сервер** (`info/routes.py`, `delete_file`):
   - Проверка наличия `filename` и `section`.
   - `file_manager.delete_file(filename, section, field_name)`.

### FileManager.delete_file (`file_manager.py`)
- Поиск в БД: `InfoFile` по filename, section_endpoint, при необходимости по field_name. Если запись есть — удаление с диска (если не stored_in_db) и удаление записи из БД.
- Если в БД нет: поиск файла в `static/uploads/info/` (обход дерева), затем в путях `uploads/section_name/`, `uploads/pages/section_name/`, для food — `uploads/nutrition/menus/`, при необходимости глобальный обход `base_upload_path`. Файл удаляется с диска.
- Обновление form_data: в `section.text` из поля `form_data[field_name]` (строка с URL через запятую) удаляются вхождения данного filename; для раздела main — из списка `form_data['files']`. Изменённый JSON сохраняется в `section.text`.

---

## 3. Хранение

### Файловая система
- **Сведения (info):** `static/uploads/info/ГОД/РАЗДЕЛ/` (например, `.../info/2026/education/`). Имена файлов — с поддержкой кириллицы (`_safe_filename_preserve_unicode`), при коллизии добавляется суффикс `_1`, `_2` и т.д. (кроме специальных полей вроде `menu_file`).
- **Обычные разделы:** `static/uploads/РАЗДЕЛ/` или `static/uploads/pages/РАЗДЕЛ/`.
- **Меню питания:** при `field_name == 'menu_file'` файл может сохраняться в подпапке food с перезаписью по имени.

### База данных
- **InfoSection:** поле `text` — JSON с ключами `form_data`, `text`, при необходимости `content_blocks`. В `form_data` файловые поля хранятся как:
  - **строка:** `"url|displayName"` или несколько через запятую (после upload_file или после старых сценариев);
  - **массив объектов:** `[{ "url": "...", "displayName": "...", "filename": "..." }]` — после сохранения раздела из мастера с полями file_with_name.
- **InfoFile** (если используется): filename, section_endpoint, field_name, file_path, original_filename, display_name, file_data/stored_in_db и т.д. — для выдачи корректного имени при скачивании и для удаления.

---

## 4. Отображение

### На странице раздела (`templates/info/section.html`)
- Макрос **`render_field_content(field_name, field_label, field_value, section_endpoint)`**:
  - массив объектов (file_with_name): цикл по объектам, ссылка через `filename | info_file_url(section_endpoint)`, подпись — displayName/originalName/filename;
  - один объект (mapping) с `url`: одна ссылка;
  - строка: поддержка нескольких URL через запятую и формата `url|displayName`; для одного файла — разбор `url` и `displayName` из строки;
  - одиночный URL (начинается с `/download_file/`, `/info/download_file/`, `/static/uploads/`) — одна ссылка «Скачать …».
- Ссылки на файлы формируются фильтром **`info_file_url(filename, section_endpoint)`** (`app.py`) → `/info/download_file/{section_endpoint}/{filename}`.

### Скачивание (`info/routes.py`, `download_file`)
- Маршруты: `/info/download_file/<section>/<filename>`, `/download_file/<section>/<filename>`.
- Сначала поиск в БД (InfoFile) по filename и section — для получения оригинального/отображаемого имени и, при необходимости, содержимого из БД.
- Затем поиск файла на диске: в `static/uploads/info/` (по году и разделу), в `static/uploads/section/`, `static/uploads/pages/section/`. При нахождении — отправка через `send_file` с безопасным именем в Content-Disposition (поддержка кириллицы).

---

## 5. Внесённые исправления (в рамках аудита)

1. **Удаление в мастере для file_with_name:** имя файла для запроса delete берётся из `fileData.filename` или из `fileData.url` (последний сегмент), чтобы удаление работало и когда с сервера приходит только `url`/`displayName` без `filename`.
2. **Отображение в мастере при строковом значении:** для полей `file_with_name` значение из form_data в формате строки `url|displayName` парсится в массив из одного объекта, чтобы файл показывался в списке и кнопка «×» работала.
3. **Безопасность отображения имён:** при выводе имён файлов в мастере (список file_with_name и в `updateFileWithNameUI`) экранируются символы `&`, `<`, `>`, `"` во избежание XSS и поломки HTML.

---

## 6. Рекомендации

- При сохранении раздела из мастера поля file_with_name приходят массивом объектов; бэкенд сохраняет их в form_data как JSON-массив — это корректно и поддерживается `render_field_content` и загрузкой мастера (в т.ч. после парсинга строки в массив).
- Не удалять логику парсинга строки `url|displayName` для file_with_name в мастере: после первой загрузки через upload_file в form_data остаётся строка до первого сохранения из мастера.
- Периодически проверять очистку несуществующих файлов из form_data (существующие вызовы `_clean_nonexistent_files_from_form_data` и обновление имён через `_update_form_data_file_names`).
