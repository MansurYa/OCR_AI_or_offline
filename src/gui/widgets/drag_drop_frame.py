"""
Виджет для Drag & Drop функциональности.
Позволяет перетаскивать файлы и папки в приложение.
"""

import tkinter as tk
from tkinter import messagebox
import os
import logging
from typing import Optional, List

# Попытка импорта tkinterdnd2 для drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND_SUPPORT = True
except ImportError:
    HAS_DND_SUPPORT = False

# Импорт для типов
try:
    from ..presenters.main_presenter import MainPresenter
except ImportError:
    MainPresenter = None


class DragDropFrame(tk.Frame):
    """
    Виджет области для перетаскивания файлов.
    Поддерживает drag & drop файлов и папок с визуальной обратной связью.
    """

    def __init__(self, parent: tk.Widget):
        """
        Инициализация drag & drop области.

        :param parent: Родительский виджет
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Presenter будет установлен позже
        self.presenter: Optional[MainPresenter] = None

        # Состояние drag & drop
        self.is_drag_active = False
        self.original_bg_color = "#f8f9fa"
        self.drag_bg_color = "#e3f2fd"
        self.drag_border_color = "#2196f3"

        # Поддерживаемые форматы
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}

        # Настройка внешнего вида
        self.configure(
            bg=self.original_bg_color,
            relief=tk.RAISED,
            bd=2,
            height=120
        )

        # Создаем GUI
        self._create_gui()

        # Настройка drag & drop
        if HAS_DND_SUPPORT:
            self._setup_drag_drop()
        else:
            self._setup_fallback_interface()

    def set_presenter(self, presenter) -> None:
        """
        Устанавливает presenter для взаимодействия.

        :param presenter: Экземпляр MainPresenter
        """
        self.presenter = presenter

    def _create_gui(self) -> None:
        """Создает интерфейс drag & drop области."""
        # Основной контейнер
        main_container = tk.Frame(self, bg=self.original_bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Иконка
        icon_label = tk.Label(
            main_container,
            text="📂",
            font=("Arial", 24),
            bg=self.original_bg_color,
            fg="#6c757d"
        )
        icon_label.pack(pady=(10, 5))

        # Основной текст
        if HAS_DND_SUPPORT:
            main_text = "Перетащите файлы изображений сюда"
        else:
            main_text = "Drag & Drop не поддерживается"

        self.main_label = tk.Label(
            main_container,
            text=main_text,
            font=("Arial", 12, "bold"),
            bg=self.original_bg_color,
            fg="#495057"
        )
        self.main_label.pack(pady=2)

        # Дополнительный текст
        if HAS_DND_SUPPORT:
            sub_text = "или нажмите для выбора файлов"
        else:
            sub_text = "Используйте кнопки для добавления файлов"

        self.sub_label = tk.Label(
            main_container,
            text=sub_text,
            font=("Arial", 10),
            bg=self.original_bg_color,
            fg="#6c757d"
        )
        self.sub_label.pack(pady=2)

        # Информация о поддерживаемых форматах
        formats_text = "Поддерживаемые форматы: PNG, JPG, JPEG, TIFF, BMP, GIF"
        formats_label = tk.Label(
            main_container,
            text=formats_text,
            font=("Arial", 8),
            bg=self.original_bg_color,
            fg="#adb5bd"
        )
        formats_label.pack(pady=(10, 5))

        # Привязываем клик для файлового диалога
        self._bind_click_events(main_container)

    def _bind_click_events(self, container: tk.Widget) -> None:
        """
        Привязывает события клика к виджетам.

        :param container: Контейнер с виджетами
        """
        # Привязываем клик ко всем виджетам в контейнере
        def bind_recursive(widget):
            widget.bind("<Button-1>", self._on_click)
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(container)
        self.bind("<Button-1>", self._on_click)

    def _setup_drag_drop(self) -> None:
        """Настраивает drag & drop функциональность."""
        try:
            # Регистрируем область для drag & drop
            self.drop_target_register(DND_FILES)

            # Привязываем события drag & drop
            self.dnd_bind('<<DropEnter>>', self._on_drag_enter)
            self.dnd_bind('<<DropLeave>>', self._on_drag_leave)
            self.dnd_bind('<<Drop>>', self._on_drop)

            self.logger.info("Drag & Drop функциональность активирована")

        except Exception as e:
            self.logger.error(f"Ошибка настройки drag & drop: {e}")
            self._setup_fallback_interface()

    def _setup_fallback_interface(self) -> None:
        """Настраивает интерфейс без drag & drop."""
        self.main_label.configure(text="Используйте кнопки для добавления файлов")
        self.sub_label.configure(text="Drag & Drop недоступен в этой системе")

        # Изменяем цвета для обозначения отсутствия drag & drop
        self.configure(bg="#fff3cd", relief=tk.FLAT)
        for child in self.winfo_children():
            self._update_widget_bg(child, "#fff3cd")

    def _update_widget_bg(self, widget: tk.Widget, color: str) -> None:
        """
        Рекурсивно обновляет цвет фона виджетов.

        :param widget: Виджет для обновления
        :param color: Новый цвет фона
        """
        try:
            if hasattr(widget, 'configure'):
                widget.configure(bg=color)
            for child in widget.winfo_children():
                self._update_widget_bg(child, color)
        except tk.TclError:
            pass  # Некоторые виджеты не поддерживают изменение bg

    def _on_drag_enter(self, event) -> None:
        """Обработчик входа в область drag."""
        self.is_drag_active = True
        self._update_drag_appearance(True)

    def _on_drag_leave(self, event) -> None:
        """Обработчик выхода из области drag."""
        self.is_drag_active = False
        self._update_drag_appearance(False)

    def _on_drop(self, event) -> None:
        """
        Обработчик события drop (отпускание файлов).

        :param event: Событие с данными о файлах
        """
        self.is_drag_active = False
        self._update_drag_appearance(False)

        try:
            # Получаем список файлов из события
            files = self._parse_drop_data(event.data)

            if files:
                self._process_dropped_files(files)
            else:
                messagebox.showwarning(
                    "Нет файлов",
                    "Не обнаружено поддерживаемых файлов изображений",
                    parent=self
                )

        except Exception as e:
            self.logger.error(f"Ошибка обработки drop события: {e}")
            messagebox.showerror(
                "Ошибка",
                f"Ошибка при обработке файлов:\n{e}",
                parent=self
            )

    def _parse_drop_data(self, data: str) -> List[str]:
        """
        Парсит данные drop события для извлечения путей к файлам.

        :param data: Строка с данными от drop события
        :return: Список путей к файлам
        """
        # Удаляем фигурные скобки и разделяем по пробелам
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]

        # Разделяем пути, учитывая пробелы в именах файлов
        paths = []
        current_path = ""
        in_quotes = False

        i = 0
        while i < len(data):
            char = data[i]

            if char == '"':
                in_quotes = not in_quotes
            elif char == ' ' and not in_quotes:
                if current_path.strip():
                    paths.append(current_path.strip())
                    current_path = ""
            else:
                current_path += char

            i += 1

        # Добавляем последний путь
        if current_path.strip():
            paths.append(current_path.strip())

        # Фильтруем только существующие пути
        valid_paths = []
        for path in paths:
            # Удаляем лишние кавычки
            clean_path = path.strip('"\'')
            if os.path.exists(clean_path):
                valid_paths.append(clean_path)

        return valid_paths

    def _process_dropped_files(self, paths: List[str]) -> None:
        """
        Обрабатывает перетащенные файлы и папки.

        :param paths: Список путей к файлам и папкам
        """
        if not self.presenter:
            self.logger.warning("Presenter не установлен, невозможно обработать файлы")
            return

        files_to_add = []
        directories_to_process = []

        # Разделяем файлы и папки
        for path in paths:
            if os.path.isfile(path):
                # Проверяем формат файла
                _, ext = os.path.splitext(path)
                if ext.lower() in self.supported_formats:
                    files_to_add.append(path)
            elif os.path.isdir(path):
                directories_to_process.append(path)

        # Добавляем файлы
        if files_to_add:
            result = self.presenter.add_files(files_to_add)
            self._show_add_result(result, "файлов")

        # Обрабатываем папки
        for directory in directories_to_process:
            # Спрашиваем о рекурсивном поиске только для первой папки
            if directory == directories_to_process[0] and len(directories_to_process) == 1:
                recursive = messagebox.askyesno(
                    "Поиск в подпапках",
                    f"Искать изображения во всех подпапках папки '{os.path.basename(directory)}'?",
                    parent=self
                )
            else:
                recursive = False  # Для множественных папок используем простой поиск

            result = self.presenter.add_directory(directory, recursive)
            self._show_add_result(result, f"из папки '{os.path.basename(directory)}'")

    def _show_add_result(self, result: dict, source_description: str) -> None:
        """
        Показывает результат добавления файлов.

        :param result: Результат добавления файлов
        :param source_description: Описание источника файлов
        """
        added = len(result.get('added', []))
        skipped = len(result.get('skipped', []))
        invalid = len(result.get('invalid', []))

        if added == 0 and (skipped > 0 or invalid > 0):
            messages = []
            if skipped > 0:
                messages.append(f"Пропущено (дубликаты): {skipped}")
            if invalid > 0:
                messages.append(f"Неподдерживаемый формат: {invalid}")

            messagebox.showwarning(
                "Добавление файлов",
                f"Не добавлено новых файлов {source_description}.\n\n" + "\n".join(messages),
                parent=self
            )
        elif added > 0 and (skipped > 0 or invalid > 0):
            messages = [f"Добавлено: {added}"]
            if skipped > 0:
                messages.append(f"Пропущено: {skipped}")
            if invalid > 0:
                messages.append(f"Неверный формат: {invalid}")

            messagebox.showinfo(
                "Добавление файлов",
                f"Результат добавления {source_description}:\n\n" + "\n".join(messages),
                parent=self
            )

    def _update_drag_appearance(self, is_dragging: bool) -> None:
        """
        Обновляет внешний вид во время drag операции.

        :param is_dragging: True если идет перетаскивание
        """
        if is_dragging:
            # Стиль во время перетаскивания
            self.configure(
                bg=self.drag_bg_color,
                relief=tk.RIDGE,
                bd=3
            )

            # Обновляем текст
            if hasattr(self, 'main_label'):
                self.main_label.configure(
                    text="📥 Отпустите файлы здесь",
                    fg=self.drag_border_color
                )

            # Обновляем цвет фона дочерних виджетов
            for child in self.winfo_children():
                self._update_widget_bg(child, self.drag_bg_color)
        else:
            # Обычный стиль
            self.configure(
                bg=self.original_bg_color,
                relief=tk.RAISED,
                bd=2
            )

            # Восстанавливаем текст
            if hasattr(self, 'main_label'):
                if HAS_DND_SUPPORT:
                    text = "Перетащите файлы изображений сюда"
                else:
                    text = "Используйте кнопки для добавления файлов"

                self.main_label.configure(
                    text=text,
                    fg="#495057"
                )

            # Восстанавливаем цвет фона дочерних виджетов
            for child in self.winfo_children():
                self._update_widget_bg(child, self.original_bg_color)

    def _on_click(self, event) -> None:
        """Обработчик клика для открытия файлового диалога."""
        if not self.presenter:
            return

        from tkinter import filedialog

        filetypes = [
            ("Изображения", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif"),
            ("PNG файлы", "*.png"),
            ("JPEG файлы", "*.jpg *.jpeg"),
            ("Все файлы", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=filetypes,
            parent=self
        )

        if files:
            result = self.presenter.add_files(list(files))
            self._show_add_result(result, "через диалог выбора")

    def update_supported_formats(self, formats: set) -> None:
        """
        Обновляет список поддерживаемых форматов.

        :param formats: Новый набор поддерживаемых форматов
        """
        self.supported_formats = formats

        # Обновляем текст с форматами
        formats_text = "Поддерживаемые форматы: " + ", ".join(
            fmt.upper().lstrip('.') for fmt in sorted(formats)
        )

        # Находим и обновляем label с форматами
        for child in self.winfo_children():
            for subchild in child.winfo_children():
                if isinstance(subchild, tk.Label) and "Поддерживаемые форматы" in subchild.cget("text"):
                    subchild.configure(text=formats_text)
                    break

    def set_enabled(self, enabled: bool) -> None:
        """
        Включает или отключает drag & drop область.

        :param enabled: True для включения, False для отключения
        """
        if enabled:
            self.configure(state=tk.NORMAL)
            if hasattr(self, 'main_label'):
                if HAS_DND_SUPPORT:
                    self.main_label.configure(text="Перетащите файлы изображений сюда")
                else:
                    self.main_label.configure(text="Используйте кнопки для добавления файлов")
                self.main_label.configure(fg="#495057")
        else:
            self.configure(state=tk.DISABLED)
            if hasattr(self, 'main_label'):
                self.main_label.configure(
                    text="Добавление файлов отключено во время обработки",
                    fg="#adb5bd"
                )

    def get_drag_drop_status(self) -> dict:
        """
        Возвращает информацию о статусе drag & drop.

        :return: Словарь с информацией о статусе
        """
        return {
            'has_dnd_support': HAS_DND_SUPPORT,
            'is_drag_active': self.is_drag_active,
            'supported_formats': list(self.supported_formats),
            'is_enabled': str(self.cget('state')) != 'disabled'
        }
