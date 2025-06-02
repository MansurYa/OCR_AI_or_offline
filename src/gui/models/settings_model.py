"""
Модель настроек приложения.
Управляет настройками OCR, GUI и сохранением конфигурации.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class OfflineSettings:
    """Настройки offline OCR."""
    language: str = "rus"
    psm_mode: int = 3
    tessdata_dir: str = "~/tessdata"


@dataclass
class OnlineSettings:
    """Настройки online OCR."""
    prompt_name: str = "classic_ocr"
    max_threads: int = 5
    timeout_seconds: int = 30
    retry_attempts: int = 3


@dataclass
class GUISettings:
    """Настройки GUI."""
    window_width: int = 1000
    window_height: int = 700
    theme: str = "light"
    auto_save_settings: bool = True
    show_image_preview: bool = True
    preview_size: int = 150
    remember_last_directory: bool = True
    last_output_directory: str = ""
    last_input_directory: str = ""


class SettingsModel:
    """
    Модель настроек приложения.
    Управляет всеми настройками OCR и GUI, обеспечивает их сохранение и загрузку.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Инициализация модели настроек.

        :param config_path: Путь к файлу конфигурации
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path

        # Текущие настройки
        self.ocr_mode = "offline"  # "offline" или "online"
        self.sort_method = "natural"
        self.output_file = "result.txt"
        self.include_metadata = True

        # Специфичные настройки для режимов
        self.offline_settings = OfflineSettings()
        self.online_settings = OnlineSettings()
        self.gui_settings = GUISettings()

        # Доступные опции
        self.available_sort_methods = [
            {"name": "Natural (по номерам)", "key": "natural"},
            {"name": "По времени создания", "key": "creation_time"},
            {"name": "По времени изменения", "key": "modification_time"},
            {"name": "Алфавитная сортировка", "key": "alphabetical"},
            {"name": "По размеру файла", "key": "file_size"}
        ]

        self.available_languages = ["rus", "eng", "fra", "deu", "spa", "ita", "por"]
        self.available_psm_modes = [
            {"name": "Auto OSD (0)", "value": 0},
            {"name": "Auto с OSD (1)", "value": 1},
            {"name": "Auto без OSD (2)", "value": 2},
            {"name": "Полностью автоматический (3)", "value": 3},
            {"name": "Один столбец текста (4)", "value": 4},
            {"name": "Вертикальный блок текста (5)", "value": 5},
            {"name": "Единый блок текста (6)", "value": 6},
            {"name": "Одна строка текста (7)", "value": 7},
            {"name": "Одно слово (8)", "value": 8},
            {"name": "Одно слово в круге (9)", "value": 9},
            {"name": "Один символ (10)", "value": 10}
        ]

        # Колбэки для уведомления об изменениях
        self._observers: List[Callable[[], None]] = []

        # Загружаем настройки при инициализации
        self.load_settings()

    def add_observer(self, callback: Callable[[], None]) -> None:
        """
        Добавляет наблюдателя для изменений настроек.

        :param callback: Функция обратного вызова
        """
        self._observers.append(callback)

    def _notify_observers(self) -> None:
        """Уведомляет всех наблюдателей об изменениях настроек."""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Ошибка в settings observer callback: {e}")

    def load_settings(self) -> bool:
        """
        Загружает настройки из файла конфигурации.

        :return: True если загрузка успешна
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.info(f"Файл конфигурации не найден: {self.config_path}, используем настройки по умолчанию")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)

            self._load_from_config(config)
            self.logger.info("Настройки успешно загружены")
            self._notify_observers()
            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка формата JSON в файле конфигурации: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка загрузки настроек: {e}")
            return False

    def _load_from_config(self, config: Dict[str, Any]) -> None:
        """
        Загружает настройки из словаря конфигурации.

        :param config: Словарь с конфигурацией
        """
        # OCR настройки
        ocr_settings = config.get('ocr_settings', {})

        # Offline настройки
        offline_config = ocr_settings.get('offline', {})
        self.offline_settings.language = offline_config.get('default_language', self.offline_settings.language)
        self.offline_settings.psm_mode = offline_config.get('psm_mode', self.offline_settings.psm_mode)
        self.offline_settings.tessdata_dir = offline_config.get('tessdata_dir', self.offline_settings.tessdata_dir)

        # Online настройки
        online_config = ocr_settings.get('online', {})
        self.online_settings.prompt_name = online_config.get('default_prompt', self.online_settings.prompt_name)
        self.online_settings.max_threads = online_config.get('max_threads', self.online_settings.max_threads)
        self.online_settings.timeout_seconds = online_config.get('timeout_seconds', self.online_settings.timeout_seconds)
        self.online_settings.retry_attempts = online_config.get('retry_attempts', self.online_settings.retry_attempts)

        # GUI настройки
        gui_config = config.get('gui_settings', {})
        window_size = gui_config.get('window_size', '1000x700')
        if 'x' in window_size:
            width, height = window_size.split('x')
            self.gui_settings.window_width = int(width)
            self.gui_settings.window_height = int(height)

        self.gui_settings.theme = gui_config.get('theme', self.gui_settings.theme)
        self.gui_settings.auto_save_settings = gui_config.get('auto_save_settings', self.gui_settings.auto_save_settings)
        self.gui_settings.show_image_preview = gui_config.get('show_image_preview', self.gui_settings.show_image_preview)
        self.gui_settings.preview_size = gui_config.get('preview_size', self.gui_settings.preview_size)

        # Обновляем доступные опции сортировки если есть в конфигурации
        if 'sorting_options' in config:
            self.available_sort_methods = config['sorting_options']

    def save_settings(self) -> bool:
        """
        Сохраняет текущие настройки в файл конфигурации.

        :return: True если сохранение успешно
        """
        try:
            # Загружаем существующую конфигурацию чтобы не потерять другие настройки
            existing_config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    existing_config = json.load(file)

            # Обновляем настройки
            config = existing_config.copy()

            # OCR настройки
            if 'ocr_settings' not in config:
                config['ocr_settings'] = {}

            config['ocr_settings']['offline'] = {
                'default_language': self.offline_settings.language,
                'psm_mode': self.offline_settings.psm_mode,
                'tessdata_dir': self.offline_settings.tessdata_dir,
                'supported_formats': [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
            }

            config['ocr_settings']['online'] = {
                'default_prompt': self.online_settings.prompt_name,
                'max_threads': self.online_settings.max_threads,
                'timeout_seconds': self.online_settings.timeout_seconds,
                'retry_attempts': self.online_settings.retry_attempts
            }

            # GUI настройки
            config['gui_settings'] = {
                'window_size': f"{self.gui_settings.window_width}x{self.gui_settings.window_height}",
                'theme': self.gui_settings.theme,
                'auto_save_settings': self.gui_settings.auto_save_settings,
                'show_image_preview': self.gui_settings.show_image_preview,
                'preview_size': self.gui_settings.preview_size
            }

            # Сохраняем в файл
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)

            self.logger.info("Настройки успешно сохранены")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек: {e}")
            return False

    def set_ocr_mode(self, mode: str) -> bool:
        """
        Устанавливает режим OCR.

        :param mode: Режим OCR ("offline" или "online")
        :return: True если режим установлен успешно
        """
        if mode in ["offline", "online"]:
            old_mode = self.ocr_mode
            self.ocr_mode = mode

            if old_mode != mode:
                self._notify_observers()
                self.logger.debug(f"Режим OCR изменен на: {mode}")

            return True
        else:
            self.logger.warning(f"Неверный режим OCR: {mode}")
            return False

    def set_sort_method(self, method: str) -> bool:
        """
        Устанавливает метод сортировки файлов.

        :param method: Ключ метода сортировки
        :return: True если метод установлен успешно
        """
        available_keys = [opt['key'] for opt in self.available_sort_methods]

        if method in available_keys:
            old_method = self.sort_method
            self.sort_method = method

            if old_method != method:
                self._notify_observers()
                self.logger.debug(f"Метод сортировки изменен на: {method}")

            return True
        else:
            self.logger.warning(f"Неверный метод сортировки: {method}")
            return False

    def set_output_file(self, file_path: str) -> None:
        """
        Устанавливает путь к выходному файлу.

        :param file_path: Путь к выходному файлу
        """
        if file_path != self.output_file:
            self.output_file = file_path

            # Сохраняем директорию для будущего использования
            if self.gui_settings.remember_last_directory:
                self.gui_settings.last_output_directory = os.path.dirname(file_path)

            self._notify_observers()
            self.logger.debug(f"Выходной файл изменен на: {file_path}")

    def update_offline_settings(self, **kwargs) -> None:
        """
        Обновляет настройки offline OCR.

        :param kwargs: Параметры для обновления
        """
        updated = False

        for key, value in kwargs.items():
            if hasattr(self.offline_settings, key):
                old_value = getattr(self.offline_settings, key)
                setattr(self.offline_settings, key, value)

                if old_value != value:
                    updated = True
                    self.logger.debug(f"Offline настройка {key} изменена: {old_value} -> {value}")

        if updated:
            self._notify_observers()

    def update_online_settings(self, **kwargs) -> None:
        """
        Обновляет настройки online OCR.

        :param kwargs: Параметры для обновления
        """
        updated = False

        for key, value in kwargs.items():
            if hasattr(self.online_settings, key):
                old_value = getattr(self.online_settings, key)
                setattr(self.online_settings, key, value)

                if old_value != value:
                    updated = True
                    self.logger.debug(f"Online настройка {key} изменена: {old_value} -> {value}")

        if updated:
            self._notify_observers()

    def update_gui_settings(self, **kwargs) -> None:
        """
        Обновляет настройки GUI.

        :param kwargs: Параметры для обновления
        """
        updated = False

        for key, value in kwargs.items():
            if hasattr(self.gui_settings, key):
                old_value = getattr(self.gui_settings, key)
                setattr(self.gui_settings, key, value)

                if old_value != value:
                    updated = True
                    self.logger.debug(f"GUI настройка {key} изменена: {old_value} -> {value}")

        if updated:
            self._notify_observers()

    def get_current_ocr_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки для текущего режима OCR.

        :return: Словарь с настройками
        """
        if self.ocr_mode == "offline":
            return asdict(self.offline_settings)
        else:
            return asdict(self.online_settings)

    def get_sort_method_name(self, key: str = None) -> str:
        """
        Возвращает человекочитаемое название метода сортировки.

        :param key: Ключ метода (если None, используется текущий)
        :return: Название метода
        """
        method_key = key or self.sort_method

        for method in self.available_sort_methods:
            if method['key'] == method_key:
                return method['name']

        return method_key

    def get_available_prompts(self) -> List[str]:
        """
        Возвращает список доступных промптов.

        :return: Список названий промптов
        """
        # Этот метод будет дополнен интеграцией с PromptManager
        return ["classic_ocr", "math_formulas_ocr", "japanese_ocr", "table_ocr"]

    def reset_to_defaults(self) -> None:
        """Сбрасывает все настройки к значениям по умолчанию."""
        self.ocr_mode = "offline"
        self.sort_method = "natural"
        self.output_file = "result.txt"
        self.include_metadata = True

        self.offline_settings = OfflineSettings()
        self.online_settings = OnlineSettings()
        self.gui_settings = GUISettings()

        self._notify_observers()
        self.logger.info("Настройки сброшены к значениям по умолчанию")

    def export_settings(self, file_path: str) -> bool:
        """
        Экспортирует настройки в файл.

        :param file_path: Путь к файлу для экспорта
        :return: True если экспорт успешен
        """
        try:
            settings_data = {
                'ocr_mode': self.ocr_mode,
                'sort_method': self.sort_method,
                'output_file': self.output_file,
                'include_metadata': self.include_metadata,
                'offline_settings': asdict(self.offline_settings),
                'online_settings': asdict(self.online_settings),
                'gui_settings': asdict(self.gui_settings)
            }

            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(settings_data, file, ensure_ascii=False, indent=4)

            self.logger.info(f"Настройки экспортированы в: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка экспорта настроек: {e}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """
        Импортирует настройки из файла.

        :param file_path: Путь к файлу для импорта
        :return: True если импорт успешен
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                settings_data = json.load(file)

            # Импортируем базовые настройки
            self.ocr_mode = settings_data.get('ocr_mode', self.ocr_mode)
            self.sort_method = settings_data.get('sort_method', self.sort_method)
            self.output_file = settings_data.get('output_file', self.output_file)
            self.include_metadata = settings_data.get('include_metadata', self.include_metadata)

            # Импортируем настройки компонентов
            if 'offline_settings' in settings_data:
                offline_data = settings_data['offline_settings']
                for key, value in offline_data.items():
                    if hasattr(self.offline_settings, key):
                        setattr(self.offline_settings, key, value)

            if 'online_settings' in settings_data:
                online_data = settings_data['online_settings']
                for key, value in online_data.items():
                    if hasattr(self.online_settings, key):
                        setattr(self.online_settings, key, value)

            if 'gui_settings' in settings_data:
                gui_data = settings_data['gui_settings']
                for key, value in gui_data.items():
                    if hasattr(self.gui_settings, key):
                        setattr(self.gui_settings, key, value)

            self._notify_observers()
            self.logger.info(f"Настройки импортированы из: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка импорта настроек: {e}")
            return False

    def auto_save_if_enabled(self) -> None:
        """Автоматически сохраняет настройки если включено автосохранение."""
        if self.gui_settings.auto_save_settings:
            self.save_settings()
