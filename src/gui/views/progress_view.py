"""
Представление диалога прогресса обработки OCR.
Показывает прогресс-бар, текущий файл и позволяет отменить обработку.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional

from ..models.app_model import ProcessingState

# Импорт для типов
try:
    from ..presenters.main_presenter import MainPresenter
except ImportError:
    MainPresenter = None


class ProgressView:
    """
    Представление диалога прогресса OCR обработки.
    Показывает детальную информацию о ходе обработки.
    """

    def __init__(self, parent: tk.Widget):
        """
        Инициализация представления прогресса.

        :param parent: Родительское окно
        """
        self.parent = parent
        self.logger = logging.getLogger(__name__)

        # Presenter будет установлен позже
        self.presenter: Optional[MainPresenter] = None

        # Диалоговое окно
        self.dialog: Optional[tk.Toplevel] = None

        # Переменные для отображения
        self.progress_var = tk.DoubleVar()
        self.current_file_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.speed_var = tk.StringVar()

        # Виджеты
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.current_file_label: Optional[tk.Label] = None
        self.status_label: Optional[tk.Label] = None
        self.time_label: Optional[tk.Label] = None
        self.speed_label: Optional[tk.Label] = None
        self.cancel_button: Optional[tk.Button] = None
        self.pause_button: Optional[tk.Button] = None

        # Состояние
        self.is_visible = False
        self.can_pause = False

    def set_presenter(self, presenter) -> None:
        """
        Устанавливает presenter для взаимодействия.

        :param presenter: Экземпляр MainPresenter
        """
        self.presenter = presenter

    def show_dialog(self) -> None:
        """Показывает диалог прогресса."""
        if self.is_visible:
            return

        self._create_dialog()
        self.is_visible = True

        # Инициализируем начальные значения
        self.progress_var.set(0)
        self.current_file_var.set("Подготовка...")
        self.status_var.set("Запуск обработки")
        self.time_var.set("Время: 00:00")
        self.speed_var.set("Скорость: -- файлов/мин")

    def hide_dialog(self) -> None:
        """Скрывает диалог прогресса."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None

        self.is_visible = False

    def _create_dialog(self) -> None:
        """Создает диалоговое окно прогресса."""
        # Создаем модальное окно
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Обработка OCR")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Центрируем окно
        self._center_dialog()

        # Обработчик закрытия окна
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_dialog_close)

        # Создаем содержимое
        self._create_dialog_content()

    def _center_dialog(self) -> None:
        """Центрирует диалог относительно родительского окна."""
        self.dialog.update_idletasks()

        # Получаем размеры окон
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Вычисляем позицию для центрирования
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_dialog_content(self) -> None:
        """Создает содержимое диалога прогресса."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = tk.Label(
            main_frame,
            text="🔍 Обработка изображений OCR",
            font=("Arial", 14, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 20))

        # Прогресс-бар
        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        progress_label = tk.Label(
            progress_frame,
            text="Общий прогресс:",
            font=("Arial", 10, "bold")
        )
        progress_label.pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            style="TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

        # Процент выполнения
        self.progress_percent_label = tk.Label(
            progress_frame,
            text="0%",
            font=("Arial", 9),
            fg="#3498db"
        )
        self.progress_percent_label.pack(anchor=tk.E, pady=(2, 0))

        # Текущий файл
        current_frame = tk.Frame(main_frame)
        current_frame.pack(fill=tk.X, pady=(0, 15))

        current_title = tk.Label(
            current_frame,
            text="Текущий файл:",
            font=("Arial", 10, "bold")
        )
        current_title.pack(anchor=tk.W)

        self.current_file_label = tk.Label(
            current_frame,
            textvariable=self.current_file_var,
            font=("Arial", 9),
            fg="#34495e",
            wraplength=450,
            justify=tk.LEFT
        )
        self.current_file_label.pack(anchor=tk.W, pady=(2, 0))

        # Статус и время
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 20))

        # Левый столбец - статус
        left_info = tk.Frame(info_frame)
        left_info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = tk.Label(
            left_info,
            textvariable=self.status_var,
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.status_label.pack(anchor=tk.W)

        self.time_label = tk.Label(
            left_info,
            textvariable=self.time_var,
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.time_label.pack(anchor=tk.W, pady=(2, 0))

        # Правый столбец - скорость
        right_info = tk.Frame(info_frame)
        right_info.pack(side=tk.RIGHT)

        self.speed_label = tk.Label(
            right_info,
            textvariable=self.speed_var,
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.speed_label.pack(anchor=tk.E)

        # Кнопки управления
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        # Кнопка паузы (пока скрыта, может быть добавлена в будущем)
        self.pause_button = tk.Button(
            buttons_frame,
            text="⏸️ Пауза",
            command=self._on_pause_click,
            bg="#f39c12",
            fg="white",
            state=tk.DISABLED,
            width=12
        )
        # self.pause_button.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка отмены
        self.cancel_button = tk.Button(
            buttons_frame,
            text="❌ Отменить",
            command=self._on_cancel_click,
            bg="#e74c3c",
            fg="white",
            width=12
        )
        self.cancel_button.pack(side=tk.RIGHT)

        # Кнопка "Скрыть в фон"
        minimize_button = tk.Button(
            buttons_frame,
            text="📦 Скрыть",
            command=self._on_minimize_click,
            bg="#95a5a6",
            fg="white",
            width=12
        )
        minimize_button.pack(side=tk.RIGHT, padx=(0, 10))

    def update_progress(self, state: ProcessingState) -> None:
        """
        Обновляет отображение прогресса.

        :param state: Состояние обработки
        """
        if not self.is_visible or not self.dialog:
            return

        # Обновляем прогресс-бар
        self.progress_var.set(state.progress_percentage)

        # Обновляем процент
        if hasattr(self, 'progress_percent_label'):
            self.progress_percent_label.configure(text=f"{state.progress_percentage:.1f}%")

        # Обновляем текущий файл
        if state.current_filename:
            if state.is_running:
                current_text = f"📄 {state.current_filename}"
                if state.total_files > 0:
                    current_text += f" ({state.current_file_index}/{state.total_files})"
            else:
                current_text = state.current_filename

            self.current_file_var.set(current_text)

        # Обновляем статус
        if state.is_running:
            if state.current_file_index > 0 and state.total_files > 0:
                remaining = state.total_files - state.current_file_index
                self.status_var.set(f"Обрабатываем... (осталось: {remaining})")
            else:
                self.status_var.set("Обрабатываем...")
        else:
            if state.progress_percentage >= 100:
                self.status_var.set("✅ Обработка завершена")
            else:
                self.status_var.set("⏹️ Обработка остановлена")

        # Обновляем время (примерное, так как точное время нужно отслеживать отдельно)
        if hasattr(state, 'elapsed_time'):
            elapsed_minutes = int(state.elapsed_time // 60)
            elapsed_seconds = int(state.elapsed_time % 60)
            self.time_var.set(f"Время: {elapsed_minutes:02d}:{elapsed_seconds:02d}")

        # Обновляем скорость
        if hasattr(state, 'processing_speed') and state.processing_speed > 0:
            speed_per_minute = state.processing_speed * 60
            self.speed_var.set(f"Скорость: {speed_per_minute:.1f} файлов/мин")

        # Обновляем состояние кнопок
        if state.is_running:
            self.cancel_button.configure(state=tk.NORMAL)
            if hasattr(state, 'can_pause') and state.can_pause:
                self.pause_button.configure(state=tk.NORMAL)
        else:
            self.cancel_button.configure(text="✅ Закрыть", bg="#27ae60")

    def _format_time(self, seconds: float) -> str:
        """
        Форматирует время в читаемый вид.

        :param seconds: Время в секундах
        :return: Отформатированная строка времени
        """
        if seconds < 60:
            return f"{int(seconds)}с"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}м {secs}с"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}ч {minutes}м"

    # ========================
    # Обработчики событий
    # ========================

    def _on_pause_click(self) -> None:
        """Обработчик кнопки паузы."""
        if self.presenter:
            # Здесь можно добавить логику паузы/возобновления
            # Пока что эта функция не реализована в presenter
            pass

    def _on_cancel_click(self) -> None:
        """Обработчик кнопки отмены."""
        if self.presenter:
            # Проверяем, идет ли обработка
            state = self.presenter.get_processing_state()

            if state.is_running:
                # Подтверждение отмены
                import tkinter.messagebox as messagebox
                if messagebox.askyesno(
                    "Подтверждение отмены",
                    "Вы действительно хотите отменить обработку?",
                    parent=self.dialog
                ):
                    self.presenter.cancel_processing()
            else:
                # Если обработка не идет, просто закрываем диалог
                self.hide_dialog()

    def _on_minimize_click(self) -> None:
        """Обработчик кнопки скрытия в фон."""
        if self.dialog:
            self.dialog.withdraw()  # Скрываем окно, но не уничтожаем

        # Можно добавить иконку в трей или создать маленький виджет прогресса
        self._create_minimized_progress()

    def _on_dialog_close(self) -> None:
        """Обработчик закрытия диалога через X."""
        if self.presenter:
            state = self.presenter.get_processing_state()

            if state.is_running:
                # Предлагаем скрыть вместо закрытия
                import tkinter.messagebox as messagebox
                result = messagebox.askyesnocancel(
                    "Закрытие окна",
                    "Обработка еще выполняется.\n\n"
                    "Да - Отменить обработку и закрыть\n"
                    "Нет - Скрыть окно в фон\n"
                    "Отмена - Оставить окно открытым",
                    parent=self.dialog
                )

                if result is True:  # Да - отменить и закрыть
                    self.presenter.cancel_processing()
                    self.hide_dialog()
                elif result is False:  # Нет - скрыть в фон
                    self._on_minimize_click()
                # При None (Отмена) ничего не делаем
            else:
                # Обработка не идет, можно закрывать
                self.hide_dialog()

    def _create_minimized_progress(self) -> None:
        """Создает минимизированный виджет прогресса."""
        # Создаем маленькое окошко с прогрессом
        mini_window = tk.Toplevel(self.parent)
        mini_window.title("OCR Progress")
        mini_window.geometry("300x80")
        mini_window.resizable(False, False)

        # Позиционируем в правом нижнем углу
        mini_window.update_idletasks()
        screen_width = mini_window.winfo_screenwidth()
        screen_height = mini_window.winfo_screenheight()
        x = screen_width - 320
        y = screen_height - 150
        mini_window.geometry(f"+{x}+{y}")

        # Делаем окно поверх других
        mini_window.attributes('-topmost', True)

        # Содержимое мини-окна
        frame = tk.Frame(mini_window, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Мини прогресс-бар
        mini_progress = ttk.Progressbar(
            frame,
            variable=self.progress_var,
            maximum=100,
            length=200
        )
        mini_progress.pack(fill=tk.X)

        # Статус
        mini_status = tk.Label(
            frame,
            textvariable=self.status_var,
            font=("Arial", 8)
        )
        mini_status.pack(pady=(5, 0))

        # Кнопки
        mini_buttons = tk.Frame(frame)
        mini_buttons.pack(fill=tk.X, pady=(5, 0))

        show_button = tk.Button(
            mini_buttons,
            text="Показать",
            command=lambda: self._restore_dialog(mini_window),
            font=("Arial", 8),
            height=1
        )
        show_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        cancel_button = tk.Button(
            mini_buttons,
            text="Отмена",
            command=lambda: self._cancel_from_mini(mini_window),
            font=("Arial", 8),
            height=1,
            bg="#e74c3c",
            fg="white"
        )
        cancel_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Сохраняем ссылку на мини-окно
        self.mini_window = mini_window

    def _restore_dialog(self, mini_window: tk.Toplevel) -> None:
        """
        Восстанавливает главный диалог прогресса.

        :param mini_window: Мини-окно для закрытия
        """
        mini_window.destroy()
        if hasattr(self, 'mini_window'):
            delattr(self, 'mini_window')

        if self.dialog:
            self.dialog.deiconify()  # Показываем основное окно
            self.dialog.lift()  # Поднимаем на передний план

    def _cancel_from_mini(self, mini_window: tk.Toplevel) -> None:
        """
        Отменяет обработку из мини-окна.

        :param mini_window: Мини-окно для закрытия
        """
        if self.presenter:
            self.presenter.cancel_processing()

        mini_window.destroy()
        if hasattr(self, 'mini_window'):
            delattr(self, 'mini_window')

    def is_dialog_visible(self) -> bool:
        """
        Проверяет, видим ли диалог прогресса.

        :return: True если диалог видим
        """
        return self.is_visible and self.dialog and self.dialog.winfo_viewable()

    def bring_to_front(self) -> None:
        """Выводит диалог на передний план."""
        if self.dialog:
            self.dialog.lift()
            self.dialog.focus_force()
