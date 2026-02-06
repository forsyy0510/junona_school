import sys
import os

# Добавляем текущую директорию в путь импорта
sys.path.append(os.getcwd())

def test_config_loading():
    print("Testing config loading...")
    try:
        from config import config, DevelopmentConfig, ProductionConfig
        assert isinstance(config, DevelopmentConfig), "Default config should be DevelopmentConfig"
        print("Config loading passed.")
    except Exception as e:
        print(f"Config loading failed: {e}")
        sys.exit(1)

def test_app_creation():
    print("Testing app creation...")
    try:
        from app import create_app
        app = create_app()
        assert app is not None, "App instance should not be None"
        print("App creation passed.")
    except Exception as e:
        print(f"App creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_file_manager_import():
    print("Testing FileManager import...")
    try:
        from file_manager import FileManager
        fm = FileManager()
        assert hasattr(fm, 'get_section_files_from_db'), "FileManager missing get_section_files_from_db"
        print("FileManager import passed.")
    except Exception as e:
        print(f"FileManager import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_config_loading()
    test_file_manager_import()
    # App creation requires database which might not be initialized or might need context
    # We will try it last
    try:
        test_app_creation()
        print("ALL TESTS PASSED")
    except ImportError:
         print("Skipping app creation test due to missing dependencies in environment")
