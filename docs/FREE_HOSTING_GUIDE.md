# Руководство по размещению на бесплатных хостингах

## 🏆 Рекомендация: Render.com

### Преимущества:
- ✅ Бесплатный tier с PostgreSQL
- ✅ Автоматический деплой из GitHub
- ✅ Бесплатный SSL сертификат
- ✅ Простая настройка
- ✅ Поддержка переменных окружения

### Недостатки:
- ⚠️ Приложение засыпает после 15 минут бездействия (первый запрос может быть медленным)
- ⚠️ Ограниченные ресурсы на бесплатном плане

### Инструкция по деплою на Render:

1. **Подготовка проекта:**

   Создайте файл `render.yaml` в корне проекта:
   ```yaml
   services:
     - type: web
       name: site-junona
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: gunicorn app:app
       envVars:
         - key: SECRET_KEY
           generateValue: true
         - key: DATABASE_URL
           fromDatabase:
             name: site-junona-db
             property: connectionString
       databases:
         - name: site-junona-db
           plan: free
   ```

2. **Создайте файл `Procfile`:**
   ```
   web: gunicorn app:app
   ```

3. **Обновите `requirements.txt`:**
   ```
   Flask>=2.2.0
   Flask-Login>=0.6.0
   Flask-WTF>=1.0.0
   WTForms>=3.0.0
   Flask-SQLAlchemy>=3.0.0
   Werkzeug>=2.2.0
   Jinja2>=3.1.0
   itsdangerous>=2.1.0
   click>=8.1.0
   Pillow>=9.0.0
   requests>=2.28.0
   gunicorn>=20.1.0
   psycopg2-binary>=2.9.0
   ```

4. **Обновите `config.py` для поддержки PostgreSQL:**
   ```python
   import os
   
   class Config:
       SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
       # Поддержка PostgreSQL от Render
       database_url = os.environ.get('DATABASE_URL')
       if database_url and database_url.startswith('postgres://'):
           database_url = database_url.replace('postgres://', 'postgresql://', 1)
       SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///site.db'
       SQLALCHEMY_TRACK_MODIFICATIONS = False
       # ... остальные настройки
   ```

5. **Деплой:**
   - Зарегистрируйтесь на [render.com](https://render.com)
   - Подключите репозиторий GitHub
   - Создайте новый Web Service
   - Выберите репозиторий
   - Render автоматически определит настройки из `render.yaml`
   - Добавьте PostgreSQL базу данных
   - Дождитесь завершения деплоя

---

## 🚂 Railway.app

### Преимущества:
- ✅ Очень простой деплой
- ✅ Автоматическое определение Python приложений
- ✅ PostgreSQL в один клик
- ✅ $5 бесплатных кредитов в месяц

### Инструкция:

1. **Создайте файл `Procfile`:**
   ```
   web: gunicorn app:app
   ```

2. **Добавьте в `requirements.txt`:**
   ```
   gunicorn>=20.1.0
   psycopg2-binary>=2.9.0
   ```

3. **Деплой:**
   - Зарегистрируйтесь на [railway.app](https://railway.app)
   - Нажмите "New Project" → "Deploy from GitHub repo"
   - Выберите репозиторий
   - Railway автоматически определит Flask приложение
   - Добавьте PostgreSQL базу данных
   - Настройте переменные окружения:
     - `SECRET_KEY` (сгенерируйте случайный ключ)
     - `DATABASE_URL` (автоматически из PostgreSQL)

---

## ✈️ Fly.io

### Преимущества:
- ✅ Глобальная сеть (быстрая загрузка)
- ✅ Хорошая производительность
- ✅ PostgreSQL доступен

### Инструкция:

1. **Установите Fly CLI:**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Создайте `fly.toml`:**
   ```toml
   app = "site-junona"
   primary_region = "iad"
   
   [build]
   
   [env]
     PORT = "8080"
     SECRET_KEY = "your-secret-key-here"
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   
     [[services.ports]]
       port = 80
       handlers = ["http"]
       force_https = true
   
     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
   ```

3. **Деплой:**
   ```bash
   fly auth login
   fly launch
   fly postgres create
   fly secrets set SECRET_KEY=your-secret-key
   fly deploy
   ```

---

## 🐍 PythonAnywhere

### Преимущества:
- ✅ Работает с SQLite (ваша текущая БД)
- ✅ Веб-интерфейс для управления
- ✅ Простая настройка

### Недостатки:
- ⚠️ Только 1 веб-приложение на бесплатном аккаунте
- ⚠️ Ограниченный трафик
- ⚠️ Требуется подтверждение email для внешних доменов

### Инструкция:

1. **Зарегистрируйтесь на [pythonanywhere.com](https://www.pythonanywhere.com)**

2. **Загрузите проект:**
   - Используйте встроенный файловый менеджер
   - Или загрузите через Git

3. **Настройте Web App:**
   - Перейдите в раздел "Web"
   - Нажмите "Add a new web app"
   - Выберите Flask
   - Укажите путь к `app.py`
   - Настройте WSGI файл

4. **Настройте переменные окружения:**
   - В разделе "Web" → "Environment variables"
   - Добавьте `SECRET_KEY`

5. **Перезагрузите приложение**

---

## 🔧 Общие рекомендации для всех платформ

### 1. Обновите `config.py` для production:

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Поддержка PostgreSQL (для Render, Railway, Fly.io)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Исправление для старых форматов PostgreSQL URL
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Fallback на SQLite для локальной разработки
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'site.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 64 * 1024 * 1024))
    
    # Production настройки
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
```

### 2. Создайте `runtime.txt` (для указания версии Python):

```
python-3.11.0
```

### 3. Создайте `.gitignore` (если еще нет):

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
instance/
*.db
.env
.venv/
venv/
ENV/
uploads/
*.log
```

### 4. Миграция с SQLite на PostgreSQL (если нужно):

Если вы переходите на PostgreSQL, создайте скрипт миграции:

```python
# migrate_to_postgres.py
from app import app, db
from models.models import *
import sqlite3

def migrate():
    with app.app_context():
        # Подключение к SQLite
        sqlite_conn = sqlite3.connect('instance/site.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Здесь добавьте логику миграции данных
        # ...
        
        print("Миграция завершена")
```

---

## 📊 Сравнительная таблица

| Платформа | Бесплатный tier | PostgreSQL | SSL | Автодеплой | Рекомендация |
|-----------|----------------|------------|-----|------------|--------------|
| **Render** | ✅ Да | ✅ Да | ✅ Да | ✅ Да | ⭐⭐⭐⭐⭐ |
| **Railway** | ✅ $5/мес | ✅ Да | ✅ Да | ✅ Да | ⭐⭐⭐⭐ |
| **Fly.io** | ✅ Да | ✅ Да | ✅ Да | ✅ Да | ⭐⭐⭐⭐ |
| **PythonAnywhere** | ✅ Да | ❌ Нет | ✅ Да | ❌ Нет | ⭐⭐⭐ |
| **Replit** | ✅ Да | ❌ Нет | ✅ Да | ✅ Да | ⭐⭐ |

---

## 🎯 Итоговая рекомендация

**Для начала:** Используйте **Render.com** — самый простой и надежный вариант для Flask приложений.

**Для production:** Рассмотрите **Fly.io** или **Railway** для лучшей производительности.

**Для обучения:** **PythonAnywhere** отлично подходит, если нужна работа с SQLite без изменений.

---

## 📝 Чеклист перед деплоем

- [ ] Обновлен `config.py` для поддержки PostgreSQL
- [ ] Добавлен `gunicorn` в `requirements.txt`
- [ ] Создан `Procfile`
- [ ] Настроены переменные окружения (`SECRET_KEY`)
- [ ] Обновлен `.gitignore`
- [ ] Протестировано локально
- [ ] Создана резервная копия базы данных
- [ ] Настроен домен (опционально)

---

## 🔗 Полезные ссылки

- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Fly.io Documentation](https://fly.io/docs)
- [PythonAnywhere Help](https://help.pythonanywhere.com)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)

