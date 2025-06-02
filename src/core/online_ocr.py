"""
Online OCR обработка с использованием LLM.
Включает распараллеливание и интеграцию с LLM_manager.
"""

import time
import logging
import concurrent.futures
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

# Импорт из существующей системы LLM
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.LLM_manager import ChatLLMAgent
from .types import OCRResult  # Импорт из родительского модуля


class OnlineOCRProcessor:
    """
    Процессор для online OCR с использованием LLM.
    Поддерживает распараллеливание и различные промпты.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация online OCR процессора.

        :param config: Конфигурация приложения
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ocr_settings = config.get('ocr_settings', {}).get('online', {})

        # Настройки LLM
        self.llm_agent = self._create_llm_agent()

        # Настройки обработки
        self.max_threads = self.ocr_settings.get('max_threads', 5)
        self.timeout_seconds = self.ocr_settings.get('timeout_seconds', 30)
        self.retry_attempts = self.ocr_settings.get('retry_attempts', 3)

    def _create_llm_agent(self) -> ChatLLMAgent:
        """
        Создает экземпляр LLM агента на основе конфигурации.

        :return: Настроенный ChatLLMAgent
        :raises ValueError: Если конфигурация некорректна
        """
        try:
            # Извлекаем параметры из конфигурации
            model_name = self.config.get("model_name", "gpt-4o-mini")
            openai_api_key = self.config.get("openai_api_key")
            openai_organization = self.config.get("openai_organization")
            openrouter_api_key = self.config.get("openrouter_api_key")
            use_openai_or_openrouter = self.config.get("use_openai_or_openrouter", "openai")

            max_total_tokens = self.config.get("max_total_tokens", 30000)
            max_response_tokens = self.config.get("max_response_tokens", 4095)
            temperature = self.config.get("temperature", 0.1)

            # Проверяем наличие необходимых ключей
            if use_openai_or_openrouter == "openai":
                if not openai_api_key or not openai_organization:
                    raise ValueError("Для OpenAI требуются openai_api_key и openai_organization")
            elif use_openai_or_openrouter == "openrouter":
                if not openrouter_api_key:
                    raise ValueError("Для OpenRouter требуется openrouter_api_key")
            else:
                raise ValueError(f"Неподдерживаемый провайдер: {use_openai_or_openrouter}")

            # Создаем агента
            agent = ChatLLMAgent(
                model_name=model_name,
                openai_api_key=openai_api_key,
                openai_organization=openai_organization,
                openrouter_api_key=openrouter_api_key,
                use_openai_or_openrouter=use_openai_or_openrouter,
                mode=1,  # Очистка контекста перед каждым новым сообщением
                task_prompt="Ты точный OCR ассистент. Твоя задача - максимально точно распознать весь текст с изображения.",
                max_total_tokens=max_total_tokens,
                max_response_tokens=max_response_tokens,
                temperature=temperature
            )

            self.logger.info(f"LLM агент создан: {model_name} через {use_openai_or_openrouter}")
            return agent

        except Exception as e:
            error_msg = f"Ошибка создания LLM агента: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e

# ИСПРАВЛЕНИЕ для src/core/online_ocr.py
# Заменить метод _process_single_image в строке с agent_clone:

    def _process_single_image(self, image_path: str, prompt_text: str) -> OCRResult:
        """
        Обрабатывает одно изображение с использованием LLM.

        :param image_path: Путь к изображению
        :param prompt_text: Промпт для OCR
        :return: Результат OCR обработки
        """
        start_time = time.time()

        try:
            # Проверяем существование файла
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Файл не найден: {image_path}")

            # Выполняем OCR с повторными попытками
            last_error = None
            for attempt in range(self.retry_attempts):
                try:
                    # ИСПРАВЛЕНИЕ: Используем оригинальный агент напрямую вместо клонирования
                    # так как метод clone() может отсутствовать в LLM_manager

                    # Отправляем запрос к LLM
                    response = self.llm_agent.response_from_LLM(
                        user_message=prompt_text,
                        images=[image_path]
                    )

                    if response and response.strip():
                        processing_time = time.time() - start_time

                        result = OCRResult(
                            file_path=image_path,
                            success=True,
                            text_content=response.strip(),
                            processing_time=processing_time
                        )

                        self.logger.debug(
                            f"Файл {image_path} обработан за {processing_time:.2f}с "
                            f"(попытка {attempt + 1}), извлечено {len(response)} символов"
                        )

                        return result
                    else:
                        raise ValueError("Получен пустой ответ от LLM")

                except Exception as e:
                    last_error = e
                    if attempt < self.retry_attempts - 1:
                        wait_time = (attempt + 1) * 2  # Экспоненциальная задержка
                        self.logger.warning(
                            f"Попытка {attempt + 1} неудачна для {image_path}: {e}. "
                            f"Повтор через {wait_time}с"
                        )
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Все попытки исчерпаны для {image_path}: {e}")

            # Если все попытки неудачны
            processing_time = time.time() - start_time
            error_message = f"Ошибка обработки {image_path}: {last_error}"

            return OCRResult(
                file_path=image_path,
                success=False,
                text_content="",
                error_message=error_message,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Критическая ошибка при обработке {image_path}: {str(e)}"

            result = OCRResult(
                file_path=image_path,
                success=False,
                text_content="",
                error_message=error_message,
                processing_time=processing_time
            )

            self.logger.error(error_message)
            return result

    def process_images_batch(self, image_paths: List[str],
                           prompt_text: str,
                           max_threads: Optional[int] = None,
                           progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[OCRResult]:
        """
        Обрабатывает список изображений параллельно.

        :param image_paths: Список путей к изображениям
        :param prompt_text: Промпт для OCR
        :param max_threads: Максимальное количество потоков (None = использовать из конфигурации)
        :param progress_callback: Колбэк для отслеживания прогресса
        :return: Список результатов OCR
        """
        if max_threads is None:
            max_threads = self.max_threads

        self.logger.info(f"Начинаем batch обработку {len(image_paths)} изображений с {max_threads} потоками")

        results = [None] * len(image_paths)  # Предзаполняем массив для сохранения порядка
        completed_count = 0

        def update_progress(future_index: int):
            """Обновляет прогресс выполнения"""
            nonlocal completed_count
            completed_count += 1

            if progress_callback:
                current_file = os.path.basename(image_paths[future_index])
                progress_callback(completed_count, len(image_paths), current_file)

        # Используем ThreadPoolExecutor для параллельной обработки
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Создаем futures для всех изображений
            future_to_index = {}

            for i, image_path in enumerate(image_paths):
                future = executor.submit(self._process_single_image, image_path, prompt_text)
                future_to_index[future] = i

            # Собираем результаты по мере готовности
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]

                try:
                    result = future.result(timeout=self.timeout_seconds)
                    results[index] = result

                except concurrent.futures.TimeoutError:
                    # Создаем результат с ошибкой таймаута
                    results[index] = OCRResult(
                        file_path=image_paths[index],
                        success=False,
                        text_content="",
                        error_message=f"Превышен таймаут ({self.timeout_seconds}с)",
                        processing_time=self.timeout_seconds
                    )
                    self.logger.error(f"Таймаут при обработке {image_paths[index]}")

                except Exception as e:
                    # Создаем результат с ошибкой
                    results[index] = OCRResult(
                        file_path=image_paths[index],
                        success=False,
                        text_content="",
                        error_message=f"Ошибка executor: {str(e)}",
                        processing_time=0.0
                    )
                    self.logger.error(f"Ошибка executor для {image_paths[index]}: {e}")

                # Обновляем прогресс
                update_progress(index)

        # Проверяем, что все результаты получены
        for i, result in enumerate(results):
            if result is None:
                results[i] = OCRResult(
                    file_path=image_paths[i],
                    success=False,
                    text_content="",
                    error_message="Неизвестная ошибка: результат не получен",
                    processing_time=0.0
                )

        successful_count = sum(1 for r in results if r.success)
        self.logger.info(
            f"Batch обработка завершена: {successful_count}/{len(image_paths)} успешно"
        )

        return results

    def process_single_image_sync(self, image_path: str, prompt_text: str) -> OCRResult:
        """
        Синхронно обрабатывает одно изображение (для простых случаев).

        :param image_path: Путь к изображению
        :param prompt_text: Промпт для OCR
        :return: Результат OCR обработки
        """
        return self._process_single_image(image_path, prompt_text)

    def test_llm_connection(self) -> bool:
        """
        Тестирует соединение с LLM сервисом.

        :return: True если соединение работает
        """
        try:
            test_response = self.llm_agent.response_from_LLM(
                user_message="Привет! Это тест соединения. Ответь 'OK'."
            )

            if test_response and 'ok' in test_response.lower():
                self.logger.info("Тест соединения с LLM прошел успешно")
                return True
            else:
                self.logger.warning(f"Неожиданный ответ при тесте: {test_response}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка при тестировании соединения с LLM: {e}")
            return False

    def get_llm_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о настройках LLM.

        :return: Словарь с информацией о LLM
        """
        return {
            'model_name': self.llm_agent.model_name,
            'provider': self.llm_agent.use_openai_or_openrouter,
            'max_total_tokens': self.llm_agent.max_total_tokens,
            'max_response_tokens': self.llm_agent.max_response_tokens,
            'temperature': self.llm_agent.temperature,
            'max_threads': self.max_threads,
            'timeout_seconds': self.timeout_seconds,
            'retry_attempts': self.retry_attempts
        }

    def update_settings(self, **kwargs) -> None:
        """
        Обновляет настройки процессора.

        :param kwargs: Новые настройки
        """
        if 'max_threads' in kwargs:
            self.max_threads = kwargs['max_threads']
            self.logger.info(f"Обновлено max_threads: {self.max_threads}")

        if 'timeout_seconds' in kwargs:
            self.timeout_seconds = kwargs['timeout_seconds']
            self.logger.info(f"Обновлено timeout_seconds: {self.timeout_seconds}")

        if 'retry_attempts' in kwargs:
            self.retry_attempts = kwargs['retry_attempts']
            self.logger.info(f"Обновлено retry_attempts: {self.retry_attempts}")

    def estimate_processing_time(self, image_count: int) -> float:
        """
        Оценивает время обработки для заданного количества изображений.

        :param image_count: Количество изображений
        :return: Оценочное время в секундах
        """
        # Средние времена основаны на эмпирических данных
        avg_time_per_image = 5.0  # секунд на изображение

        # Учитываем параллелизм
        parallel_factor = min(self.max_threads, image_count) / image_count

        estimated_time = (image_count * avg_time_per_image) * parallel_factor

        return max(estimated_time, image_count * 2.0)  # Минимум 2 секунды на изображение
