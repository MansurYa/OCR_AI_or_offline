"""
Презентер для управления процессом OCR обработки.
Специализированный presenter для детального управления OCR процессами.
"""

import os
import time
import logging
import threading
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

# Импорты из core
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.ocr_processor import OCRProcessor, OCRResult, OCRBatchResult


@dataclass
class OCRProgressInfo:
    """Детальная информация о прогрессе OCR."""
    current_file_index: int
    total_files: int
    current_filename: str
    current_file_path: str
    progress_percentage: float
    elapsed_time: float
    estimated_remaining_time: float
    current_file_size: int
    processing_speed: float  # файлов в секунду
    is_paused: bool = False
    can_pause: bool = True


class OCRPresenter:
    """
    Презентер для детального управления OCR обработкой.
    Предоставляет расширенный контроль над процессом OCR.
    """

    def __init__(self, ocr_processor: OCRProcessor):
        """
        Инициализация OCR презентера.

        :param ocr_processor: Экземпляр OCR процессора
        """
        self.logger = logging.getLogger(__name__)
        self.ocr_processor = ocr_processor

        # Состояние обработки
        self._is_processing = False
        self._is_paused = False
        self._is_cancelled = False

        # Статистика обработки
        self._start_time: Optional[float] = None
        self._processed_files = 0
        self._successful_files = 0
        self._failed_files = 0

        # Прогресс
        self._current_progress = OCRProgressInfo(
            current_file_index=0,
            total_files=0,
            current_filename="",
            current_file_path="",
            progress_percentage=0.0,
            elapsed_time=0.0,
            estimated_remaining_time=0.0,
            current_file_size=0,
            processing_speed=0.0
        )

        # События и колбэки
        self._progress_callbacks: List[Callable[[OCRProgressInfo], None]] = []
        self._completion_callbacks: List[Callable[[OCRBatchResult], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        # Синхронизация
        self._pause_event = threading.Event()
        self._pause_event.set()  # Изначально не на паузе

    def add_progress_callback(self, callback: Callable[[OCRProgressInfo], None]) -> None:
        """
        Добавляет колбэк для обновления прогресса.

        :param callback: Функция обратного вызова
        """
        self._progress_callbacks.append(callback)

    def add_completion_callback(self, callback: Callable[[OCRBatchResult], None]) -> None:
        """
        Добавляет колбэк для завершения обработки.

        :param callback: Функция обратного вызова
        """
        self._completion_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        Добавляет колбэк для обработки ошибок.

        :param callback: Функция обратного вызова
        """
        self._error_callbacks.append(callback)

    def _notify_progress(self) -> None:
        """Уведомляет колбэки о прогрессе."""
        for callback in self._progress_callbacks:
            try:
                callback(self._current_progress)
            except Exception as e:
                self.logger.error(f"Ошибка в progress callback: {e}")

    def _notify_completion(self, result: OCRBatchResult) -> None:
        """
        Уведомляет колбэки о завершении.

        :param result: Результат обработки
        """
        for callback in self._completion_callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logger.error(f"Ошибка в completion callback: {e}")

    def _notify_error(self, error_message: str) -> None:
        """
        Уведомляет колбэки об ошибке.

        :param error_message: Сообщение об ошибке
        """
        for callback in self._error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Ошибка в error callback: {e}")

    def start_processing(self, image_paths: List[str],
                        output_file: str,
                        mode: str = "offline",
                        sort_method: str = "natural",
                        **processing_kwargs) -> bool:
        """
        Запускает процесс OCR обработки.

        :param image_paths: Список путей к изображениям
        :param output_file: Путь к выходному файлу
        :param mode: Режим обработки ("offline" или "online")
        :param sort_method: Метод сортировки файлов
        :param processing_kwargs: Дополнительные параметры обработки
        :return: True если обработка запущена успешно
        """
        if self._is_processing:
            self.logger.warning("Обработка уже выполняется")
            return False

        if not image_paths:
            self.logger.error("Нет файлов для обработки")
            return False

        # Инициализируем состояние
        self._is_processing = True
        self._is_paused = False
        self._is_cancelled = False
        self._start_time = time.time()
        self._processed_files = 0
        self._successful_files = 0
        self._failed_files = 0

        # Настраиваем прогресс
        self._current_progress.total_files = len(image_paths)
        self._current_progress.current_file_index = 0
        self._current_progress.progress_percentage = 0.0
        self._current_progress.is_paused = False

        # Запускаем обработку в отдельном потоке
        processing_thread = threading.Thread(
            target=self._process_images_thread,
            args=(image_paths, output_file, mode, sort_method, processing_kwargs),
            daemon=True
        )
        processing_thread.start()

        self.logger.info(f"Начата OCR обработка {len(image_paths)} файлов в режиме {mode}")
        return True

    def _process_images_thread(self, image_paths: List[str],
                             output_file: str,
                             mode: str,
                             sort_method: str,
                             processing_kwargs: Dict[str, Any]) -> None:
        """
        Выполняет обработку изображений в отдельном потоке.

        :param image_paths: Список путей к изображениям
        :param output_file: Путь к выходному файлу
        :param mode: Режим обработки
        :param sort_method: Метод сортировки
        :param processing_kwargs: Дополнительные параметры
        """
        try:
            # Настраиваем прогресс callback
            self.ocr_processor.set_progress_callback(self._on_file_progress)

            # Запускаем обработку
            result = self.ocr_processor.process_batch(
                image_paths=image_paths,
                output_file=output_file,
                mode=mode,
                sort_method=sort_method,
                **processing_kwargs
            )

            # Обработка завершена успешно
            if not self._is_cancelled:
                self._on_processing_completed(result)

        except Exception as e:
            error_message = f"Ошибка при обработке: {str(e)}"
            self.logger.error(error_message)
            self._notify_error(error_message)

        finally:
            self._is_processing = False
            self._is_paused = False

    def _on_file_progress(self, current: int, total: int, filename: str) -> None:
        """
        Обработчик прогресса обработки файла.

        :param current: Текущий индекс файла
        :param total: Общее количество файлов
        :param filename: Имя текущего файла
        """
        # Проверяем на отмену
        if self._is_cancelled:
            return

        # Ждем если на паузе
        self._pause_event.wait()

        # Обновляем статистику
        elapsed_time = time.time() - self._start_time if self._start_time else 0

        # Вычисляем скорость обработки
        processing_speed = current / elapsed_time if elapsed_time > 0 else 0

        # Оценка оставшегося времени
        remaining_files = total - current
        estimated_remaining = remaining_files / processing_speed if processing_speed > 0 else 0

        # Получаем размер текущего файла
        current_file_path = ""
        current_file_size = 0

        # Находим полный путь файла по имени (упрощенный поиск)
        for path in self.ocr_processor.get_image_paths() if hasattr(self.ocr_processor, 'get_image_paths') else []:
            if os.path.basename(path) == filename:
                current_file_path = path
                try:
                    current_file_size = os.path.getsize(path)
                except (OSError, IOError):
                    current_file_size = 0
                break

        # Обновляем прогресс
        self._current_progress.current_file_index = current
        self._current_progress.current_filename = filename
        self._current_progress.current_file_path = current_file_path
        self._current_progress.progress_percentage = (current / total) * 100
        self._current_progress.elapsed_time = elapsed_time
        self._current_progress.estimated_remaining_time = estimated_remaining
        self._current_progress.current_file_size = current_file_size
        self._current_progress.processing_speed = processing_speed
        self._current_progress.is_paused = self._is_paused

        # Уведомляем подписчиков
        self._notify_progress()

    def _on_processing_completed(self, result: OCRBatchResult) -> None:
        """
        Обработчик завершения обработки.

        :param result: Результат обработки
        """
        # Обновляем финальную статистику
        self._successful_files = result.successful_files
        self._failed_files = result.total_files - result.successful_files

        # Финальное обновление прогресса
        self._current_progress.progress_percentage = 100.0
        self._current_progress.current_filename = "Завершено"
        self._notify_progress()

        # Уведомляем о завершении
        self._notify_completion(result)

        self.logger.info(
            f"OCR обработка завершена: {result.successful_files}/{result.total_files} файлов за "
            f"{result.total_processing_time:.2f}с"
        )

    def pause_processing(self) -> bool:
        """
        Приостанавливает обработку.

        :return: True если пауза установлена
        """
        if not self._is_processing or self._is_paused:
            return False

        self._is_paused = True
        self._pause_event.clear()

        # Обновляем состояние прогресса
        self._current_progress.is_paused = True
        self._current_progress.current_filename = "Пауза..."
        self._notify_progress()

        self.logger.info("OCR обработка приостановлена")
        return True

    def resume_processing(self) -> bool:
        """
        Возобновляет обработку.

        :return: True если обработка возобновлена
        """
        if not self._is_processing or not self._is_paused:
            return False

        self._is_paused = False
        self._pause_event.set()

        # Обновляем состояние прогресса
        self._current_progress.is_paused = False
        self._notify_progress()

        self.logger.info("OCR обработка возобновлена")
        return True

    def cancel_processing(self) -> bool:
        """
        Отменяет обработку.

        :return: True если отмена выполнена
        """
        if not self._is_processing:
            return False

        self._is_cancelled = True

        # Снимаем паузу если она была
        if self._is_paused:
            self._pause_event.set()

        # Обновляем состояние прогресса
        self._current_progress.current_filename = "Отмена..."
        self._notify_progress()

        self.logger.info("OCR обработка отменена")
        return True

    def get_current_progress(self) -> OCRProgressInfo:
        """
        Возвращает текущий прогресс обработки.

        :return: Информация о прогрессе
        """
        return self._current_progress

    def is_processing(self) -> bool:
        """
        Проверяет, выполняется ли обработка.

        :return: True если обработка выполняется
        """
        return self._is_processing

    def is_paused(self) -> bool:
        """
        Проверяет, приостановлена ли обработка.

        :return: True если обработка приостановлена
        """
        return self._is_paused

    def can_pause(self) -> bool:
        """
        Проверяет, можно ли приостановить обработку.

        :return: True если можно приостановить
        """
        return self._is_processing and not self._is_paused and self._current_progress.can_pause

    def can_resume(self) -> bool:
        """
        Проверяет, можно ли возобновить обработку.

        :return: True если можно возобновить
        """
        return self._is_processing and self._is_paused

    def can_cancel(self) -> bool:
        """
        Проверяет, можно ли отменить обработку.

        :return: True если можно отменить
        """
        return self._is_processing

    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Возвращает детальную статистику обработки.

        :return: Словарь со статистикой
        """
        elapsed_time = time.time() - self._start_time if self._start_time else 0

        return {
            'is_processing': self._is_processing,
            'is_paused': self._is_paused,
            'is_cancelled': self._is_cancelled,
            'processed_files': self._processed_files,
            'successful_files': self._successful_files,
            'failed_files': self._failed_files,
            'total_files': self._current_progress.total_files,
            'elapsed_time': elapsed_time,
            'processing_speed': self._current_progress.processing_speed,
            'estimated_remaining_time': self._current_progress.estimated_remaining_time,
            'progress_percentage': self._current_progress.progress_percentage
        }

    def estimate_total_time(self, file_count: int, mode: str = "offline") -> float:
        """
        Оценивает общее время обработки.

        :param file_count: Количество файлов
        :param mode: Режим обработки
        :return: Оценочное время в секундах
        """
        if mode == "online" and hasattr(self.ocr_processor, 'online_processor'):
            return self.ocr_processor.online_processor.estimate_processing_time(file_count)
        else:
            # Оценка для offline режима
            return file_count * 2.0  # 2 секунды на файл

    def get_detailed_file_progress(self) -> Dict[str, Any]:
        """
        Возвращает детальную информацию о текущем обрабатываемом файле.

        :return: Словарь с информацией о файле
        """
        return {
            'filename': self._current_progress.current_filename,
            'file_path': self._current_progress.current_file_path,
            'file_size': self._current_progress.current_file_size,
            'file_index': self._current_progress.current_file_index,
            'total_files': self._current_progress.total_files,
            'file_progress_percentage': (
                (self._current_progress.current_file_index / self._current_progress.total_files * 100)
                if self._current_progress.total_files > 0 else 0
            )
        }
