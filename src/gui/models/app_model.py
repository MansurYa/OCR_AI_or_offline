"""
Модель состояния приложения.
Хранит текущее состояние GUI и управляет списком изображений для обработки.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImageFile:
    """Информация об одном файле изображения."""
    path: str
    filename: str
    size: int = 0
    is_valid: bool = True
    error_message: str = ""

    def __post_init__(self):
        """Инициализация после создания объекта."""
        if not self.filename:
            self.filename = os.path.basename(self.path)

        # Получаем размер файла если не указан
        if self.size == 0:
            try:
                self.size = os.path.getsize(self.path)
            except (OSError, IOError):
                self.size = 0
                self.is_valid = False
                self.error_message = "Не удалось получить размер файла"


@dataclass
class ProcessingState:
    """Состояние процесса OCR обработки."""
    is_running: bool = False
    current_file_index: int = 0
    total_files: int = 0
    current_filename: str = ""
    progress_percentage: float = 0.0
    estimated_time_remaining: float = 0.0
    can_cancel: bool = True


class AppModel:
    """
    Модель состояния приложения.
    Управляет списком изображений, настройками и состоянием обработки.
    """

    def __init__(self):
        """Инициализация модели приложения."""
        self.logger = logging.getLogger(__name__)

        # Список изображений для обработки
        self._image_files: List[ImageFile] = []

        # Состояние обработки
        self.processing_state = ProcessingState()

        # Поддерживаемые форматы изображений
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}

        # Колбэки для уведомления о изменениях
        self._observers: List[Callable[[], None]] = []
        self._processing_observers: List[Callable[[ProcessingState], None]] = []

    def add_observer(self, callback: Callable[[], None]) -> None:
        """
        Добавляет наблюдателя для изменений в списке файлов.

        :param callback: Функция обратного вызова
        """
        self._observers.append(callback)

    def add_processing_observer(self, callback: Callable[[ProcessingState], None]) -> None:
        """
        Добавляет наблюдателя для изменений состояния обработки.

        :param callback: Функция обратного вызова
        """
        self._processing_observers.append(callback)

    def _notify_observers(self) -> None:
        """Уведомляет всех наблюдателей об изменениях."""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Ошибка в observer callback: {e}")

    def _notify_processing_observers(self) -> None:
        """Уведомляет наблюдателей об изменениях состояния обработки."""
        for callback in self._processing_observers:
            try:
                callback(self.processing_state)
            except Exception as e:
                self.logger.error(f"Ошибка в processing observer callback: {e}")

    def add_images(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Добавляет изображения в список для обработки.

        :param file_paths: Список путей к файлам
        :return: Словарь с результатами добавления
        """
        added_files = []
        skipped_files = []
        invalid_files = []

        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    invalid_files.append(file_path)
                    continue

                # Проверяем, не добавлен ли уже этот файл
                if any(img.path == file_path for img in self._image_files):
                    skipped_files.append(file_path)
                    continue

                # Проверяем формат файла
                file_extension = Path(file_path).suffix.lower()
                if file_extension not in self.supported_formats:
                    invalid_files.append(file_path)
                    continue

                # Создаем объект ImageFile
                image_file = ImageFile(path=file_path, filename=os.path.basename(file_path))

                if image_file.is_valid:
                    self._image_files.append(image_file)
                    added_files.append(file_path)
                else:
                    invalid_files.append(file_path)

            except Exception as e:
                self.logger.error(f"Ошибка при добавлении файла {file_path}: {e}")
                invalid_files.append(file_path)

        if added_files:
            self._notify_observers()
            self.logger.info(f"Добавлено {len(added_files)} файлов")

        return {
            'added': added_files,
            'skipped': skipped_files,
            'invalid': invalid_files
        }

    def add_images_from_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, List[str]]:
        """
        Добавляет все изображения из директории.

        :param directory_path: Путь к директории
        :param recursive: Рекурсивный поиск в подпапках
        :return: Словарь с результатами добавления
        """
        try:
            directory = Path(directory_path)
            if not directory.exists() or not directory.is_dir():
                return {'added': [], 'skipped': [], 'invalid': [directory_path]}

            # Ищем файлы изображений
            image_files = []

            if recursive:
                for ext in self.supported_formats:
                    image_files.extend(directory.rglob(f"*{ext}"))
                    image_files.extend(directory.rglob(f"*{ext.upper()}"))
            else:
                for ext in self.supported_formats:
                    image_files.extend(directory.glob(f"*{ext}"))
                    image_files.extend(directory.glob(f"*{ext.upper()}"))

            # Преобразуем в строки путей
            file_paths = [str(path) for path in image_files]

            return self.add_images(file_paths)

        except Exception as e:
            self.logger.error(f"Ошибка при добавлении файлов из директории {directory_path}: {e}")
            return {'added': [], 'skipped': [], 'invalid': [directory_path]}

    def remove_image(self, index: int) -> bool:
        """
        Удаляет изображение из списка по индексу.

        :param index: Индекс изображения в списке
        :return: True если удаление успешно
        """
        try:
            if 0 <= index < len(self._image_files):
                removed_file = self._image_files.pop(index)
                self._notify_observers()
                self.logger.debug(f"Удален файл: {removed_file.filename}")
                return True
            else:
                self.logger.warning(f"Неверный индекс для удаления: {index}")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка при удалении файла с индексом {index}: {e}")
            return False

    def remove_image_by_path(self, file_path: str) -> bool:
        """
        Удаляет изображение из списка по пути к файлу.

        :param file_path: Путь к файлу
        :return: True если удаление успешно
        """
        try:
            for i, image_file in enumerate(self._image_files):
                if image_file.path == file_path:
                    return self.remove_image(i)

            self.logger.warning(f"Файл не найден для удаления: {file_path}")
            return False

        except Exception as e:
            self.logger.error(f"Ошибка при удалении файла {file_path}: {e}")
            return False

    def clear_images(self) -> None:
        """Очищает весь список изображений."""
        if self._image_files:
            self._image_files.clear()
            self._notify_observers()
            self.logger.info("Список изображений очищен")

    def move_image(self, from_index: int, to_index: int) -> bool:
        """
        Перемещает изображение в списке.

        :param from_index: Исходный индекс
        :param to_index: Целевой индекс
        :return: True если перемещение успешно
        """
        try:
            if (0 <= from_index < len(self._image_files) and
                0 <= to_index < len(self._image_files) and
                from_index != to_index):

                # Перемещаем элемент
                image_file = self._image_files.pop(from_index)
                self._image_files.insert(to_index, image_file)

                self._notify_observers()
                self.logger.debug(f"Файл перемещен с позиции {from_index} на {to_index}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Ошибка при перемещении файла: {e}")
            return False

    def get_image_files(self) -> List[ImageFile]:
        """
        Возвращает копию списка изображений.

        :return: Список изображений
        """
        return self._image_files.copy()

    def get_image_paths(self) -> List[str]:
        """
        Возвращает список путей к изображениям.

        :return: Список путей
        """
        return [img.path for img in self._image_files]

    def get_image_count(self) -> int:
        """
        Возвращает количество изображений в списке.

        :return: Количество изображений
        """
        return len(self._image_files)

    def get_valid_image_count(self) -> int:
        """
        Возвращает количество валидных изображений.

        :return: Количество валидных изображений
        """
        return sum(1 for img in self._image_files if img.is_valid)

    def get_total_size(self) -> int:
        """
        Возвращает общий размер всех изображений в байтах.

        :return: Общий размер в байтах
        """
        return sum(img.size for img in self._image_files if img.is_valid)

    def update_processing_state(self, **kwargs) -> None:
        """
        Обновляет состояние обработки.

        :param kwargs: Параметры для обновления
        """
        updated = False

        for key, value in kwargs.items():
            if hasattr(self.processing_state, key):
                setattr(self.processing_state, key, value)
                updated = True

        # Вычисляем прогресс в процентах
        if (self.processing_state.total_files > 0 and
            self.processing_state.current_file_index >= 0):
            self.processing_state.progress_percentage = (
                self.processing_state.current_file_index / self.processing_state.total_files * 100
            )

        if updated:
            self._notify_processing_observers()

    def start_processing(self, total_files: int) -> None:
        """
        Начинает процесс обработки.

        :param total_files: Общее количество файлов для обработки
        """
        self.processing_state.is_running = True
        self.processing_state.current_file_index = 0
        self.processing_state.total_files = total_files
        self.processing_state.current_filename = ""
        self.processing_state.progress_percentage = 0.0
        self.processing_state.can_cancel = True

        self._notify_processing_observers()
        self.logger.info(f"Начата обработка {total_files} файлов")

    def update_processing_progress(self, current_index: int, current_filename: str) -> None:
        """
        Обновляет прогресс обработки.

        :param current_index: Текущий индекс файла (1-based)
        :param current_filename: Имя текущего обрабатываемого файла
        """
        self.update_processing_state(
            current_file_index=current_index,
            current_filename=current_filename
        )

    def finish_processing(self) -> None:
        """Завершает процесс обработки."""
        self.processing_state.is_running = False
        self.processing_state.progress_percentage = 100.0
        self.processing_state.current_filename = ""

        self._notify_processing_observers()
        self.logger.info("Обработка завершена")

    def cancel_processing(self) -> None:
        """Отменяет процесс обработки."""
        if self.processing_state.can_cancel:
            self.processing_state.is_running = False
            self.processing_state.current_filename = "Отмена..."

            self._notify_processing_observers()
            self.logger.info("Обработка отменена пользователем")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по загруженным файлам.

        :return: Словарь со статистикой
        """
        valid_files = [img for img in self._image_files if img.is_valid]
        invalid_files = [img for img in self._image_files if not img.is_valid]

        total_size = sum(img.size for img in valid_files)

        # Группировка по расширениям
        extensions = {}
        for img in valid_files:
            ext = Path(img.path).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

        return {
            'total_files': len(self._image_files),
            'valid_files': len(valid_files),
            'invalid_files': len(invalid_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'extensions': extensions
        }

    def validate_all_files(self) -> None:
        """Перепроверяет валидность всех файлов."""
        updated = False

        for image_file in self._image_files:
            old_validity = image_file.is_valid

            # Проверяем существование файла
            if not os.path.exists(image_file.path):
                image_file.is_valid = False
                image_file.error_message = "Файл не найден"
            else:
                # Проверяем размер файла
                try:
                    size = os.path.getsize(image_file.path)
                    image_file.size = size
                    image_file.is_valid = True
                    image_file.error_message = ""
                except (OSError, IOError) as e:
                    image_file.is_valid = False
                    image_file.error_message = f"Ошибка доступа к файлу: {e}"

            if old_validity != image_file.is_valid:
                updated = True

        if updated:
            self._notify_observers()
            self.logger.info("Валидация файлов завершена")
