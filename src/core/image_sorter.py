"""
Сортировка изображений по различным критериям.
Поддерживает natural sort, сортировку по времени, размеру и другие алгоритмы.
"""

import os
import re
import logging
from typing import List, Callable, Any
from pathlib import Path


class ImageSorter:
    """
    Класс для сортировки списка изображений по различным критериям.
    """

    def __init__(self):
        """Инициализация сортировщика изображений."""
        self.logger = logging.getLogger(__name__)

        # Регистр доступных методов сортировки
        self.sort_methods = {
            'natural': self._sort_natural,
            'alphabetical': self._sort_alphabetical,
            'creation_time': self._sort_by_creation_time,
            'modification_time': self._sort_by_modification_time,
            'file_size': self._sort_by_file_size,
            'file_size_desc': self._sort_by_file_size_desc,
            'reverse_alphabetical': self._sort_reverse_alphabetical,
            'random': self._sort_random
        }

    def sort_files(self, file_paths: List[str], method: str = "natural") -> List[str]:
        """
        Сортирует список файлов по указанному методу.

        :param file_paths: Список путей к файлам
        :param method: Метод сортировки
        :return: Отсортированный список путей
        :raises ValueError: Если метод сортировки неизвестен
        """
        if not file_paths:
            return []

        if method not in self.sort_methods:
            available_methods = list(self.sort_methods.keys())
            raise ValueError(
                f"Неизвестный метод сортировки: {method}. "
                f"Доступные методы: {available_methods}"
            )

        try:
            sort_function = self.sort_methods[method]
            sorted_paths = sort_function(file_paths.copy())

            self.logger.debug(f"Файлы отсортированы методом '{method}': {len(sorted_paths)} файлов")
            return sorted_paths

        except Exception as e:
            self.logger.error(f"Ошибка при сортировке методом '{method}': {e}")
            # Возвращаем исходный список в случае ошибки
            return file_paths.copy()

    def _natural_sort_key(self, text: str) -> List[Any]:
        """
        Создает ключ для естественной сортировки (учитывает числа).

        Примеры:
        - "file1.jpg", "file2.jpg", "file10.jpg" -> правильный порядок
        - "image-001.png", "image-002.png", "image-010.png" -> правильный порядок

        :param text: Текст для создания ключа
        :return: Ключ сортировки
        """
        def convert_part(part):
            """Конвертирует часть строки в число или оставляет как строку"""
            return int(part) if part.isdigit() else part.lower()

        # Разбиваем строку на части (числовые и текстовые)
        parts = re.split(r'(\d+)', text)
        return [convert_part(part) for part in parts]

    def _sort_natural(self, file_paths: List[str]) -> List[str]:
        """
        Естественная сортировка с учетом чисел в именах файлов.

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=lambda x: self._natural_sort_key(os.path.basename(x)))

    def _sort_alphabetical(self, file_paths: List[str]) -> List[str]:
        """
        Алфавитная сортировка по имени файла.

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=lambda x: os.path.basename(x).lower())

    def _sort_reverse_alphabetical(self, file_paths: List[str]) -> List[str]:
        """
        Обратная алфавитная сортировка по имени файла.

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=lambda x: os.path.basename(x).lower(), reverse=True)

    def _get_file_creation_time(self, file_path: str) -> float:
        """
        Получает время создания файла.

        :param file_path: Путь к файлу
        :return: Время создания в секундах с эпохи Unix
        """
        try:
            stat_info = os.stat(file_path)
            # В Windows используем st_ctime, в Unix st_birthtime если доступно
            if hasattr(stat_info, 'st_birthtime'):
                return stat_info.st_birthtime
            else:
                return stat_info.st_ctime
        except (OSError, IOError):
            # Если не удается получить время создания, используем время изменения
            return self._get_file_modification_time(file_path)

    def _get_file_modification_time(self, file_path: str) -> float:
        """
        Получает время последнего изменения файла.

        :param file_path: Путь к файлу
        :return: Время изменения в секундах с эпохи Unix
        """
        try:
            return os.path.getmtime(file_path)
        except (OSError, IOError):
            # Если не удается получить время, возвращаем 0
            return 0.0

    def _get_file_size(self, file_path: str) -> int:
        """
        Получает размер файла в байтах.

        :param file_path: Путь к файлу
        :return: Размер файла в байтах
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, IOError):
            # Если не удается получить размер, возвращаем 0
            return 0

    def _sort_by_creation_time(self, file_paths: List[str]) -> List[str]:
        """
        Сортировка по времени создания файла (от старых к новым).

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=self._get_file_creation_time)

    def _sort_by_modification_time(self, file_paths: List[str]) -> List[str]:
        """
        Сортировка по времени последнего изменения файла (от старых к новым).

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=self._get_file_modification_time)

    def _sort_by_file_size(self, file_paths: List[str]) -> List[str]:
        """
        Сортировка по размеру файла (от маленьких к большим).

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=self._get_file_size)

    def _sort_by_file_size_desc(self, file_paths: List[str]) -> List[str]:
        """
        Сортировка по размеру файла (от больших к маленьким).

        :param file_paths: Список путей к файлам
        :return: Отсортированный список
        """
        return sorted(file_paths, key=self._get_file_size, reverse=True)

    def _sort_random(self, file_paths: List[str]) -> List[str]:
        """
        Случайная перестановка файлов.

        :param file_paths: Список путей к файлам
        :return: Перемешанный список
        """
        import random
        shuffled = file_paths.copy()
        random.shuffle(shuffled)
        return shuffled

    def get_available_methods(self) -> List[str]:
        """
        Возвращает список доступных методов сортировки.

        :return: Список названий методов
        """
        return list(self.sort_methods.keys())

    def get_method_description(self, method: str) -> str:
        """
        Возвращает описание метода сортировки.

        :param method: Название метода
        :return: Описание метода
        """
        descriptions = {
            'natural': 'Естественная сортировка (учитывает числа в именах)',
            'alphabetical': 'Алфавитная сортировка по имени файла',
            'creation_time': 'По времени создания файла (старые → новые)',
            'modification_time': 'По времени изменения файла (старые → новые)',
            'file_size': 'По размеру файла (маленькие → большие)',
            'file_size_desc': 'По размеру файла (большие → маленькие)',
            'reverse_alphabetical': 'Обратная алфавитная сортировка',
            'random': 'Случайная перестановка'
        }

        return descriptions.get(method, 'Описание недоступно')

    def analyze_file_patterns(self, file_paths: List[str]) -> dict:
        """
        Анализирует паттерны в именах файлов для рекомендации оптимального метода сортировки.

        :param file_paths: Список путей к файлам
        :return: Словарь с анализом и рекомендациями
        """
        if not file_paths:
            return {'recommendation': 'natural', 'reason': 'Нет файлов для анализа'}

        basenames = [os.path.basename(path) for path in file_paths]

        # Анализируем наличие чисел в именах
        has_numbers = any(re.search(r'\d+', name) for name in basenames)

        # Анализируем паттерны нумерации
        sequential_pattern = self._detect_sequential_pattern(basenames)

        # Анализируем временные паттерны
        time_variance = self._analyze_time_variance(file_paths)

        # Формируем рекомендацию
        if sequential_pattern:
            recommendation = 'natural'
            reason = 'Обнаружена последовательная нумерация в именах файлов'
        elif has_numbers:
            recommendation = 'natural'
            reason = 'В именах файлов присутствуют числа'
        elif time_variance > 3600:  # Больше часа разброса
            recommendation = 'creation_time'
            reason = 'Значительный разброс во времени создания файлов'
        else:
            recommendation = 'alphabetical'
            reason = 'Стандартная алфавитная сортировка'

        return {
            'recommendation': recommendation,
            'reason': reason,
            'has_numbers': has_numbers,
            'sequential_pattern': sequential_pattern,
            'time_variance_hours': time_variance / 3600
        }

    def _detect_sequential_pattern(self, basenames: List[str]) -> bool:
        """
        Определяет наличие последовательной нумерации в именах файлов.

        :param basenames: Список базовых имен файлов
        :return: True если обнаружена последовательность
        """
        # Извлекаем числа из имен файлов
        numbers = []
        for name in basenames:
            matches = re.findall(r'\d+', name)
            if matches:
                # Берем последнее (самое правое) число как потенциальный индекс
                numbers.append(int(matches[-1]))

        if len(numbers) < 2:
            return False

        # Проверяем, образуют ли числа последовательность
        numbers.sort()

        # Проверяем арифметическую прогрессию
        if len(numbers) >= 3:
            differences = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            # Если все разности одинаковы (или почти одинаковы), это последовательность
            return len(set(differences)) <= 2

        return False

    def _analyze_time_variance(self, file_paths: List[str]) -> float:
        """
        Анализирует разброс во времени создания файлов.

        :param file_paths: Список путей к файлам
        :return: Максимальная разность времени в секундах
        """
        if len(file_paths) < 2:
            return 0.0

        times = [self._get_file_creation_time(path) for path in file_paths]
        times = [t for t in times if t > 0]  # Убираем некорректные значения

        if len(times) < 2:
            return 0.0

        return max(times) - min(times)

    def sort_with_custom_key(self, file_paths: List[str],
                           key_function: Callable[[str], Any],
                           reverse: bool = False) -> List[str]:
        """
        Сортирует файлы с пользовательской функцией ключа.

        :param file_paths: Список путей к файлам
        :param key_function: Функция для создания ключа сортировки
        :param reverse: Обратный порядок сортировки
        :return: Отсортированный список
        """
        try:
            return sorted(file_paths, key=key_function, reverse=reverse)
        except Exception as e:
            self.logger.error(f"Ошибка в пользовательской сортировке: {e}")
            return file_paths.copy()
