"""
CLI точка входа для приложения OCR AI or Offline.
Обеспечивает работу через командную строку без GUI.
"""

import sys
import os
import argparse
import logging
import json
from pathlib import Path
from typing import List, Optional

# Добавляем src в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.ocr_processor import OCRProcessor
    from core.image_sorter import ImageSorter
except ImportError as e:
    print(f"Ошибка импорта core компонентов: {e}")
    print("Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
    sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """
    Настраивает систему логирования для CLI приложения.

    :param verbose: Включить подробный вывод
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Устанавливаем уровень для внешних библиотек
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def load_config(config_path: str) -> dict:
    """
    Загружает конфигурацию из файла.

    :param config_path: Путь к файлу конфигурации
    :return: Словарь с конфигурацией
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Файл конфигурации не найден: {config_path}")
        print("Используем настройки по умолчанию")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате конфигурации: {e}")
        sys.exit(1)


def find_images(input_path: str, recursive: bool = False) -> List[str]:
    """
    Находит изображения в указанной директории или возвращает файл.

    :param input_path: Путь к файлу или директории
    :param recursive: Рекурсивный поиск в подпапках
    :return: Список путей к изображениям
    """
    path = Path(input_path)
    supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}

    if path.is_file():
        if path.suffix.lower() in supported_formats:
            return [str(path)]
        else:
            print(f"❌ Неподдерживаемый формат файла: {path.suffix}")
            return []

    elif path.is_dir():
        images = []

        if recursive:
            for ext in supported_formats:
                images.extend(path.rglob(f"*{ext}"))
                images.extend(path.rglob(f"*{ext.upper()}"))
        else:
            for ext in supported_formats:
                images.extend(path.glob(f"*{ext}"))
                images.extend(path.glob(f"*{ext.upper()}"))

        return [str(img) for img in images]

    else:
        print(f"❌ Путь не существует: {input_path}")
        return []


def create_progress_callback(total_files: int):
    """
    Создает колбэк для отображения прогресса в CLI.

    :param total_files: Общее количество файлов
    :return: Функция колбэка
    """
    def progress_callback(current: int, total: int, filename: str):
        percentage = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        print(f'\r[{bar}] {percentage:.1f}% ({current}/{total}) - {filename}', end='', flush=True)

        if current == total:
            print()  # Новая строка в конце

    return progress_callback


def main():
    """Главная функция CLI приложения."""
    parser = argparse.ArgumentParser(
        description='OCR AI or Offline - Распознавание текста с изображений',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Offline OCR одного файла
  python main.py image.png --output result.txt

  # Offline OCR папки с изображениями
  python main.py /path/to/images --output result.txt --recursive

  # Online OCR с промптом для математических формул
  python main.py /path/to/images --mode online --prompt math_formulas_ocr --output math_text.txt

  # Сортировка по времени создания
  python main.py /path/to/images --sort creation_time --output sorted_result.txt

  # Подробный вывод
  python main.py /path/to/images --verbose --output debug_result.txt
        """)

    # Основные аргументы
    parser.add_argument('input', help='Путь к изображению или папке с изображениями')
    parser.add_argument('--output', '-o', default='ocr_result.txt',
                       help='Путь к выходному файлу (по умолчанию: ocr_result.txt)')

    # Режим обработки
    parser.add_argument('--mode', '-m', choices=['offline', 'online'], default='offline',
                       help='Режим OCR: offline (Tesseract) или online (LLM) (по умолчанию: offline)')

    # Настройки offline OCR
    parser.add_argument('--language', '-l', default='rus',
                       help='Язык для Tesseract OCR (по умолчанию: rus)')
    parser.add_argument('--psm', type=int, default=3,
                       help='Page Segmentation Mode для Tesseract (по умолчанию: 3)')

    # Настройки online OCR
    parser.add_argument('--prompt', '-p', default='classic_ocr',
                       help='Промпт для online OCR (по умолчанию: classic_ocr)')
    parser.add_argument('--threads', '-t', type=int, default=5,
                       help='Количество потоков для online OCR (по умолчанию: 5)')

    # Настройки сортировки
    parser.add_argument('--sort', '-s',
                       choices=['natural', 'alphabetical', 'creation_time', 'modification_time', 'file_size'],
                       default='natural',
                       help='Метод сортировки файлов (по умолчанию: natural)')

    # Дополнительные опции
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Рекурсивный поиск в подпапках')
    parser.add_argument('--config', '-c', default='config.json',
                       help='Путь к файлу конфигурации (по умолчанию: config.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Подробный вывод')
    parser.add_argument('--no-metadata', action='store_true',
                       help='Не включать метаданные в результат')

    # GUI режим
    parser.add_argument('--gui', action='store_true',
                       help='Запустить GUI версию')

    args = parser.parse_args()

    # Если запрашивается GUI, перенаправляем на gui_main.py
    if args.gui:
        print("Запуск GUI версии...")
        try:
            import gui_main
            return gui_main.main()
        except ImportError:
            print("❌ GUI компоненты недоступны")
            return 1

    # Настройка логирования
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    print("🔍 OCR AI or Offline - CLI режим")
    print("=" * 50)

    # Загрузка конфигурации
    config = load_config(args.config)

    try:
        # Поиск изображений
        print(f"Поиск изображений в: {args.input}")
        image_paths = find_images(args.input, args.recursive)

        if not image_paths:
            print("❌ Изображения не найдены")
            return 1

        print(f"✅ Найдено изображений: {len(image_paths)}")

        # Инициализация OCR процессора
        print("Инициализация OCR процессора...")
        processor = OCRProcessor(args.config)

        # Сортировка файлов
        if len(image_paths) > 1:
            print(f"Сортировка файлов методом: {args.sort}")
            image_paths = processor.sort_images(image_paths, args.sort)

        # Настройка прогресса
        progress_callback = create_progress_callback(len(image_paths))
        processor.set_progress_callback(progress_callback)

        # Обработка в зависимости от режима
        print(f"Начинаем {args.mode} OCR обработку...")
        print("-" * 50)

        if args.mode == 'offline':
            # Offline обработка
            result = processor.process_batch(
                image_paths=image_paths,
                output_file=args.output,
                mode='offline',
                sort_method=args.sort,
                language=args.language,
                psm_mode=args.psm
            )
        else:
            # Online обработка
            result = processor.process_batch(
                image_paths=image_paths,
                output_file=args.output,
                mode='online',
                sort_method=args.sort,
                prompt_name=args.prompt,
                max_threads=args.threads
            )

        # Результаты
        print("\n" + "=" * 50)
        print("✅ Обработка завершена!")
        print(f"📊 Статистика:")
        print(f"   • Всего файлов: {result.total_files}")
        print(f"   • Успешно обработано: {result.successful_files}")
        print(f"   • Ошибок: {result.total_files - result.successful_files}")
        print(f"   • Время обработки: {result.total_processing_time:.2f} секунд")
        print(f"   • Результат сохранен: {result.output_file_path}")

        if result.successful_files == 0:
            print("⚠️ Ни один файл не был обработан успешно")
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n🛑 Обработка остановлена пользователем")
        return 0

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
        if args.verbose:
            import traceback
            print(f"Трассировка:\n{traceback.format_exc()}")
        return 1


def show_version():
    """Показывает информацию о версии."""
    print("OCR AI or Offline v1.0.0")
    print("Инструмент для распознавания текста с изображений")
    print()
    print("Поддерживаемые режимы:")
    print("  • Offline: Tesseract OCR")
    print("  • Online: ИИ модели (OpenAI/OpenRouter)")
    print()
    print("Поддерживаемые форматы: PNG, JPG, JPEG, TIFF, BMP, GIF")


def show_examples():
    """Показывает примеры использования."""
    examples = [
        ("Простая обработка одного файла",
         "python main.py image.png --output result.txt"),

        ("Обработка папки в offline режиме",
         "python main.py /path/to/images --output result.txt --recursive"),

        ("Online OCR с промптом для формул",
         "python main.py /path/to/images --mode online --prompt math_formulas_ocr"),

        ("Сортировка по времени создания",
         "python main.py /path/to/images --sort creation_time"),

        ("Японский текст с custom настройками",
         "python main.py japanese_images/ --mode online --prompt japanese_ocr"),

        ("Подробный вывод для отладки",
         "python main.py images/ --verbose --output debug.txt"),

        ("Запуск GUI из командной строки",
         "python main.py --gui")
    ]

    print("Примеры использования OCR AI or Offline:")
    print("=" * 50)

    for i, (description, command) in enumerate(examples, 1):
        print(f"{i}. {description}")
        print(f"   {command}")
        print()


if __name__ == "__main__":
    # Проверяем специальные аргументы
    if len(sys.argv) == 2:
        if sys.argv[1] in ['--version', '-V']:
            show_version()
            sys.exit(0)
        elif sys.argv[1] in ['--examples', '--help-examples']:
            show_examples()
            sys.exit(0)

    # Проверяем версию Python
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или новее")
        print(f"Текущая версия: {sys.version}")
        sys.exit(1)

    # Запускаем приложение
    exit_code = main()
    sys.exit(exit_code)
