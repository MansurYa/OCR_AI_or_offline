"""
Управление OCR промптами.
Загрузка, валидация и кэширование промптов из директории OCR_prompts.
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path


class PromptManager:
    """
    Менеджер для управления OCR промптами.
    Обеспечивает загрузку, кэширование и валидацию промптов.
    """

    def __init__(self, prompts_directory: str = "OCR_prompts"):
        """
        Инициализация менеджера промптов.

        :param prompts_directory: Директория с промптами
        """
        self.prompts_directory = Path(prompts_directory)
        self.logger = logging.getLogger(__name__)
        self._prompt_cache: Dict[str, str] = {}
        self._prompt_metadata: Dict[str, Dict] = {}

        # Создаем директорию если не существует
        self._ensure_prompts_directory()

        # Загружаем промпты при инициализации
        self._load_all_prompts()

    def _ensure_prompts_directory(self) -> None:
        """
        Создает директорию промптов если она не существует.
        """
        try:
            self.prompts_directory.mkdir(exist_ok=True)
            self.logger.info(f"Директория промптов: {self.prompts_directory}")
        except Exception as e:
            self.logger.error(f"Не удалось создать директорию промптов: {e}")
            raise

    def _load_all_prompts(self) -> None:
        """
        Загружает все промпты из директории в кэш.
        """
        if not self.prompts_directory.exists():
            self.logger.warning(f"Директория промптов не существует: {self.prompts_directory}")
            return

        prompt_files = list(self.prompts_directory.glob("*.txt"))

        if not prompt_files:
            self.logger.warning(f"Не найдено промптов в директории: {self.prompts_directory}")
            # Создаем базовый промпт если нет никаких файлов
            self._create_default_prompt()
            return

        loaded_count = 0
        for prompt_file in prompt_files:
            try:
                prompt_name = prompt_file.stem  # Имя файла без расширения
                content = self._load_prompt_file(prompt_file)

                if content:
                    self._prompt_cache[prompt_name] = content
                    self._prompt_metadata[prompt_name] = {
                        'file_path': str(prompt_file),
                        'file_size': prompt_file.stat().st_size,
                        'modified_time': prompt_file.stat().st_mtime,
                        'valid': self._validate_prompt_content(content)
                    }
                    loaded_count += 1

            except Exception as e:
                self.logger.error(f"Ошибка загрузки промпта {prompt_file}: {e}")

        self.logger.info(f"Загружено {loaded_count} промптов из {len(prompt_files)} файлов")

    def _load_prompt_file(self, file_path: Path) -> Optional[str]:
        """
        Загружает содержимое файла промпта.

        :param file_path: Путь к файлу промпта
        :return: Содержимое файла или None при ошибке
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()

            if not content:
                self.logger.warning(f"Файл промпта пуст: {file_path}")
                return None

            return content

        except UnicodeDecodeError as e:
            self.logger.error(f"Ошибка кодировки при чтении {file_path}: {e}")
            # Пытаемся с другой кодировкой
            try:
                with open(file_path, 'r', encoding='cp1251') as file:
                    return file.read().strip()
            except Exception:
                return None

        except Exception as e:
            self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return None

    def _validate_prompt_content(self, content: str) -> bool:
        """
        Валидирует содержимое промпта.

        :param content: Содержимое промпта
        :return: True если промпт валиден
        """
        if not content or len(content.strip()) < 10:
            return False

        # Проверяем наличие базовых инструкций
        content_lower = content.lower()

        # Ключевые слова, которые должны присутствовать в OCR промпте
        required_keywords = ['текст', 'изображен']
        helpful_keywords = ['точно', 'распознай', 'перепиши', 'ocr']

        has_required = any(keyword in content_lower for keyword in required_keywords)
        has_helpful = any(keyword in content_lower for keyword in helpful_keywords)

        return has_required or has_helpful

    def _create_default_prompt(self) -> None:
        """
        Создает базовый промпт по умолчанию.
        """
        default_prompt = """Перепиши весь текст с изображения точно как он написан.

ИНСТРУКЦИИ:
1. Переписывай каждое слово в точности как оно написано
2. Сохраняй все знаки препинания и форматирование
3. Не исправляй орфографические ошибки в оригинале
4. Если текст неразборчив, используй [неразборчиво]

РЕЗУЛЬТАТ: Только чистый текст с изображения."""

        try:
            default_file = self.prompts_directory / "classic_ocr.txt"
            with open(default_file, 'w', encoding='utf-8') as file:
                file.write(default_prompt)

            self._prompt_cache["classic_ocr"] = default_prompt
            self._prompt_metadata["classic_ocr"] = {
                'file_path': str(default_file),
                'file_size': len(default_prompt),
                'modified_time': default_file.stat().st_mtime,
                'valid': True
            }

            self.logger.info("Создан базовый промпт по умолчанию")

        except Exception as e:
            self.logger.error(f"Не удалось создать базовый промпт: {e}")

    def load_prompt(self, prompt_name: str) -> str:
        """
        Загружает промпт по имени.

        :param prompt_name: Имя промпта (без расширения .txt)
        :return: Содержимое промпта
        :raises ValueError: Если промпт не найден
        """
        # Сначала проверяем кэш
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]

        # Пытаемся загрузить из файла
        prompt_file = self.prompts_directory / f"{prompt_name}.txt"

        if not prompt_file.exists():
            available_prompts = self.get_available_prompts()
            raise ValueError(
                f"Промпт '{prompt_name}' не найден. "
                f"Доступные промпты: {available_prompts}"
            )

        # Загружаем и добавляем в кэш
        content = self._load_prompt_file(prompt_file)
        if content:
            self._prompt_cache[prompt_name] = content
            self._prompt_metadata[prompt_name] = {
                'file_path': str(prompt_file),
                'file_size': prompt_file.stat().st_size,
                'modified_time': prompt_file.stat().st_mtime,
                'valid': self._validate_prompt_content(content)
            }
            return content
        else:
            raise ValueError(f"Не удалось загрузить промпт '{prompt_name}'")

    def get_available_prompts(self) -> List[str]:
        """
        Возвращает список доступных промптов.

        :return: Список имен промптов
        """
        # Объединяем промпты из кэша и файлов
        cached_prompts = set(self._prompt_cache.keys())

        file_prompts = set()
        if self.prompts_directory.exists():
            for prompt_file in self.prompts_directory.glob("*.txt"):
                file_prompts.add(prompt_file.stem)

        all_prompts = sorted(cached_prompts.union(file_prompts))
        return all_prompts

    def get_prompt_info(self, prompt_name: str) -> Optional[Dict]:
        """
        Возвращает информацию о промпте.

        :param prompt_name: Имя промпта
        :return: Словарь с информацией или None если промпт не найден
        """
        if prompt_name not in self._prompt_metadata:
            # Пытаемся загрузить если есть файл
            try:
                self.load_prompt(prompt_name)
            except ValueError:
                return None

        metadata = self._prompt_metadata.get(prompt_name, {}).copy()

        if prompt_name in self._prompt_cache:
            content = self._prompt_cache[prompt_name]
            metadata.update({
                'content_length': len(content),
                'line_count': content.count('\n') + 1,
                'cached': True
            })

        return metadata

    def save_prompt(self, prompt_name: str, content: str) -> bool:
        """
        Сохраняет промпт в файл и кэш.

        :param prompt_name: Имя промпта
        :param content: Содержимое промпта
        :return: True если сохранение успешно
        """
        if not content or not content.strip():
            self.logger.error("Попытка сохранить пустой промпт")
            return False

        try:
            prompt_file = self.prompts_directory / f"{prompt_name}.txt"

            with open(prompt_file, 'w', encoding='utf-8') as file:
                file.write(content.strip())

            # Обновляем кэш
            self._prompt_cache[prompt_name] = content.strip()
            self._prompt_metadata[prompt_name] = {
                'file_path': str(prompt_file),
                'file_size': prompt_file.stat().st_size,
                'modified_time': prompt_file.stat().st_mtime,
                'valid': self._validate_prompt_content(content)
            }

            self.logger.info(f"Промпт '{prompt_name}' успешно сохранен")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения промпта '{prompt_name}': {e}")
            return False

    def delete_prompt(self, prompt_name: str) -> bool:
        """
        Удаляет промпт из файла и кэша.

        :param prompt_name: Имя промпта
        :return: True если удаление успешно
        """
        try:
            prompt_file = self.prompts_directory / f"{prompt_name}.txt"

            # Удаляем файл если существует
            if prompt_file.exists():
                prompt_file.unlink()

            # Удаляем из кэша
            self._prompt_cache.pop(prompt_name, None)
            self._prompt_metadata.pop(prompt_name, None)

            self.logger.info(f"Промпт '{prompt_name}' удален")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка удаления промпта '{prompt_name}': {e}")
            return False

    def refresh_prompts(self) -> None:
        """
        Перезагружает все промпты из файлов.
        """
        self.logger.info("Перезагружаем промпты...")
        self._prompt_cache.clear()
        self._prompt_metadata.clear()
        self._load_all_prompts()

    def get_prompt_with_variables(self, prompt_name: str, **variables) -> str:
        """
        Загружает промпт и заменяет переменные.

        :param prompt_name: Имя промпта
        :param variables: Переменные для замены в промпте
        :return: Промпт с замененными переменными
        """
        prompt_content = self.load_prompt(prompt_name)

        # Заменяем переменные в формате {variable_name}
        try:
            return prompt_content.format(**variables)
        except KeyError as e:
            self.logger.warning(f"Не найдена переменная {e} в промпте '{prompt_name}'")
            return prompt_content
        except Exception as e:
            self.logger.error(f"Ошибка подстановки переменных в промпте '{prompt_name}': {e}")
            return prompt_content

    def validate_all_prompts(self) -> Dict[str, bool]:
        """
        Валидирует все загруженные промпты.

        :return: Словарь с результатами валидации
        """
        results = {}

        for prompt_name in self.get_available_prompts():
            try:
                content = self.load_prompt(prompt_name)
                results[prompt_name] = self._validate_prompt_content(content)
            except Exception:
                results[prompt_name] = False

        return results

    def get_prompts_summary(self) -> Dict:
        """
        Возвращает сводную информацию о всех промптах.

        :return: Словарь со сводной информацией
        """
        available_prompts = self.get_available_prompts()
        validation_results = self.validate_all_prompts()

        total_size = 0
        valid_count = 0

        for prompt_name in available_prompts:
            info = self.get_prompt_info(prompt_name)
            if info:
                total_size += info.get('file_size', 0)

            if validation_results.get(prompt_name, False):
                valid_count += 1

        return {
            'total_prompts': len(available_prompts),
            'valid_prompts': valid_count,
            'invalid_prompts': len(available_prompts) - valid_count,
            'total_size_bytes': total_size,
            'prompts_directory': str(self.prompts_directory),
            'cached_prompts': len(self._prompt_cache)
        }
