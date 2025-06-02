"""
Главный координатор OCR обработки.
Управляет выбором между offline и online режимами, координирует весь процесс обработки.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

from .offline_ocr import OfflineOCRProcessor
from .online_ocr import OnlineOCRProcessor
from .image_sorter import ImageSorter
from .prompt_manager import PromptManager
from .result_formatter import ResultFormatter


@dataclass
class OCRResult:
    """Результат OCR обработки для одного изображения."""
    file_path: str
    success: bool
    text_content: str
    error_message: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class OCRBatchResult:
    """Результат обработки группы изображений."""
    results: List[OCRResult]
    total_files: int
    successful_files: int
    total_processing_time: float
    output_file_path: str


class OCRProcessor:
    """
    Главный класс для координации OCR обработки.
    Управляет выбором режима обработки, сортировкой файлов и объединением результатов.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Инициализация OCR процессора.

        :param config_path: Путь к файлу конфигурации
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Инициализируем компоненты
        self.image_sorter = ImageSorter()
        self.prompt_manager = PromptManager()
        self.result_formatter = ResultFormatter()

        # Процессоры для разных режимов
        self.offline_processor = OfflineOCRProcessor(self.config)
        self.online_processor = OnlineOCRProcessor(self.config)

        # Колбэк для отслеживания прогресса
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Загружает конфигурацию из JSON файла.

        :param config_path: Путь к файлу конфигурации
        :return: Словарь с конфигурацией
        :raises FileNotFoundError: Если файл конфигурации не найден
        :raises json.JSONDecodeError: Если файл содержит невалидный JSON
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
                self.logger.info(f"Конфигурация загружена из {config_path}")
                return config
        except FileNotFoundError:
            self.logger.error(f"Файл конфигурации не найден: {config_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка в формате конфигурации: {e}")
            raise

    def _setup_logging(self) -> logging.Logger:
        """
        Настраивает систему логирования.

        :return: Настроенный logger
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Проверяем, не настроен ли уже handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Устанавливает колбэк для отслеживания прогресса обработки.

        :param callback: Функция с параметрами (current, total, current_file)
        """
        self.progress_callback = callback

    def get_supported_formats(self) -> List[str]:
        """
        Возвращает список поддерживаемых форматов изображений.

        :return: Список расширений файлов (например, ['.png', '.jpg'])
        """
        return self.config.get('ocr_settings', {}).get('offline', {}).get(
            'supported_formats', ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        )

    def find_image_files(self, directory_path: str) -> List[str]:
        """
        Находит все изображения в указанной директории.

        :param directory_path: Путь к директории
        :return: Список путей к файлам изображений
        :raises ValueError: Если директория не существует
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Директория не существует: {directory_path}")

        if not directory.is_dir():
            raise ValueError(f"Указанный путь не является директорией: {directory_path}")

        supported_formats = self.get_supported_formats()
        image_files = []

        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                image_files.append(str(file_path))

        self.logger.info(f"Найдено {len(image_files)} изображений в {directory_path}")
        return image_files

    def sort_images(self, image_paths: List[str], sort_method: str = "natural") -> List[str]:
        """
        Сортирует список изображений по выбранному алгоритму.

        :param image_paths: Список путей к изображениям
        :param sort_method: Метод сортировки ('natural', 'alphabetical', 'creation_time', etc.)
        :return: Отсортированный список путей
        """
        try:
            sorted_paths = self.image_sorter.sort_files(image_paths, sort_method)
            self.logger.info(f"Изображения отсортированы методом: {sort_method}")
            return sorted_paths
        except Exception as e:
            self.logger.error(f"Ошибка при сортировке: {e}")
            return image_paths  # Возвращаем исходный список в случае ошибки

    def process_images_offline(self, image_paths: List[str],
                             language: str = "rus",
                             psm_mode: int = 3) -> List[OCRResult]:
        """
        Обрабатывает изображения в offline режиме (tesseract).

        :param image_paths: Список путей к изображениям
        :param language: Язык для OCR (например, 'rus', 'eng')
        :param psm_mode: Режим сегментации страницы Tesseract
        :return: Список результатов OCR
        """
        self.logger.info(f"Начинаем offline обработку {len(image_paths)} изображений")
        results = []

        for i, image_path in enumerate(image_paths):
            # Уведомляем о прогрессе
            if self.progress_callback:
                filename = os.path.basename(image_path)
                self.progress_callback(i + 1, len(image_paths), filename)

            try:
                result = self.offline_processor.process_image(
                    image_path, language, psm_mode
                )
                results.append(result)
                self.logger.debug(f"Обработан файл: {image_path}")

            except Exception as e:
                error_result = OCRResult(
                    file_path=image_path,
                    success=False,
                    text_content="",
                    error_message=str(e)
                )
                results.append(error_result)
                self.logger.error(f"Ошибка при обработке {image_path}: {e}")

        self.logger.info(f"Offline обработка завершена: {len(results)} файлов")
        return results

    def process_images_online(self, image_paths: List[str],
                            prompt_name: str = "classic_ocr",
                            max_threads: int = 5) -> List[OCRResult]:
        """
        Обрабатывает изображения в online режиме (LLM).

        :param image_paths: Список путей к изображениям
        :param prompt_name: Название промпта для OCR
        :param max_threads: Максимальное количество потоков для параллельной обработки
        :return: Список результатов OCR
        """
        self.logger.info(f"Начинаем online обработку {len(image_paths)} изображений")

        # Загружаем промпт
        try:
            prompt_text = self.prompt_manager.load_prompt(prompt_name)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки промпта {prompt_name}: {e}")
            # Используем базовый промпт как fallback
            prompt_text = "Перепиши весь текст с изображения точно как он написан."

        # Обрабатываем изображения
        results = self.online_processor.process_images_batch(
            image_paths=image_paths,
            prompt_text=prompt_text,
            max_threads=max_threads,
            progress_callback=self.progress_callback
        )

        self.logger.info(f"Online обработка завершена: {len(results)} файлов")
        return results

    def save_results(self, results: List[OCRResult], output_file: str,
                    include_metadata: bool = True) -> str:
        """
        Сохраняет результаты OCR в файл.

        :param results: Список результатов OCR
        :param output_file: Путь к выходному файлу
        :param include_metadata: Включать ли метаданные о файлах
        :return: Путь к созданному файлу
        """
        try:
            formatted_content = self.result_formatter.format_results(
                results, include_metadata
            )

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(formatted_content)

            self.logger.info(f"Результаты сохранены в {output_file}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результатов: {e}")
            raise

    def process_batch(self, image_paths: List[str],
                     output_file: str,
                     mode: str = "offline",
                     sort_method: str = "natural",
                     **kwargs) -> OCRBatchResult:
        """
        Полный цикл обработки группы изображений.

        :param image_paths: Список путей к изображениям
        :param output_file: Путь к выходному файлу
        :param mode: Режим обработки ('offline' или 'online')
        :param sort_method: Метод сортировки изображений
        :param kwargs: Дополнительные параметры для обработки
        :return: Результат обработки группы
        """
        import time

        start_time = time.time()
        self.logger.info(f"Начинаем обработку {len(image_paths)} изображений в режиме {mode}")

        try:
            # Сортируем изображения
            sorted_images = self.sort_images(image_paths, sort_method)

            # Обрабатываем в зависимости от режима
            if mode.lower() == "offline":
                language = kwargs.get('language', 'rus')
                psm_mode = kwargs.get('psm_mode', 3)
                results = self.process_images_offline(sorted_images, language, psm_mode)

            elif mode.lower() == "online":
                prompt_name = kwargs.get('prompt_name', 'classic_ocr')
                max_threads = kwargs.get('max_threads', 5)
                results = self.process_images_online(sorted_images, prompt_name, max_threads)

            else:
                raise ValueError(f"Неподдерживаемый режим обработки: {mode}")

            # Сохраняем результаты
            actual_output_path = self.save_results(results, output_file)

            # Подсчитываем статистику
            successful_files = sum(1 for r in results if r.success)
            total_time = time.time() - start_time

            batch_result = OCRBatchResult(
                results=results,
                total_files=len(image_paths),
                successful_files=successful_files,
                total_processing_time=total_time,
                output_file_path=actual_output_path
            )

            self.logger.info(
                f"Обработка завершена: {successful_files}/{len(image_paths)} файлов успешно, "
                f"время: {total_time:.2f}с"
            )

            return batch_result

        except Exception as e:
            self.logger.error(f"Критическая ошибка при обработке: {e}")
            raise

    def get_available_prompts(self) -> List[str]:
        """
        Возвращает список доступных промптов.

        :return: Список названий промптов
        """
        return self.prompt_manager.get_available_prompts()

    def get_available_languages(self) -> List[str]:
        """
        Возвращает список доступных языков для offline OCR.

        :return: Список кодов языков
        """
        return self.offline_processor.get_available_languages()

    def validate_config(self) -> bool:
        """
        Проверяет корректность конфигурации.

        :return: True если конфигурация валидна
        """
        required_keys = ['ocr_settings', 'gui_settings']

        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"Отсутствует обязательный ключ конфигурации: {key}")
                return False

        return True
