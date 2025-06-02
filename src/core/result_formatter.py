"""
Форматирование результатов OCR обработки.
Создание структурированного выходного файла с метаданными и статистикой.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from .types import OCRResult  # Импорт из родительского модуля


class ResultFormatter:
    """
    Класс для форматирования и структурирования результатов OCR обработки.
    """

    def __init__(self):
        """Инициализация форматтера результатов."""
        self.logger = logging.getLogger(__name__)

    def format_results(self, results: List[OCRResult],
                      include_metadata: bool = True,
                      format_type: str = "detailed") -> str:
        """
        Форматирует список результатов OCR в текстовый документ.

        :param results: Список результатов OCR
        :param include_metadata: Включать ли метаданные о файлах
        :param format_type: Тип форматирования ('detailed', 'simple', 'clean')
        :return: Форматированный текст
        """
        if not results:
            return self._generate_empty_report()

        if format_type == "detailed":
            return self._format_detailed(results, include_metadata)
        elif format_type == "simple":
            return self._format_simple(results, include_metadata)
        elif format_type == "clean":
            return self._format_clean_text_only(results)
        else:
            self.logger.warning(f"Неизвестный тип форматирования: {format_type}, используем detailed")
            return self._format_detailed(results, include_metadata)

    def _generate_empty_report(self) -> str:
        """
        Генерирует отчет для случая отсутствия результатов.

        :return: Текст отчета
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""
# OCR ОБРАБОТКА - ОТЧЕТ

**Время генерации:** {timestamp}
**Статус:** Нет результатов для обработки

Не было найдено файлов для обработки или все файлы завершились с ошибками.
"""

    def _format_detailed(self, results: List[OCRResult], include_metadata: bool) -> str:
        """
        Детальное форматирование с полной информацией.

        :param results: Список результатов OCR
        :param include_metadata: Включать ли метаданные
        :return: Детально форматированный текст
        """
        lines = []

        # Заголовок документа
        lines.extend(self._generate_header(results))

        # Статистика обработки
        if include_metadata:
            lines.extend(self._generate_statistics(results))

        # Основное содержимое
        lines.append("\n" + "="*80)
        lines.append("# ИЗВЛЕЧЕННЫЙ ТЕКСТ")
        lines.append("="*80 + "\n")

        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Успешно обработанные файлы
        if successful_results:
            for i, result in enumerate(successful_results, 1):
                lines.extend(self._format_single_result(result, i, include_metadata))

        # Файлы с ошибками
        if failed_results and include_metadata:
            lines.append("\n" + "="*80)
            lines.append("# ФАЙЛЫ С ОШИБКАМИ")
            lines.append("="*80 + "\n")

            for result in failed_results:
                lines.extend(self._format_error_result(result))

        # Итоговая статистика
        if include_metadata:
            lines.extend(self._generate_footer_statistics(results))

        return "\n".join(lines)

    def _format_simple(self, results: List[OCRResult], include_metadata: bool) -> str:
        """
        Простое форматирование с базовой информацией.

        :param results: Список результатов OCR
        :param include_metadata: Включать ли метаданные
        :return: Просто форматированный текст
        """
        lines = []

        if include_metadata:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"OCR Обработка - {timestamp}")
            lines.append("-" * 50)
            lines.append("")

        successful_results = [r for r in results if r.success]

        for i, result in enumerate(successful_results, 1):
            if include_metadata:
                filename = os.path.basename(result.file_path)
                lines.append(f"[{i}] {filename}")
                lines.append("-" * 30)

            if result.text_content.strip():
                lines.append(result.text_content.strip())
            else:
                lines.append("[Текст не обнаружен]")

            lines.append("")  # Пустая строка между файлами

        return "\n".join(lines)

    def _format_clean_text_only(self, results: List[OCRResult]) -> str:
        """
        Форматирование только извлеченного текста без метаданных.

        :param results: Список результатов OCR
        :return: Чистый текст без метаданных
        """
        text_parts = []

        successful_results = [r for r in results if r.success]

        for result in successful_results:
            if result.text_content.strip():
                text_parts.append(result.text_content.strip())

        return "\n\n".join(text_parts)

    def _generate_header(self, results: List[OCRResult]) -> List[str]:
        """
        Генерирует заголовок документа.

        :param results: Список результатов OCR
        :return: Список строк заголовка
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return [
            "# ОТЧЕТ OCR ОБРАБОТКИ",
            "",
            f"**Время обработки:** {timestamp}",
            f"**Всего файлов:** {len(results)}",
            f"**Успешно обработано:** {sum(1 for r in results if r.success)}",
            f"**Ошибок:** {sum(1 for r in results if not r.success)}",
            ""
        ]

    def _generate_statistics(self, results: List[OCRResult]) -> List[str]:
        """
        Генерирует статистику обработки.

        :param results: Список результатов OCR
        :return: Список строк статистики
        """
        lines = ["## СТАТИСТИКА ОБРАБОТКИ", ""]

        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Базовая статистика
        lines.extend([
            f"- Обработано успешно: {len(successful_results)}",
            f"- Завершено с ошибками: {len(failed_results)}",
            f"- Общий процент успеха: {len(successful_results)/len(results)*100:.1f}%"
        ])

        # Статистика времени
        if successful_results:
            processing_times = [r.processing_time for r in successful_results if r.processing_time > 0]
            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                max_time = max(processing_times)
                min_time = min(processing_times)

                lines.extend([
                    "",
                    "**Время обработки:**",
                    f"- Среднее время: {avg_time:.2f}с",
                    f"- Максимальное время: {max_time:.2f}с",
                    f"- Минимальное время: {min_time:.2f}с"
                ])

        # Статистика контента
        if successful_results:
            text_lengths = [len(r.text_content) for r in successful_results]
            if text_lengths:
                avg_length = sum(text_lengths) / len(text_lengths)
                max_length = max(text_lengths)
                total_chars = sum(text_lengths)

                lines.extend([
                    "",
                    "**Извлеченный текст:**",
                    f"- Общее количество символов: {total_chars:,}",
                    f"- Среднее количество символов на файл: {avg_length:.0f}",
                    f"- Самый длинный текст: {max_length:,} символов"
                ])

        lines.append("")
        return lines

    def _format_single_result(self, result: OCRResult, index: int,
                            include_metadata: bool) -> List[str]:
        """
        Форматирует результат обработки одного файла.

        :param result: Результат OCR
        :param index: Порядковый номер файла
        :param include_metadata: Включать ли метаданные
        :return: Список форматированных строк
        """
        lines = []
        filename = os.path.basename(result.file_path)

        if include_metadata:
            lines.extend([
                f"## [{index}] {filename}",
                "",
                f"**Путь:** {result.file_path}",
                f"**Время обработки:** {result.processing_time:.2f}с",
                f"**Размер текста:** {len(result.text_content)} символов",
                ""
            ])
        else:
            lines.extend([
                f"## {filename}",
                ""
            ])

        # Добавляем текст
        if result.text_content.strip():
            lines.append("**ИЗВЛЕЧЕННЫЙ ТЕКСТ:**")
            lines.append("")
            lines.append(result.text_content.strip())
        else:
            lines.append("*[Текст не обнаружен или файл пуст]*")

        lines.extend(["", "-" * 80, ""])

        return lines

    def _format_error_result(self, result: OCRResult) -> List[str]:
        """
        Форматирует результат с ошибкой.

        :param result: Результат OCR с ошибкой
        :return: Список форматированных строк
        """
        filename = os.path.basename(result.file_path)

        return [
            f"**{filename}**",
            f"- Путь: {result.file_path}",
            f"- Ошибка: {result.error_message}",
            f"- Время попытки: {result.processing_time:.2f}с",
            ""
        ]

    def _generate_footer_statistics(self, results: List[OCRResult]) -> List[str]:
        """
        Генерирует итоговую статистику в конце документа.

        :param results: Список результатов OCR
        :return: Список строк итоговой статистики
        """
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return [
                "",
                "="*80,
                "# ИТОГОВАЯ СТАТИСТИКА",
                "="*80,
                "",
                "Не было успешно обработано ни одного файла."
            ]

        total_chars = sum(len(r.text_content) for r in successful_results)
        total_time = sum(r.processing_time for r in results if r.processing_time > 0)

        lines = [
            "",
            "="*80,
            "# ИТОГОВАЯ СТАТИСТИКА",
            "="*80,
            "",
            f"Всего извлечено символов: {total_chars:,}",
            f"Общее время обработки: {total_time:.2f}с",
            f"Скорость обработки: {total_chars/total_time if total_time > 0 else 0:.0f} символов/сек",
            "",
            f"Обработка завершена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        return lines

    def export_to_formats(self, results: List[OCRResult],
                         base_filename: str) -> Dict[str, str]:
        """
        Экспортирует результаты в различные форматы.

        :param results: Список результатов OCR
        :param base_filename: Базовое имя файла без расширения
        :return: Словарь с путями к созданным файлам
        """
        exported_files = {}
        base_path = Path(base_filename).parent
        base_name = Path(base_filename).stem

        # Детальный отчет
        detailed_content = self.format_results(results, include_metadata=True, format_type="detailed")
        detailed_path = base_path / f"{base_name}_detailed.txt"
        self._write_file(detailed_path, detailed_content)
        exported_files["detailed"] = str(detailed_path)

        # Простой формат
        simple_content = self.format_results(results, include_metadata=True, format_type="simple")
        simple_path = base_path / f"{base_name}_simple.txt"
        self._write_file(simple_path, simple_content)
        exported_files["simple"] = str(simple_path)

        # Только текст
        clean_content = self.format_results(results, include_metadata=False, format_type="clean")
        clean_path = base_path / f"{base_name}_clean.txt"
        self._write_file(clean_path, clean_content)
        exported_files["clean"] = str(clean_path)

        # JSON формат для программной обработки
        json_path = base_path / f"{base_name}_data.json"
        json_content = self._export_to_json(results)
        self._write_file(json_path, json_content)
        exported_files["json"] = str(json_path)

        return exported_files

    def _write_file(self, file_path: Path, content: str) -> None:
        """
        Записывает содержимое в файл.

        :param file_path: Путь к файлу
        :param content: Содержимое для записи
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.logger.debug(f"Файл записан: {file_path}")
        except Exception as e:
            self.logger.error(f"Ошибка записи файла {file_path}: {e}")

    def _export_to_json(self, results: List[OCRResult]) -> str:
        """
        Экспортирует результаты в JSON формат.

        :param results: Список результатов OCR
        :return: JSON строка
        """
        import json

        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_files": len(results),
                "successful_files": sum(1 for r in results if r.success),
                "failed_files": sum(1 for r in results if not r.success)
            },
            "results": []
        }

        for result in results:
            result_data = {
                "file_path": result.file_path,
                "filename": os.path.basename(result.file_path),
                "success": result.success,
                "text_content": result.text_content,
                "processing_time": result.processing_time,
                "error_message": result.error_message,
                "text_length": len(result.text_content),
                "file_size": self._get_file_size(result.file_path)
            }
            data["results"].append(result_data)

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _get_file_size(self, file_path: str) -> int:
        """
        Получает размер файла.

        :param file_path: Путь к файлу
        :return: Размер файла в байтах
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, IOError):
            return 0

    def generate_summary_report(self, results: List[OCRResult]) -> str:
        """
        Генерирует краткий сводный отчет.

        :param results: Список результатов OCR
        :return: Краткий отчет
        """
        if not results:
            return "Нет данных для формирования отчета."

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_chars = sum(len(r.text_content) for r in successful)
        total_time = sum(r.processing_time for r in results if r.processing_time > 0)

        report = f"""СВОДНЫЙ ОТЧЕТ OCR ОБРАБОТКИ
{'='*40}

Файлов обработано: {len(results)}
Успешно: {len(successful)} ({len(successful)/len(results)*100:.1f}%)
С ошибками: {len(failed)} ({len(failed)/len(results)*100:.1f}%)

Извлечено символов: {total_chars:,}
Время обработки: {total_time:.1f}с
Скорость: {total_chars/total_time if total_time > 0 else 0:.0f} символов/сек

Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report
