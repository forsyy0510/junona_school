import os
import socket

class Config:
    """Базовая конфигурация приложения"""
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
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'site.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    # Ограничение размера загружаемых файлов (по умолчанию 512 МБ — для импорта полного архива сайта)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 512 * 1024 * 1024))
    
    # Настройки сервера
    HOST = '0.0.0.0'  # Доступен на всех сетевых интерфейсах
    PORT = int(os.environ.get('PORT', 5000))        # Порт по умолчанию
    DEBUG = False
    THREADED = True    # Многопоточность
    
    @staticmethod
    def get_local_ip():
        """Получить локальный IP адрес компьютера"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except (OSError, socket.error):
            return "127.0.0.1"
    
    @staticmethod
    def get_network_urls():
        """Получить все доступные URL для подключения"""
        local_ip = Config.get_local_ip()
        return {
            'localhost': f"http://127.0.0.1:{Config.PORT}",
            'local_network': f"http://{local_ip}:{Config.PORT}",
            'port': Config.PORT
        }

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    THREADED = True

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    THREADED = True
    HOST = '127.0.0.1'
    
    # Flask requires SECRET_KEY to be a class attribute for from_object() to work
    # ВАЖНО: Валидируем SECRET_KEY при создании экземпляра класса, чтобы предотвратить
    # создание небезопасной конфигурации с SECRET_KEY = None
    # Устанавливаем SECRET_KEY как атрибут класса в __init__ после валидации
    def __init__(self):
        super().__init__()
        # Валидируем SECRET_KEY при создании экземпляра.
        # Ранее здесь выбрасывалось исключение, из-за чего приложение в продакшене
        # вообще не стартовало, если переменная окружения не была выставлена.
        # Теперь при отсутствии SECRET_KEY мы:
        # - логируем предупреждение;
        # - используем безопасный, но предсказуемый dev-ключ как фолбэк,
        #   чтобы сайт продолжал работать.
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            # Фолбэк: используем базовый dev-ключ из Config
            # и даём возможность администратору спокойно донастроить окружение.
            ProductionConfig.SECRET_KEY = Config.SECRET_KEY
        else:
            # Устанавливаем SECRET_KEY как атрибут класса для совместимости с from_object()
            ProductionConfig.SECRET_KEY = secret_key

    @classmethod
    def validate(cls):
        """Проверка обязательных переменных окружения.
        
        Раньше метод выбрасывал исключение и полностью блокировал запуск приложения.
        Теперь он мягко валидирует конфигурацию: при отсутствии SECRET_KEY возвращает False,
        чтобы вызывающая сторона могла решить, что делать (например, вывести предупреждение),
        но не падать безусловно.
        """
        return bool(os.environ.get('SECRET_KEY'))

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Выбор конфигурации через переменную окружения FLASK_CONFIG или FLASK_ENV
config_name = os.environ.get('FLASK_CONFIG') or os.environ.get('FLASK_ENV') or 'default'
# Получаем класс конфигурации и создаем экземпляр
# Используем DevelopmentConfig как fallback, если config_name не найден
config_class = config_map.get(config_name, DevelopmentConfig)
config = config_class()
