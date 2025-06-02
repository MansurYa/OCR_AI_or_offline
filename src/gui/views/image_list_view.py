"""
Представление списка изображений.
Отображает список добавленных файлов с возможностью управления.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
from typing import List, Optional

from ..models.app_model import ImageFile

# Импорт для типов
try:
    from ..presenters.main_presenter import MainPresenter
except ImportError:
    MainPresenter = None


class ImageListView(tk.Frame):
    """
    Представление для отображения и управления списком изображений.
    """

    def __init__(self, parent: tk.Widget):
        """
        Инициализация представления списка изображений.

        :param parent: Родительский виджет
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Presenter будет установлен позже
        self.presenter: Optional[MainPresenter] = None

        # Компоненты GUI
        self.treeview: Optional[ttk.Treeview] = None
        self.scrollbar_v: Optional[ttk.Scrollbar] = None
        self.scrollbar_h: Optional[ttk.Scrollbar] = None

        # Контекстное меню
        self.context_menu: Optional[tk.Menu] = None
        self.selected_item_index: int = -1

        # Создаем GUI
        self._create_gui()
        self._setup_bindings()

    def set_presenter(self, presenter) -> None:
        """
        Устанавливает presenter для взаимодействия.

        :param presenter: Экземпляр MainPresenter
        """
        self.presenter = presenter

    def _create_gui(self) -> None:
        """Создает интерфейс списка изображений."""
        # Заголовок списка
        header_frame = tk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        title_label = tk.Label(
            header_frame,
            text="📋 Список изображений",
            font=("Arial", 10, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Информация о файлах
        self.info_label = tk.Label(
            header_frame,
            text="Файлов: 0",
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.info_label.pack(side=tk.RIGHT)

        # Контейнер для treeview и scrollbars
        tree_container = tk.Frame(self)
        tree_container.pack(fill=tk.BOTH, expand=True)

        # Создаем treeview с колонками
        columns = ("filename", "size", "status")
        self.treeview = ttk.Treeview(tree_container, columns=columns, show="tree headings", height=10)

        # Настраиваем колонки
        self.treeview.heading("#0", text="№", anchor=tk.W)
        self.treeview.heading("filename", text="Имя файла", anchor=tk.W)
        self.treeview.heading("size", text="Размер", anchor=tk.E)
        self.treeview.heading("status", text="Статус", anchor=tk.CENTER)

        # Ширина колонок
        self.treeview.column("#0", width=40, minwidth=30, stretch=False)
        self.treeview.column("filename", width=300, minwidth=200, stretch=True)
        self.treeview.column("size", width=80, minwidth=60, stretch=False)
        self.treeview.column("status", width=80, minwidth=60, stretch=False)

        # Вертикальный scrollbar
        self.scrollbar_v = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.scrollbar_v.set)

        # Горизонтальный scrollbar
        self.scrollbar_h = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(xscrollcommand=self.scrollbar_h.set)

        # Размещение элементов
        self.treeview.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")
        self.scrollbar_h.grid(row=1, column=0, sticky="ew")

        # Настройка grid
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Создаем контекстное меню
        self._create_context_menu()

    def _create_context_menu(self) -> None:
        """Создает контекстное меню для элементов списка."""
        self.context_menu = tk.Menu(self, tearoff=0)

        self.context_menu.add_command(
            label="🗑️ Удалить",
            command=self._on_remove_file
        )

        self.context_menu.add_separator()

        self.context_menu.add_command(
            label="⬆️ Переместить вверх",
            command=self._on_move_up
        )

        self.context_menu.add_command(
            label="⬇️ Переместить вниз",
            command=self._on_move_down
        )

        self.context_menu.add_separator()

        self.context_menu.add_command(
            label="📁 Показать в проводнике",
            command=self._on_show_in_explorer
        )

        self.context_menu.add_command(
            label="ℹ️ Свойства файла",
            command=self._on_show_properties
        )

    def _setup_bindings(self) -> None:
        """Настраивает обработчики событий."""
        # Правый клик для контекстного меню
        self.treeview.bind("<Button-3>", self._on_right_click)

        # Двойной клик для просмотра свойств
        self.treeview.bind("<Double-1>", self._on_double_click)

        # Клавиши Delete для удаления
        self.treeview.bind("<Delete>", self._on_delete_key)

        # Выбор элемента
        self.treeview.bind("<<TreeviewSelect>>", self._on_selection_changed)

    def update_file_list(self, files: List[ImageFile]) -> None:
        """
        Обновляет список файлов в treeview.

        :param files: Список файлов для отображения
        """
        # Очищаем текущий список
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        # Добавляем новые файлы
        for i, file_info in enumerate(files, 1):
            # Форматируем размер файла
            size_str = self._format_file_size(file_info.size)

            # Определяем статус и цвет
            if file_info.is_valid:
                status = "✅ OK"
                tags = ("valid",)
            else:
                status = "❌ Ошибка"
                tags = ("invalid",)

            # Добавляем элемент
            item_id = self.treeview.insert(
                "",
                tk.END,
                text=str(i),
                values=(file_info.filename, size_str, status),
                tags=tags
            )

            # Сохраняем индекс файла в item_id для обратной связи
            # Используем file_info.path как уникальный идентификатор

        # Настраиваем теги для цветового кодирования
        self.treeview.tag_configure("valid", foreground="#27ae60")
        self.treeview.tag_configure("invalid", foreground="#e74c3c")

        # Обновляем информационную панель
        self._update_info_label(files)

    def _update_info_label(self, files: List[ImageFile]) -> None:
        """
        Обновляет информационную панель.

        :param files: Список файлов
        """
        total_files = len(files)
        valid_files = sum(1 for f in files if f.is_valid)
        total_size = sum(f.size for f in files if f.is_valid)

        if total_files == 0:
            info_text = "Файлов: 0"
        else:
            size_str = self._format_file_size(total_size)

            if valid_files == total_files:
                info_text = f"Файлов: {total_files}, Размер: {size_str}"
            else:
                invalid_count = total_files - valid_files
                info_text = f"Файлов: {valid_files}/{total_files}, Размер: {size_str} (⚠️ {invalid_count} ошибок)"

        self.info_label.configure(text=info_text)

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Форматирует размер файла в читаемый вид.

        :param size_bytes: Размер в байтах
        :return: Отформатированная строка
        """
        if size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB"]
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"

    def _get_selected_file_index(self) -> int:
        """
        Возвращает индекс выбранного файла.

        :return: Индекс файла или -1 если ничего не выбрано
        """
        selection = self.treeview.selection()
        if not selection:
            return -1

        try:
            # Получаем номер из первой колонки (начинается с 1)
            item_text = self.treeview.item(selection[0], "text")
            return int(item_text) - 1  # Конвертируем в 0-based индекс
        except (ValueError, IndexError):
            return -1

    def _get_file_info_by_selection(self) -> Optional[ImageFile]:
        """
        Возвращает информацию о выбранном файле.

        :return: ImageFile или None
        """
        if not self.presenter:
            return None

        index = self._get_selected_file_index()
        if index >= 0:
            return self.presenter.get_file_info(index)

        return None

    # ========================
    # Обработчики событий
    # ========================

    def _on_right_click(self, event) -> None:
        """Обработчик правого клика для показа контекстного меню."""
        # Выбираем элемент под курсором
        item = self.treeview.identify_row(event.y)
        if item:
            self.treeview.selection_set(item)
            self.selected_item_index = self._get_selected_file_index()

            # Обновляем состояние пунктов меню
            self._update_context_menu_state()

            # Показываем контекстное меню
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _on_double_click(self, event) -> None:
        """Обработчик двойного клика для показа свойств файла."""
        item = self.treeview.identify_row(event.y)
        if item:
            self.treeview.selection_set(item)
            self._on_show_properties()

    def _on_delete_key(self, event) -> None:
        """Обработчик клавиши Delete для удаления файла."""
        self._on_remove_file()

    def _on_selection_changed(self, event) -> None:
        """Обработчик изменения выбора в списке."""
        # Можно добавить дополнительную логику при изменении выбора
        pass

    def _update_context_menu_state(self) -> None:
        """Обновляет состояние пунктов контекстного меню."""
        if not self.presenter:
            return

        index = self.selected_item_index
        total_files = len(self.presenter.get_image_files())

        # Проверяем возможность перемещения
        can_move_up = index > 0
        can_move_down = index >= 0 and index < total_files - 1

        # Обновляем состояние пунктов меню
        menu_states = {
            1: tk.NORMAL if index >= 0 else tk.DISABLED,  # Удалить
            3: tk.NORMAL if can_move_up else tk.DISABLED,  # Вверх
            4: tk.NORMAL if can_move_down else tk.DISABLED,  # Вниз
            6: tk.NORMAL if index >= 0 else tk.DISABLED,  # Показать в проводнике
            7: tk.NORMAL if index >= 0 else tk.DISABLED,  # Свойства
        }

        for menu_index, state in menu_states.items():
            try:
                self.context_menu.entryconfig(menu_index, state=state)
            except tk.TclError:
                pass  # Игнорируем ошибки для разделителей

    # ===========================
    # Действия контекстного меню
    # ===========================

    def _on_remove_file(self) -> None:
        """Удаляет выбранный файл."""
        if not self.presenter:
            return

        index = self._get_selected_file_index()
        if index >= 0:
            file_info = self.presenter.get_file_info(index)
            if file_info:
                if messagebox.askyesno(
                    "Подтверждение удаления",
                    f"Удалить '{file_info.filename}' из списка?"
                ):
                    self.presenter.remove_file(index)

    def _on_move_up(self) -> None:
        """Перемещает файл вверх по списку."""
        if not self.presenter:
            return

        index = self._get_selected_file_index()
        if index > 0:
            success = self.presenter.move_file(index, index - 1)
            if success:
                # Восстанавливаем выбор на новой позиции
                self._select_item_by_index(index - 1)

    def _on_move_down(self) -> None:
        """Перемещает файл вниз по списку."""
        if not self.presenter:
            return

        index = self._get_selected_file_index()
        total_files = len(self.presenter.get_image_files())

        if index >= 0 and index < total_files - 1:
            success = self.presenter.move_file(index, index + 1)
            if success:
                # Восстанавливаем выбор на новой позиции
                self._select_item_by_index(index + 1)

    def _on_show_in_explorer(self) -> None:
        """Показывает файл в проводнике системы."""
        file_info = self._get_file_info_by_selection()
        if not file_info:
            return

        try:
            import platform
            import subprocess

            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_info.path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_info.path])
            else:  # Linux
                subprocess.run(["xdg-open", os.path.dirname(file_info.path)])

        except Exception as e:
            self.logger.error(f"Не удалось показать файл в проводнике: {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть проводник:\n{e}")

    def _on_show_properties(self) -> None:
        """Показывает свойства выбранного файла."""
        file_info = self._get_file_info_by_selection()
        if not file_info:
            return

        # Создаем окно со свойствами файла
        self._show_file_properties_dialog(file_info)

    def _show_file_properties_dialog(self, file_info: ImageFile) -> None:
        """
        Показывает диалог со свойствами файла.

        :param file_info: Информация о файле
        """
        # Создаем модальное окно
        dialog = tk.Toplevel(self)
        dialog.title(f"Свойства: {file_info.filename}")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Создаем содержимое
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = tk.Label(
            main_frame,
            text=file_info.filename,
            font=("Arial", 12, "bold"),
            wraplength=350
        )
        title_label.pack(pady=(0, 15))

        # Свойства файла
        properties = [
            ("Полный путь:", file_info.path),
            ("Размер файла:", self._format_file_size(file_info.size)),
            ("Статус:", "✅ Готов к обработке" if file_info.is_valid else "❌ Ошибка"),
        ]

        if not file_info.is_valid and file_info.error_message:
            properties.append(("Ошибка:", file_info.error_message))

        # Добавляем информацию о файле если он существует
        if os.path.exists(file_info.path):
            try:
                import time
                stat_info = os.stat(file_info.path)

                mod_time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(stat_info.st_mtime))
                properties.append(("Дата изменения:", mod_time))

                # Тип файла
                _, ext = os.path.splitext(file_info.path)
                properties.append(("Тип файла:", f"Изображение {ext.upper()}"))

            except (OSError, IOError):
                pass

        # Отображаем свойства
        for label_text, value_text in properties:
            prop_frame = tk.Frame(main_frame)
            prop_frame.pack(fill=tk.X, pady=2)

            label = tk.Label(
                prop_frame,
                text=label_text,
                font=("Arial", 9, "bold"),
                anchor=tk.W,
                width=15
            )
            label.pack(side=tk.LEFT)

            value = tk.Label(
                prop_frame,
                text=value_text,
                font=("Arial", 9),
                anchor=tk.W,
                wraplength=250,
                justify=tk.LEFT
            )
            value.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопка закрытия
        close_button = tk.Button(
            main_frame,
            text="Закрыть",
            command=dialog.destroy,
            width=10
        )
        close_button.pack(pady=(20, 0))

    def _select_item_by_index(self, index: int) -> None:
        """
        Выбирает элемент списка по индексу.

        :param index: Индекс элемента (0-based)
        """
        children = self.treeview.get_children()
        if 0 <= index < len(children):
            item_id = children[index]
            self.treeview.selection_set(item_id)
            self.treeview.focus(item_id)
            self.treeview.see(item_id)

    def get_selected_files(self) -> List[int]:
        """
        Возвращает индексы всех выбранных файлов.

        :return: Список индексов
        """
        selected_indices = []
        for item_id in self.treeview.selection():
            try:
                item_text = self.treeview.item(item_id, "text")
                index = int(item_text) - 1  # Конвертируем в 0-based
                selected_indices.append(index)
            except (ValueError, IndexError):
                continue

        return selected_indices

    def clear_selection(self) -> None:
        """Очищает выбор в списке."""
        self.treeview.selection_remove(self.treeview.selection())
