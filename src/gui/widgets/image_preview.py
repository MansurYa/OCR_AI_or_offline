"""
Виджет для предварительного просмотра изображений.
Показывает миниатюры изображений в списке файлов.
"""

import tkinter as tk
from PIL import Image, ImageTk
import os
import logging
from typing import Optional


class ImagePreview(tk.Label):
    """
    Виджет для отображения миниатюры изображения.
    """

    def __init__(self, parent: tk.Widget, image_path: str = "", size: int = 64, **kwargs):
        """
        Инициализация виджета предпросмотра.

        :param parent: Родительский виджет
        :param image_path: Путь к изображению
        :param size: Размер миниатюры
        :param kwargs: Дополнительные параметры
        """
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)

        self.image_path = image_path
        self.size = size
        self.photo_image: Optional[ImageTk.PhotoImage] = None

        if image_path:
            self.load_image(image_path)

    def load_image(self, image_path: str) -> bool:
        """
        Загружает и отображает изображение.

        :param image_path: Путь к изображению
        :return: True если загрузка успешна
        """
        try:
            if not os.path.exists(image_path):
                self._show_error_image()
                return False

            # Загружаем и изменяем размер
            with Image.open(image_path) as img:
                img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
                self.photo_image = ImageTk.PhotoImage(img)
                self.configure(image=self.photo_image)
                return True

        except Exception as e:
            self.logger.warning(f"Не удалось загрузить изображение {image_path}: {e}")
            self._show_error_image()
            return False

    def _show_error_image(self):
        """Показывает заглушку при ошибке загрузки."""
        self.configure(text="❌", image="", font=("Arial", 16))
