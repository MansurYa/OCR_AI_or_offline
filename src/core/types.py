"""
Типы данных для OCR обработки.
Содержит общие классы данных используемые во всех core модулях.
"""

from dataclasses import dataclass
from typing import List, Optional


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
