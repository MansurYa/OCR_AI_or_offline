"""
Главное представление приложения.
Содержит основной layout и координирует взаимодействие между компонентами GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import Optional, List

from ..models.app_model import ProcessingState
from ..widgets.drag_drop_frame import DragDropFrame
from .image_list_view import ImageListView
from .settings_view import SettingsView
from .progress_view import ProgressView

# Импорт для типов
try:
    from ..presenters.main_presenter import MainPresenter
    from core.ocr_processor import OCRBatchResult
except ImportError:
    # Для избежания циклических импортов при разработке
    MainPresenter = None
    OCRBatchResult = None


class MainView:
    """
    Главное представление приложения.
    Координирует все GUI компоненты и взаимодействует с presenter.
    """

    def __init__(self, parent: tk.Widget):
        """
        Инициализация главного представления.

        :param parent: Родительский виджет
        """
        self.parent = parent
        self.logger = logging.getLogger(__name__)

        # Presenter будет установлен позже
        self.presenter: Optional[MainPresenter] = None

        # Основные компоненты
        self.main_frame: Optional[tk.Frame] = None
        self.drag_drop_frame: Optional[DragDropFrame] = None
        self.image_list_view: Optional[ImageListView] = None
        self.settings_view: Optional[SettingsView] = None
        self.progress_view: Optional[ProgressView] = None

        # Кнопки управления
        self.start_button: Optional[tk.Button] = None
        self.clear_button: Optional[tk.Button] = None
        self.sort_button: Optional[tk.Button] = None

        # Статусная строка
        self.status_label: Optional[tk.Label] = None

        # Создаем GUI
        self._create_gui()

    def set_presenter(self, presenter) -> None:
        """
        Устанавливает presenter для взаимодействия.

        :param presenter: Экземпляр MainPresenter
        """
        self.presenter = presenter

        # Передаем presenter дочерним компонентам
        if self.image_list_view:
            self.image_list_view.set_presenter(presenter)
        if self.settings_view:
            self.settings_view.set_presenter(presenter)
        if self.progress_view:
            self.progress_view.set_presenter(presenter)
        if self.drag_drop_frame:
            self.drag_drop_frame.set_presenter(presenter)

    def _create_gui(self) -> None:
        """Создает главный интерфейс приложения."""
        # Главный контейнер
        self.main_frame = tk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем основные секции
        self._create_header()
        self._create_main_content()
        self._create_control_buttons()
        self._create_status_bar()

    def _create_header(self) -> None:
        """Создает заголовок приложения."""
        header_frame = tk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Заголовок
        title_label = tk.Label(
            header_frame,
            text="🔍 OCR AI or Offline",
            font=("Arial", 16, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT)

        # Кнопки меню
        menu_frame = tk.Frame(header_frame)
        menu_frame.pack(side=tk.RIGHT)

        # Кнопка настроек
        settings_btn = tk.Button(
            menu_frame,
            text="⚙️ Настройки",
            command=self._on_settings_click,
            relief=tk.FLAT,
            padx=10
        )
        settings_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Кнопка справки
        help_btn = tk.Button(
            menu_frame,
            text="❓ Справка",
            command=self._on_help_click,
            relief=tk.FLAT,
            padx=10
        )
        help_btn.pack(side=tk.RIGHT, padx=(5, 0))

    def _create_main_content(self) -> None:
        """Создает основное содержимое."""
        # Основной контейнер с двумя панелями
        main_content = tk.Frame(self.main_frame)
        main_content.pack(fill=tk.BOTH, expand=True)

        # Левая панель - изображения
        left_panel = tk.LabelFrame(main_content, text="📁 Изображения", padx=5, pady=5)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Правая панель - настройки
        right_panel = tk.LabelFrame(main_content, text="⚙️ Настройки OCR", padx=5, pady=5)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.configure(width=300)
        right_panel.pack_propagate(False)

        self._create_images_panel(left_panel)
        self._create_settings_panel(right_panel)

    def _create_images_panel(self, parent: tk.Widget) -> None:
        """
        Создает панель для работы с изображениями.

        :param parent: Родительский виджет
        """
        # Drag & Drop область
        self.drag_drop_frame = DragDropFrame(parent)
        self.drag_drop_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопки добавления файлов
        buttons_frame = tk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        add_files_btn = tk.Button(
            buttons_frame,
            text="📁 Добавить файлы",
            command=self._on_add_files_click,
            bg="#3498db",
            fg="white",
            padx=15,
            pady=5
        )
        add_files_btn.pack(side=tk.LEFT, padx=(0, 5))

        add_folder_btn = tk.Button(
            buttons_frame,
            text="📂 Добавить папку",
            command=self._on_add_folder_click,
            bg="#3498db",
            fg="white",
            padx=15,
            pady=5
        )
        add_folder_btn.pack(side=tk.LEFT, padx=5)

        # Кнопка очистки
        self.clear_button = tk.Button(
            buttons_frame,
            text="🗑️ Очистить",
            command=self._on_clear_click,
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=5
        )
        self.clear_button.pack(side=tk.RIGHT)

        # Список изображений
        self.image_list_view = ImageListView(parent)
        self.image_list_view.pack(fill=tk.BOTH, expand=True)

    def _create_settings_panel(self, parent: tk.Widget) -> None:
        """
        Создает панель настроек.

        :param parent: Родительский виджет
        """
        # Настройки OCR
        self.settings_view = SettingsView(parent)
        self.settings_view.pack(fill=tk.BOTH, expand=True)

    def _create_control_buttons(self) -> None:
        """Создает кнопки управления обработкой."""
        control_frame = tk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))

        # Кнопка сортировки
        self.sort_button = tk.Button(
            control_frame,
            text="🔢 Сортировать",
            command=self._on_sort_click,
            bg="#f39c12",
            fg="white",
            padx=20,
            pady=8
        )
        self.sort_button.pack(side=tk.LEFT)

        # Основная кнопка запуска
        self.start_button = tk.Button(
            control_frame,
            text="🚀 Начать обработку OCR",
            command=self._on_start_processing_click,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=10
        )
        self.start_button.pack(side=tk.RIGHT)

    def _create_status_bar(self) -> None:
        """Создает статусную строку."""
        status_frame = tk.Frame(self.main_frame, relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_label = tk.Label(
            status_frame,
            text="Готов к работе",
            anchor=tk.W,
            padx=5,
            pady=2
        )
        self.status_label.pack(fill=tk.X)

    # ========================
    # Обработчики событий
    # ========================

    def _on_add_files_click(self) -> None:
        """Обработчик добавления файлов."""
        if not self.presenter:
            return

        filetypes = [
            ("Изображения", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif"),
            ("PNG файлы", "*.png"),
            ("JPEG файлы", "*.jpg *.jpeg"),
            ("Все файлы", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=filetypes
        )

        if files:
            result = self.presenter.add_files(list(files))
            self._show_add_files_result(result)

    def _on_add_folder_click(self) -> None:
        """Обработчик добавления папки."""
        if not self.presenter:
            return

        directory = filedialog.askdirectory(title="Выберите папку с изображениями")

        if directory:
            # Спрашиваем о рекурсивном поиске
            recursive = messagebox.askyesno(
                "Поиск в подпапках",
                "Искать изображения во всех подпапках?",
                default=messagebox.NO
            )

            result = self.presenter.add_directory(directory, recursive)
            self._show_add_files_result(result)

    def _on_clear_click(self) -> None:
        """Обработчик очистки списка файлов."""
        if not self.presenter:
            return

        if messagebox.askyesno("Подтверждение", "Очистить весь список изображений?"):
            self.presenter.clear_files()

    def _on_sort_click(self) -> None:
        """Обработчик сортировки файлов."""
        if not self.presenter:
            return

        # Получаем текущий метод сортировки из настроек
        settings = self.presenter.get_settings()
        current_method = settings.sort_method

        self.presenter.sort_files(current_method)
        self.update_status(f"Файлы отсортированы: {settings.get_sort_method_name()}")

    def _on_start_processing_click(self) -> None:
        """Обработчик запуска обработки OCR."""
        if not self.presenter:
            return

        if not self.presenter.can_start_processing():
            reasons = []

            if self.presenter.get_statistics()['valid_files'] == 0:
                reasons.append("Нет файлов для обработки")

            settings = self.presenter.get_settings()
            if not settings.output_file:
                reasons.append("Не указан выходной файл")

            messagebox.showwarning(
                "Невозможно начать обработку",
                "Причины:\n" + "\n".join(f"• {reason}" for reason in reasons)
            )
            return

        # Показываем диалог прогресса
        if self.progress_view:
            self.progress_view.show_dialog()

        # Запускаем обработку
        success = self.presenter.start_processing()
        if not success:
            messagebox.showerror("Ошибка", "Не удалось запустить обработку")
            if self.progress_view:
                self.progress_view.hide_dialog()

    def _on_settings_click(self) -> None:
        """Обработчик открытия настроек."""
        messagebox.showinfo("Настройки", "Детальные настройки доступны в правой панели")

    def _on_help_click(self) -> None:
        """Обработчик справки."""
        help_text = """OCR AI or Offline - Инструмент для распознавания текста

Как использовать:
1. Добавьте изображения через кнопки или перетащите файлы
2. Выберите режим обработки (Offline/Online)
3. Настройте параметры в правой панели
4. Нажмите "Начать обработку OCR"

Поддерживаемые форматы:
• PNG, JPG, JPEG, TIFF, BMP, GIF

Режимы обработки:
• Offline: Tesseract OCR (быстро, без интернета)
• Online: ИИ модели (более точно, требует интернет)
"""
        messagebox.showinfo("Справка", help_text)

    def _show_add_files_result(self, result: dict) -> None:
        """
        Показывает результат добавления файлов.

        :param result: Результат добавления файлов
        """
        added = len(result.get('added', []))
        skipped = len(result.get('skipped', []))
        invalid = len(result.get('invalid', []))

        if added > 0:
            self.update_status(f"Добавлено файлов: {added}")

        if skipped > 0 or invalid > 0:
            messages = []
            if skipped > 0:
                messages.append(f"Пропущено (дубликаты): {skipped}")
            if invalid > 0:
                messages.append(f"Неверный формат: {invalid}")

            messagebox.showwarning(
                "Добавление файлов",
                "\n".join(messages)
            )

    # ==============================
    # Методы обновления интерфейса
    # ==============================

    def update_image_list(self) -> None:
        """Обновляет список изображений."""
        if self.image_list_view and self.presenter:
            files = self.presenter.get_image_files()
            self.image_list_view.update_file_list(files)

    def update_statistics(self) -> None:
        """Обновляет статистику."""
        if not self.presenter:
            return

        stats = self.presenter.get_statistics()

        # Обновляем статусную строку
        total = stats['total_files']
        valid = stats['valid_files']
        size_mb = stats['total_size_mb']

        if total > 0:
            status_text = f"Файлов: {valid}/{total}, Размер: {size_mb:.1f} МБ"

            if valid != total:
                status_text += f" (неверных: {total - valid})"

            self.update_status(status_text)
        else:
            self.update_status("Файлы не добавлены")

        # Обновляем доступность кнопок
        self._update_button_states()

    def update_settings_display(self) -> None:
        """Обновляет отображение настроек."""
        if self.settings_view:
            self.settings_view.update_from_model()

    def update_processing_state(self, state: ProcessingState) -> None:
        """
        Обновляет состояние обработки.

        :param state: Состояние обработки
        """
        if state.is_running:
            self.start_button.configure(
                text="⏸️ Обработка...",
                state=tk.DISABLED,
                bg="#e67e22"
            )

            if state.current_filename:
                self.update_status(f"Обрабатывается: {state.current_filename}")
        else:
            self.start_button.configure(
                text="🚀 Начать обработку OCR",
                state=tk.NORMAL,
                bg="#27ae60"
            )

            if state.progress_percentage >= 100:
                self.update_status("Обработка завершена")
            else:
                self.update_status("Готов к работе")

        # Обновляем прогресс диалог
        if self.progress_view:
            self.progress_view.update_progress(state)

    def update_status(self, message: str) -> None:
        """
        Обновляет статусную строку.

        :param message: Сообщение для отображения
        """
        if self.status_label:
            self.status_label.configure(text=message)

    def _update_button_states(self) -> None:
        """Обновляет состояние кнопок в зависимости от контекста."""
        if not self.presenter:
            return

        stats = self.presenter.get_statistics()
        has_files = stats['valid_files'] > 0
        is_processing = self.presenter.get_processing_state().is_running

        # Кнопка очистки
        if self.clear_button:
            self.clear_button.configure(state=tk.NORMAL if has_files and not is_processing else tk.DISABLED)

        # Кнопка сортировки
        if self.sort_button:
            self.sort_button.configure(state=tk.NORMAL if has_files and not is_processing else tk.DISABLED)

        # Кнопка запуска
        if self.start_button:
            can_start = self.presenter.can_start_processing()
            self.start_button.configure(state=tk.NORMAL if can_start else tk.DISABLED)

    # =======================
    # Обработчики событий от presenter
    # =======================

    def on_processing_completed(self, result) -> None:
        """
        Обработчик завершения обработки.

        :param result: Результат обработки OCRBatchResult
        """
        # Скрываем диалог прогресса
        if self.progress_view:
            self.progress_view.hide_dialog()

        # Показываем результат
        success_rate = result.successful_files / result.total_files * 100 if result.total_files > 0 else 0

        message = (
            f"Обработка завершена!\n\n"
            f"Обработано: {result.successful_files} из {result.total_files} файлов ({success_rate:.1f}%)\n"
            f"Время: {result.total_processing_time:.1f} секунд\n"
            f"Результат сохранен: {result.output_file_path}"
        )

        messagebox.showinfo("Обработка завершена", message)

        # Предлагаем открыть результат
        if messagebox.askyesno("Открыть результат", "Открыть файл с результатами?"):
            self._open_result_file(result.output_file_path)

    def on_processing_error(self, error_message: str) -> None:
        """
        Обработчик ошибки обработки.

        :param error_message: Сообщение об ошибке
        """
        # Скрываем диалог прогресса
        if self.progress_view:
            self.progress_view.hide_dialog()

        messagebox.showerror("Ошибка обработки", f"Произошла ошибка:\n{error_message}")

    def _open_result_file(self, file_path: str) -> None:
        """
        Открывает результирующий файл в системном редакторе.

        :param file_path: Путь к файлу
        """
        try:
            import os
            import platform

            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{file_path}'")
            else:  # Linux
                os.system(f"xdg-open '{file_path}'")

        except Exception as e:
            self.logger.error(f"Не удалось открыть файл {file_path}: {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    # ===================
    # Инициализация компонентов
    # ===================

    def initialize_progress_view(self) -> None:
        """Инициализирует диалог прогресса."""
        if not self.progress_view:
            self.progress_view = ProgressView(self.parent)
            if self.presenter:
                self.progress_view.set_presenter(self.presenter)
