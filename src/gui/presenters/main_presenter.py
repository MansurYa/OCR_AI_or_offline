"""
Главный презентер приложения.
Координирует взаимодействие между моделями и представлениями в MVP архитектуре.
"""

import os
import logging
import threading
from typing import Optional, List, Dict, Any
from pathlib import Path

# Импорты моделей
from ..models.app_model import AppModel, ImageFile, ProcessingState
from ..models.settings_model import SettingsModel

# Импорты core компонентов
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.ocr_processor import OCRProcessor
from src.core.types import OCRBatchResult


class MainPresenter:
    """
    Главный презентер для координации между моделями и представлениями.
    Управляет бизнес-логикой приложения и обеспечивает связь между компонентами.
    """

    def __init__(self):
        """Инициализация главного презентера."""
        self.logger = logging.getLogger(__name__)

        # Модели
        self.app_model = AppModel()
        self.settings_model = SettingsModel()

        # Core компоненты
        self.ocr_processor: Optional[OCRProcessor] = None

        # Представления (будут установлены позже)
        self.main_view = None

        # Состояние
        self._processing_thread: Optional[threading.Thread] = None
        self._processing_cancelled = False

        # Инициализация
        self._initialize_ocr_processor()
        self._setup_model_observers()

    def _initialize_ocr_processor(self) -> None:
        """Инициализирует OCR процессор."""
        try:
            self.ocr_processor = OCRProcessor(self.settings_model.config_path)
            self.logger.info("OCR процессор успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации OCR процессора: {e}")
            self.ocr_processor = None

    def _setup_model_observers(self) -> None:
        """Настраивает наблюдателей для моделей."""
        # Подписываемся на изменения в моделях
        self.app_model.add_observer(self._on_images_changed)
        self.app_model.add_processing_observer(self._on_processing_state_changed)
        self.settings_model.add_observer(self._on_settings_changed)

    def set_main_view(self, view) -> None:
        """
        Устанавливает главное представление.

        :param view: Главное представление
        """
        self.main_view = view
        self.logger.debug("Главное представление установлено")

    def _on_images_changed(self) -> None:
        """Обработчик изменений в списке изображений."""
        if self.main_view:
            self.main_view.update_image_list()
            self.main_view.update_statistics()

    def _on_processing_state_changed(self, state: ProcessingState) -> None:
        """
        Обработчик изменений состояния обработки.

        :param state: Новое состояние обработки
        """
        if self.main_view:
            self.main_view.update_processing_state(state)

    def _on_settings_changed(self) -> None:
        """Обработчик изменений настроек."""
        if self.main_view:
            self.main_view.update_settings_display()

        # Автосохранение настроек если включено
        self.settings_model.auto_save_if_enabled()

    # ==============================
    # Методы для работы с файлами
    # ==============================

    def add_files(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Добавляет файлы изображений.

        :param file_paths: Список путей к файлам
        :return: Результат добавления файлов
        """
        result = self.app_model.add_images(file_paths)

        # Логируем результат
        if result['added']:
            self.logger.info(f"Добавлено файлов: {len(result['added'])}")
        if result['skipped']:
            self.logger.info(f"Пропущено файлов (дубликаты): {len(result['skipped'])}")
        if result['invalid']:
            self.logger.warning(f"Неверных файлов: {len(result['invalid'])}")

        return result

    def add_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, List[str]]:
        """
        Добавляет файлы из директории.

        :param directory_path: Путь к директории
        :param recursive: Рекурсивный поиск
        :return: Результат добавления файлов
        """
        result = self.app_model.add_images_from_directory(directory_path, recursive)

        # Обновляем последнюю директорию в настройках
        if result['added'] and self.settings_model.gui_settings.remember_last_directory:
            self.settings_model.gui_settings.last_input_directory = directory_path
            self.settings_model.auto_save_if_enabled()

        return result

    def remove_file(self, index: int) -> bool:
        """
        Удаляет файл по индексу.

        :param index: Индекс файла
        :return: True если удаление успешно
        """
        return self.app_model.remove_image(index)

    def clear_files(self) -> None:
        """Очищает все файлы."""
        self.app_model.clear_images()
        self.logger.info("Список файлов очищен")

    def move_file(self, from_index: int, to_index: int) -> bool:
        """
        Перемещает файл в списке.

        :param from_index: Исходный индекс
        :param to_index: Целевой индекс
        :return: True если перемещение успешно
        """
        return self.app_model.move_image(from_index, to_index)

    def sort_files(self, method: str) -> None:
        """
        Сортирует файлы по выбранному методу.

        :param method: Метод сортировки
        """
        if not self.ocr_processor:
            self.logger.error("OCR процессор не инициализирован")
            return

        image_paths = self.app_model.get_image_paths()
        if not image_paths:
            return

        try:
            sorted_paths = self.ocr_processor.sort_images(image_paths, method)

            # Обновляем порядок в модели
            self.app_model.clear_images()
            self.app_model.add_images(sorted_paths)

            self.logger.info(f"Файлы отсортированы методом: {method}")

        except Exception as e:
            self.logger.error(f"Ошибка сортировки файлов: {e}")

    # ================================
    # Методы для работы с настройками
    # ================================

    def set_ocr_mode(self, mode: str) -> bool:
        """
        Устанавливает режим OCR.

        :param mode: Режим OCR ("offline" или "online")
        :return: True если режим установлен
        """
        return self.settings_model.set_ocr_mode(mode)

    def set_sort_method(self, method: str) -> bool:
        """
        Устанавливает метод сортировки.

        :param method: Метод сортировки
        :return: True если метод установлен
        """
        return self.settings_model.set_sort_method(method)

    def set_output_file(self, file_path: str) -> None:
        """
        Устанавливает выходной файл.

        :param file_path: Путь к выходному файлу
        """
        self.settings_model.set_output_file(file_path)

    def update_offline_settings(self, **kwargs) -> None:
        """
        Обновляет настройки offline OCR.

        :param kwargs: Настройки для обновления
        """
        self.settings_model.update_offline_settings(**kwargs)

    def update_online_settings(self, **kwargs) -> None:
        """
        Обновляет настройки online OCR.

        :param kwargs: Настройки для обновления
        """
        self.settings_model.update_online_settings(**kwargs)

    def get_available_prompts(self) -> List[str]:
        """
        Возвращает список доступных промптов.

        :return: Список промптов
        """
        if self.ocr_processor:
            return self.ocr_processor.get_available_prompts()
        return []

    def get_available_languages(self) -> List[str]:
        """
        Возвращает список доступных языков.

        :return: Список языков
        """
        if self.ocr_processor:
            return self.ocr_processor.get_available_languages()
        return self.settings_model.available_languages

    # ===============================
    # Методы для обработки OCR
    # ===============================

    def can_start_processing(self) -> bool:
        """
        Проверяет, можно ли начать обработку.

        :return: True если можно начать обработку
        """
        if self.app_model.processing_state.is_running:
            return False

        if self.app_model.get_valid_image_count() == 0:
            return False

        if not self.ocr_processor:
            return False

        if not self.settings_model.output_file:
            return False

        return True

    def start_processing(self) -> bool:
        """
        Запускает обработку OCR.

        :return: True если обработка запущена
        """
        if not self.can_start_processing():
            self.logger.warning("Невозможно начать обработку")
            return False

        # Отменяем предыдущий поток если существует
        if self._processing_thread and self._processing_thread.is_alive():
            self.cancel_processing()

        # Запускаем обработку в отдельном потоке
        self._processing_cancelled = False
        self._processing_thread = threading.Thread(target=self._process_images_thread, daemon=True)
        self._processing_thread.start()

        self.logger.info("Обработка OCR запущена")
        return True

    def cancel_processing(self) -> None:
        """Отменяет текущую обработку."""
        self._processing_cancelled = True
        self.app_model.cancel_processing()

        # Ждем завершения потока
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)

        self.logger.info("Обработка OCR отменена")

    def _process_images_thread(self) -> None:
        """Обрабатывает изображения в отдельном потоке."""
        try:
            # Получаем параметры обработки
            image_paths = self.app_model.get_image_paths()
            if not image_paths:
                return

            # Начинаем обработку
            self.app_model.start_processing(len(image_paths))

            # Настраиваем прогресс callback
            def progress_callback(current: int, total: int, filename: str):
                if self._processing_cancelled:
                    return
                self.app_model.update_processing_progress(current, filename)

            self.ocr_processor.set_progress_callback(progress_callback)

            # Получаем настройки
            mode = self.settings_model.ocr_mode
            sort_method = self.settings_model.sort_method
            output_file = self.settings_model.output_file

            # Параметры в зависимости от режима
            if mode == "offline":
                settings = self.settings_model.offline_settings
                kwargs = {
                    'language': settings.language,
                    'psm_mode': settings.psm_mode
                }
            else:
                settings = self.settings_model.online_settings
                kwargs = {
                    'prompt_name': settings.prompt_name,
                    'max_threads': settings.max_threads
                }

            # Запускаем обработку
            result: OCRBatchResult = self.ocr_processor.process_batch(
                image_paths=image_paths,
                output_file=output_file,
                mode=mode,
                sort_method=sort_method,
                **kwargs
            )

            # Завершаем обработку
            if not self._processing_cancelled:
                self.app_model.finish_processing()
                self._on_processing_completed(result)

        except Exception as e:
            self.logger.error(f"Ошибка в потоке обработки: {e}")
            self.app_model.finish_processing()
            self._on_processing_error(str(e))

    def _on_processing_completed(self, result: OCRBatchResult) -> None:
        """
        Обработчик завершения обработки.

        :param result: Результат обработки
        """
        success_rate = result.successful_files / result.total_files * 100 if result.total_files > 0 else 0

        self.logger.info(
            f"Обработка завершена: {result.successful_files}/{result.total_files} файлов "
            f"({success_rate:.1f}%) за {result.total_processing_time:.2f}с"
        )

        # Уведомляем представление о завершении
        if self.main_view:
            self.main_view.on_processing_completed(result)

    def _on_processing_error(self, error_message: str) -> None:
        """
        Обработчик ошибки обработки.

        :param error_message: Сообщение об ошибке
        """
        self.logger.error(f"Ошибка обработки: {error_message}")

        if self.main_view:
            self.main_view.on_processing_error(error_message)

    # ============================
    # Методы для получения данных
    # ============================

    def get_image_files(self) -> List[ImageFile]:
        """
        Возвращает список файлов изображений.

        :return: Список файлов
        """
        return self.app_model.get_image_files()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по файлам.

        :return: Словарь со статистикой
        """
        return self.app_model.get_statistics()

    def get_settings(self) -> SettingsModel:
        """
        Возвращает модель настроек.

        :return: Модель настроек
        """
        return self.settings_model

    def get_processing_state(self) -> ProcessingState:
        """
        Возвращает текущее состояние обработки.

        :return: Состояние обработки
        """
        return self.app_model.processing_state

    # ==================================
    # Методы жизненного цикла приложения
    # ==================================

    def on_application_start(self) -> None:
        """Обработчик запуска приложения."""
        self.logger.info("Приложение запущено")

        # Валидируем конфигурацию OCR процессора
        if self.ocr_processor and not self.ocr_processor.validate_config():
            self.logger.warning("Конфигурация OCR процессора содержит ошибки")

    def on_application_exit(self) -> None:
        """Обработчик завершения приложения."""
        # Отменяем текущую обработку если идет
        if self.app_model.processing_state.is_running:
            self.cancel_processing()

        # Сохраняем настройки
        self.settings_model.save_settings()

        self.logger.info("Приложение завершено")

    def on_window_resize(self, width: int, height: int) -> None:
        """
        Обработчик изменения размера окна.

        :param width: Новая ширина
        :param height: Новая высота
        """
        self.settings_model.update_gui_settings(
            window_width=width,
            window_height=height
        )

    # ==========================
    # Вспомогательные методы
    # ==========================

    def validate_files(self) -> None:
        """Перепроверяет валидность всех файлов."""
        self.app_model.validate_all_files()

    def get_file_info(self, index: int) -> Optional[ImageFile]:
        """
        Возвращает информацию о файле по индексу.

        :param index: Индекс файла
        :return: Информация о файле или None
        """
        files = self.app_model.get_image_files()
        if 0 <= index < len(files):
            return files[index]
        return None

    def test_ocr_connection(self) -> bool:
        """
        Тестирует подключение к OCR сервисам.

        :return: True если подключение работает
        """
        if not self.ocr_processor:
            return False

        try:
            # Тестируем offline OCR
            offline_result = self.ocr_processor.offline_processor.test_ocr_capability()

            # Тестируем online OCR если настроен
            online_result = True
            if self.settings_model.ocr_mode == "online":
                online_result = self.ocr_processor.online_processor.test_llm_connection()

            return offline_result and online_result

        except Exception as e:
            self.logger.error(f"Ошибка при тестировании OCR подключения: {e}")
            return False

    def estimate_processing_time(self) -> float:
        """
        Оценивает время обработки текущих файлов.

        :return: Оценочное время в секундах
        """
        if not self.ocr_processor:
            return 0.0

        file_count = self.app_model.get_valid_image_count()
        if file_count == 0:
            return 0.0

        if self.settings_model.ocr_mode == "online":
            return self.ocr_processor.online_processor.estimate_processing_time(file_count)
        else:
            # Примерная оценка для offline OCR
            return file_count * 2.0  # 2 секунды на файл
