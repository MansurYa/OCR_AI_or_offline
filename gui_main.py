"""
GUI точка входа для приложения OCR AI or Offline.
Запускает графический интерфейс пользователя.
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Добавляем src в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"Ошибка импорта GUI компонентов: {e}")
    print("Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
    sys.exit(1)


def setup_logging() -> None:
    """Настраивает систему логирования для GUI приложения."""
    # Создаем директорию для логов если не существует
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "ocr_gui.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Устанавливаем уровень логирования для различных модулей
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def check_dependencies() -> bool:
    """
    Проверяет наличие необходимых зависимостей.

    :return: True если все зависимости доступны
    """
    missing_dependencies = []

    # Проверяем основные зависимости
    try:
        import tkinter
    except ImportError:
        missing_dependencies.append("tkinter (обычно встроен в Python)")

    try:
        import PIL
    except ImportError:
        missing_dependencies.append("Pillow")

    try:
        import requests
    except ImportError:
        missing_dependencies.append("requests")

    # Проверяем опциональные зависимости
    optional_missing = []

    try:
        import tkinterdnd2
    except ImportError:
        optional_missing.append("tkinterdnd2 (для drag & drop функциональности)")

    try:
        import pytesseract
    except ImportError:
        optional_missing.append("pytesseract (для offline OCR)")

    # Сообщаем о результатах
    if missing_dependencies:
        print("❌ Отсутствуют критические зависимости:")
        for dep in missing_dependencies:
            print(f"  - {dep}")
        print("\nУстановите зависимости: pip install -r requirements.txt")
        return False

    if optional_missing:
        print("⚠️ Отсутствуют опциональные зависимости:")
        for dep in optional_missing:
            print(f"  - {dep}")
        print("Некоторые функции могут быть недоступны\n")

    return True


def check_config() -> bool:
    """
    Проверяет наличие и корректность конфигурационного файла.

    :return: True если конфигурация корректна
    """
    config_path = Path("config.json")

    if not config_path.exists():
        print("⚠️ Файл config.json не найден. Будет создан с настройками по умолчанию.")
        return True  # Приложение создаст конфигурацию автоматически

    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Проверяем обязательные ключи
        required_keys = ['ocr_settings', 'gui_settings']
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            print(f"⚠️ В config.json отсутствуют ключи: {missing_keys}")
            print("Будут использованы значения по умолчанию.")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате config.json: {e}")
        print("Исправьте JSON файл или удалите его для создания нового.")
        return False
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return False


def create_default_directories() -> None:
    """Создает необходимые директории если они не существуют."""
    directories = [
        "OCR_prompts",
        "logs",
        "temp"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def main() -> int:
    """
    Главная функция GUI приложения.

    :return: Код выхода (0 - успех, 1 - ошибка)
    """
    print("🔍 OCR AI or Offline - Запуск GUI приложения")
    print("=" * 50)

    # Проверяем зависимости
    print("Проверка зависимостей...")
    if not check_dependencies():
        return 1

    # Проверяем конфигурацию
    print("Проверка конфигурации...")
    if not check_config():
        return 1

    # Создаем необходимые директории
    print("Создание директорий...")
    create_default_directories()

    # Настраиваем логирование
    print("Настройка логирования...")
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Запуск GUI приложения OCR AI or Offline")

    try:
        print("Инициализация GUI...")

        # Создаем и запускаем главное окно
        app = MainWindow()

        print("✅ GUI успешно инициализирован")
        print("Приложение готово к работе!")
        print("-" * 50)

        # Запускаем главный цикл
        app.run()

        logger.info("GUI приложение завершено успешно")
        return 0

    except KeyboardInterrupt:
        print("\n🛑 Приложение остановлено пользователем")
        logger.info("Приложение остановлено пользователем (Ctrl+C)")
        return 0

    except Exception as e:
        error_message = f"Критическая ошибка: {e}"
        print(f"❌ {error_message}")

        logger.error(f"Критическая ошибка в GUI приложении: {e}")
        logger.error(f"Трассировка:\n{traceback.format_exc()}")

        # Пытаемся показать диалог ошибки если tkinter доступен
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()  # Скрываем основное окно

            messagebox.showerror(
                "Критическая ошибка",
                f"Произошла критическая ошибка при запуске приложения:\n\n{e}\n\n"
                f"Подробности сохранены в файле logs/ocr_gui.log"
            )

            root.destroy()

        except Exception:
            pass  # Если не удается показать диалог, просто продолжаем

        return 1


if __name__ == "__main__":
    # Проверяем версию Python
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или новее")
        print(f"Текущая версия: {sys.version}")
        sys.exit(1)

    # Запускаем приложение
    exit_code = main()
    sys.exit(exit_code)
