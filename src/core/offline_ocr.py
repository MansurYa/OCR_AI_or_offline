"""
Offline OCR обработка с использованием Tesseract OCR.
Включает автоматическую загрузку языковых пакетов и обработку изображений.
"""

import os
import sys
import time
import logging
import requests
from typing import Dict, Any, List
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps

from .ocr_processor import OCRResult  # Импорт из родительского модуля


class OfflineOCRProcessor:
    """
    Процессор для offline OCR с использованием Tesseract.
    Автоматически загружает языковые пакеты и обрабатывает изображения.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация offline OCR процессора.

        :param config: Конфигурация приложения
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ocr_settings = config.get('ocr_settings', {}).get('offline', {})

        # Настройки Tesseract
        self.tessdata_dir = os.path.expanduser(
            self.ocr_settings.get('tessdata_dir', '~/tessdata')
        )
        self.supported_formats = self.ocr_settings.get(
            'supported_formats', ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        )

        # Инициализация
        self._validate_tesseract()
        self._setup_tessdata_environment()

    def _validate_tesseract(self) -> None:
        """
        Проверяет доступность Tesseract в системе.

        :raises RuntimeError: Если Tesseract не найден
        """
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract версия: {version}")
        except EnvironmentError as e:
            error_msg = (
                "Tesseract OCR не найден в системе. "
                "Установите Tesseract и добавьте его в PATH."
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _setup_tessdata_environment(self) -> None:
        """
        Настраивает переменную окружения для Tesseract данных.
        """
        os.environ['TESSDATA_PREFIX'] = self.tessdata_dir
        self.logger.info(f"TESSDATA_PREFIX установлен: {self.tessdata_dir}")

    def _download_language_pack(self, language_code: str) -> bool:
        """
        Загружает языковой пакет для Tesseract с GitHub.

        :param language_code: Код языка (например, 'rus', 'eng')
        :return: True если загрузка успешна
        """
        url = f"https://github.com/tesseract-ocr/tessdata_best/raw/main/{language_code}.traineddata"

        try:
            self.logger.info(f"Загружаем языковой пакет: {language_code}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Создаем директорию если не существует
            os.makedirs(self.tessdata_dir, exist_ok=True)

            # Сохраняем файл
            file_path = os.path.join(self.tessdata_dir, f"{language_code}.traineddata")
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            self.logger.info(f"Языковой пакет {language_code} успешно загружен")
            return True

        except requests.RequestException as e:
            self.logger.error(f"Ошибка загрузки языкового пакета {language_code}: {e}")
            return False
        except IOError as e:
            self.logger.error(f"Ошибка сохранения языкового пакета {language_code}: {e}")
            return False

    def _is_language_available(self, language_code: str) -> bool:
        """
        Проверяет доступность языкового пакета.

        :param language_code: Код языка
        :return: True если языковой пакет доступен
        """
        file_path = os.path.join(self.tessdata_dir, f"{language_code}.traineddata")
        return os.path.exists(file_path)

    def setup_language(self, language_code: str) -> bool:
        """
        Настраивает языковой пакет (загружает если необходимо).

        :param language_code: Код языка
        :return: True если язык готов к использованию
        """
        # Проверяем, доступен ли уже языковой пакет
        if self._is_language_available(language_code):
            self.logger.debug(f"Языковой пакет {language_code} уже доступен")
            return True

        # Пытаемся загрузить
        return self._download_language_pack(language_code)

    def setup_multiple_languages(self, language_codes: List[str]) -> Dict[str, bool]:
        """
        Настраивает несколько языковых пакетов.

        :param language_codes: Список кодов языков
        :return: Словарь с результатами настройки для каждого языка
        """
        results = {}
        for code in language_codes:
            results[code] = self.setup_language(code)
        return results

    def get_available_languages(self) -> List[str]:
        """
        Возвращает список доступных языковых пакетов.

        :return: Список кодов языков
        """
        if not os.path.exists(self.tessdata_dir):
            return []

        languages = []
        for file_name in os.listdir(self.tessdata_dir):
            if file_name.endswith('.traineddata'):
                lang_code = file_name[:-12]  # Убираем .traineddata
                languages.append(lang_code)

        return sorted(languages)

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Предобрабатывает изображение для улучшения OCR качества.

        :param image: Исходное изображение
        :return: Обработанное изображение
        """
        # Исправляем ориентацию на основе EXIF данных
        image = ImageOps.exif_transpose(image)

        # Конвертируем в RGB если необходимо
        if image.mode != 'RGB':
            image = image.convert('RGB')

        return image

    def _build_tesseract_config(self, psm_mode: int = 3, oem_mode: int = 3) -> str:
        """
        Создает конфигурационную строку для Tesseract.

        :param psm_mode: Page Segmentation Mode (режим сегментации страницы)
        :param oem_mode: OCR Engine Mode (режим OCR движка)
        :return: Конфигурационная строка
        """
        return f'--psm {psm_mode} --oem {oem_mode}'

    def process_image(self, image_path: str, language: str = "rus",
                     psm_mode: int = 3) -> OCRResult:
        """
        Обрабатывает одно изображение с помощью Tesseract OCR.

        :param image_path: Путь к изображению
        :param language: Код языка для OCR
        :param psm_mode: Режим сегментации страницы
        :return: Результат OCR обработки
        """
        start_time = time.time()

        try:
            # Проверяем существование файла
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Файл не найден: {image_path}")

            # Проверяем формат файла
            file_extension = Path(image_path).suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")

            # Настраиваем язык если необходимо
            if not self.setup_language(language):
                # Fallback на английский язык
                language = "eng"
                if not self.setup_language(language):
                    raise RuntimeError("Не удалось настроить ни один языковой пакет")

            # Загружаем и предобрабатываем изображение
            with Image.open(image_path) as image:
                processed_image = self._preprocess_image(image)

                # Выполняем OCR
                config = self._build_tesseract_config(psm_mode)
                text = pytesseract.image_to_string(
                    processed_image,
                    lang=language,
                    config=config
                )

            processing_time = time.time() - start_time

            # Создаем результат
            result = OCRResult(
                file_path=image_path,
                success=True,
                text_content=text.strip(),
                processing_time=processing_time
            )

            self.logger.debug(
                f"Файл {image_path} обработан за {processing_time:.2f}с, "
                f"извлечено {len(text)} символов"
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Ошибка обработки {image_path}: {str(e)}"

            result = OCRResult(
                file_path=image_path,
                success=False,
                text_content="",
                error_message=error_message,
                processing_time=processing_time
            )

            self.logger.error(error_message)
            return result

    def batch_process(self, image_paths: List[str], language: str = "rus",
                     psm_mode: int = 3) -> List[OCRResult]:
        """
        Обрабатывает список изображений последовательно.

        :param image_paths: Список путей к изображениям
        :param language: Код языка для OCR
        :param psm_mode: Режим сегментации страницы
        :return: Список результатов OCR
        """
        self.logger.info(f"Начинаем batch обработку {len(image_paths)} изображений")

        results = []
        for image_path in image_paths:
            result = self.process_image(image_path, language, psm_mode)
            results.append(result)

        successful_count = sum(1 for r in results if r.success)
        self.logger.info(
            f"Batch обработка завершена: {successful_count}/{len(image_paths)} успешно"
        )

        return results

    def get_tesseract_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о Tesseract установке.

        :return: Словарь с информацией о Tesseract
        """
        try:
            version = pytesseract.get_tesseract_version()
            available_languages = self.get_available_languages()

            return {
                'version': str(version),
                'tessdata_dir': self.tessdata_dir,
                'available_languages': available_languages,
                'supported_formats': self.supported_formats
            }
        except Exception as e:
            return {
                'error': str(e),
                'tessdata_dir': self.tessdata_dir,
                'supported_formats': self.supported_formats
            }

    def test_ocr_capability(self, test_text: str = "Hello World") -> bool:
        """
        Тестирует базовую функциональность OCR.

        :param test_text: Текст для создания тестового изображения
        :return: True если тест прошел успешно
        """
        try:
            # Создаем простое тестовое изображение
            from PIL import Image, ImageDraw, ImageFont

            # Создаем белое изображение
            img = Image.new('RGB', (300, 100), color='white')
            draw = ImageDraw.Draw(img)

            # Пытаемся использовать системный шрифт
            try:
                font = ImageFont.load_default()
            except:
                font = None

            # Рисуем текст
            draw.text((10, 30), test_text, fill='black', font=font)

            # Тестируем OCR
            detected_text = pytesseract.image_to_string(img, lang='eng')

            # Проверяем результат
            if test_text.lower() in detected_text.lower():
                self.logger.info("Тест OCR функциональности пройден")
                return True
            else:
                self.logger.warning(f"Тест OCR: ожидался '{test_text}', получен '{detected_text}'")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка при тестировании OCR: {e}")
            return False
