"""
Главное окно приложения OCR AI or Offline.
Объединяет все GUI компоненты и координирует работу MVP архитектуры.
"""

import tkinter as tk
from tkinter import messagebox
import logging
import sys
import os

# Попытка импорта tkinterdnd2 для drag & drop
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND_SUPPORT = True
except ImportError:
    HAS_DND_SUPPORT = False

# Добавляем путь к src директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.presenters.main_presenter import MainPresenter
from gui.views.main_view import MainView
from gui.widgets.custom_widgets import StatusBar, add_tooltip


class MainWindow:
    """
    Главное окно приложения OCR AI or Offline.
    Управляет жизненным циклом приложения и координирует MVP компоненты.
    """

    def __init__(self):
        """Инициализация главного окна приложения."""
        self.logger = logging.getLogger(__name__)

        # Создаем главное окно
        if HAS_DND_SUPPORT:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        # MVP компоненты
        self.presenter: MainPresenter = MainPresenter()
        self.main_view: MainView = MainView(self.root)

        # Статусная строка
        self.status_bar: StatusBar = StatusBar(self.root)

        # Настройка окна
        self._configure_window()
        self._setup_mvp()
        self._setup_menu()
        self._setup_bindings()

        # Инициализация компонентов
        self._initialize_components()

        self.logger.info("Главное окно приложения инициализировано")

    def _configure_window(self) -> None:
        """Настраивает основные параметры окна."""
        # Получаем настройки размера окна
        settings = self.presenter.get_settings()

        # Заголовок и иконка
        self.root.title("🔍 OCR AI or Offline - Распознавание текста")

        # Размер окна
        width = settings.gui_settings.window_width
        height = settings.gui_settings.window_height
        self.root.geometry(f"{width}x{height}")

        # Минимальный размер
        self.root.minsize(800, 600)

        # Центрирование окна на экране
        self._center_window()

        # Настройка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Настройка изменения размера
        self.root.bind("<Configure>", self._on_window_configure)

        # Настройка темы (пока базовая)
        self._setup_theme()

    def _center_window(self) -> None:
        """Центрирует окно на экране."""
        self.root.update_idletasks()

        # Получаем размеры
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Вычисляем позицию для центрирования
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"+{x}+{y}")

    def _setup_theme(self) -> None:
        """Настраивает тему приложения."""
        # Базовые цвета для светлой темы
        colors = {
            'bg': '#ffffff',
            'fg': '#2c3e50',
            'select_bg': '#3498db',
            'select_fg': '#ffffff',
            'disabled_bg': '#ecf0f1',
            'disabled_fg': '#95a5a6'
        }

        # Применяем цвета к основному окну
        self.root.configure(bg=colors['bg'])

        # Настройка стилей ttk (если понадобится в будущем)
        try:
            import tkinter.ttk as ttk
            style = ttk.Style()

            # Стиль для прогресс-бара
            style.configure(
                "Custom.Horizontal.TProgressbar",
                background=colors['select_bg'],
                troughcolor=colors['disabled_bg'],
                borderwidth=0,
                lightcolor=colors['select_bg'],
                darkcolor=colors['select_bg']
            )

        except Exception as e:
            self.logger.warning(f"Не удалось настроить ttk стили: {e}")

    def _setup_mvp(self) -> None:
        """Настраивает MVP архитектуру."""
        # Связываем presenter и view
        self.presenter.set_main_view(self.main_view)
        self.main_view.set_presenter(self.presenter)

        # Инициализируем прогресс view
        self.main_view.initialize_progress_view()

    def _setup_menu(self) -> None:
        """Создает главное меню приложения."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)

        file_menu.add_command(
            label="📁 Добавить файлы...",
            command=self._menu_add_files,
            accelerator="Ctrl+O"
        )

        file_menu.add_command(
            label="📂 Добавить папку...",
            command=self._menu_add_folder,
            accelerator="Ctrl+Shift+O"
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="💾 Сохранить настройки",
            command=self._menu_save_settings,
            accelerator="Ctrl+S"
        )

        file_menu.add_command(
            label="📤 Экспорт настроек...",
            command=self._menu_export_settings
        )

        file_menu.add_command(
            label="📥 Импорт настроек...",
            command=self._menu_import_settings
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="🚪 Выход",
            command=self._on_closing,
            accelerator="Ctrl+Q"
        )

        # Меню "Правка"
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)

        edit_menu.add_command(
            label="🗑️ Очистить список",
            command=self._menu_clear_files,
            accelerator="Ctrl+Delete"
        )

        edit_menu.add_command(
            label="🔄 Обновить файлы",
            command=self._menu_refresh_files,
            accelerator="F5"
        )

        edit_menu.add_separator()

        edit_menu.add_command(
            label="⚙️ Настройки...",
            command=self._menu_show_settings,
            accelerator="Ctrl+,"
        )

        # Меню "Обработка"
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Обработка", menu=process_menu)

        process_menu.add_command(
            label="🚀 Начать OCR",
            command=self._menu_start_processing,
            accelerator="F9"
        )

        process_menu.add_command(
            label="⏹️ Остановить OCR",
            command=self._menu_stop_processing,
            accelerator="Escape"
        )

        process_menu.add_separator()

        process_menu.add_command(
            label="🔧 Тест соединения",
            command=self._menu_test_connection
        )

        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)

        help_menu.add_command(
            label="❓ Справка",
            command=self._menu_show_help,
            accelerator="F1"
        )

        help_menu.add_command(
            label="🔗 О программе",
            command=self._menu_show_about
        )

    def _setup_bindings(self) -> None:
        """Настраивает горячие клавиши."""
        # Горячие клавиши для меню
        self.root.bind("<Control-o>", lambda e: self._menu_add_files())
        self.root.bind("<Control-Shift-O>", lambda e: self._menu_add_folder())
        self.root.bind("<Control-s>", lambda e: self._menu_save_settings())
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        self.root.bind("<Control-Delete>", lambda e: self._menu_clear_files())
        self.root.bind("<F5>", lambda e: self._menu_refresh_files())
        self.root.bind("<Control-comma>", lambda e: self._menu_show_settings())
        self.root.bind("<F9>", lambda e: self._menu_start_processing())
        self.root.bind("<Escape>", lambda e: self._menu_stop_processing())
        self.root.bind("<F1>", lambda e: self._menu_show_help())

    def _initialize_components(self) -> None:
        """Инициализирует компоненты после создания GUI."""
        # Размещаем основное представление
        self.main_view.pack(fill=tk.BOTH, expand=True)

        # Размещаем статусную строку
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Связываем статусную строку с presenter
        self._connect_status_bar()

        # Уведомляем presenter о запуске
        self.presenter.on_application_start()

        # Добавляем подсказки к элементам интерфейса
        self._add_tooltips()

    def _connect_status_bar(self) -> None:
        """Связывает статусную строку с presenter."""
        # Подписываемся на изменения в presenter для обновления статуса
        original_update_status = self.main_view.update_status

        def enhanced_update_status(message: str):
            original_update_status(message)
            self.status_bar.set_status(message)

        self.main_view.update_status = enhanced_update_status

    def _add_tooltips(self) -> None:
        """Добавляет всплывающие подсказки к элементам интерфейса."""
        # Можно добавить подсказки к кнопкам и другим элементам
        # add_tooltip(self.main_view.start_button, "Запустить обработку OCR для всех добавленных изображений")
        pass

    # ========================
    # Обработчики меню
    # ========================

    def _menu_add_files(self) -> None:
        """Обработчик меню добавления файлов."""
        self.main_view._on_add_files_click()

    def _menu_add_folder(self) -> None:
        """Обработчик меню добавления папки."""
        self.main_view._on_add_folder_click()

    def _menu_save_settings(self) -> None:
        """Обработчик сохранения настроек."""
        settings = self.presenter.get_settings()
        if settings.save_settings():
            self.status_bar.set_status("Настройки сохранены", "success")
        else:
            self.status_bar.set_status("Ошибка сохранения настроек", "error")

    def _menu_export_settings(self) -> None:
        """Обработчик экспорта настроек."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Экспорт настроек",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )

        if filename:
            settings = self.presenter.get_settings()
            if settings.export_settings(filename):
                self.status_bar.set_status(f"Настройки экспортированы: {filename}", "success")
            else:
                self.status_bar.set_status("Ошибка экспорта настроек", "error")

    def _menu_import_settings(self) -> None:
        """Обработчик импорта настроек."""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Импорт настроек",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )

        if filename:
            settings = self.presenter.get_settings()
            if settings.import_settings(filename):
                self.status_bar.set_status(f"Настройки импортированы: {filename}", "success")
                # Обновляем интерфейс
                self.main_view.update_settings_display()
            else:
                self.status_bar.set_status("Ошибка импорта настроек", "error")

    def _menu_clear_files(self) -> None:
        """Обработчик очистки списка файлов."""
        self.main_view._on_clear_click()

    def _menu_refresh_files(self) -> None:
        """Обработчик обновления списка файлов."""
        self.presenter.validate_files()
        self.status_bar.set_status("Список файлов обновлен", "info")

    def _menu_show_settings(self) -> None:
        """Обработчик показа настроек."""
        messagebox.showinfo(
            "Настройки",
            "Настройки доступны в правой панели главного окна.\n\n"
            "Вы можете изменить режим OCR, языки, промпты и другие параметры.",
            parent=self.root
        )

    def _menu_start_processing(self) -> None:
        """Обработчик запуска обработки."""
        self.main_view._on_start_processing_click()

    def _menu_stop_processing(self) -> None:
        """Обработчик остановки обработки."""
        if self.presenter.get_processing_state().is_running:
            if messagebox.askyesno(
                "Остановка обработки",
                "Вы действительно хотите остановить обработку?",
                parent=self.root
            ):
                self.presenter.cancel_processing()

    def _menu_test_connection(self) -> None:
        """Обработчик тестирования соединения."""
        self.status_bar.start_busy_animation("Тестирование соединения")

        def test_and_update():
            try:
                success = self.presenter.test_ocr_connection()

                if success:
                    self.status_bar.set_status("Соединение с OCR сервисами работает", "success")
                    messagebox.showinfo("Тест соединения", "✅ Все OCR сервисы доступны!", parent=self.root)
                else:
                    self.status_bar.set_status("Проблемы с OCR сервисами", "warning")
                    messagebox.showwarning("Тест соединения", "⚠️ Обнаружены проблемы с подключением к OCR сервисам", parent=self.root)
            except Exception as e:
                self.status_bar.set_status(f"Ошибка тестирования: {e}", "error")
                messagebox.showerror("Ошибка теста", f"❌ Ошибка при тестировании:\n{e}", parent=self.root)

        # Запускаем тест в отдельном потоке
        import threading
        threading.Thread(target=test_and_update, daemon=True).start()

    def _menu_show_help(self) -> None:
        """Обработчик показа справки."""
        help_text = """OCR AI or Offline - Справка по использованию

🔍 ОСНОВНЫЕ ВОЗМОЖНОСТИ:
• Распознавание текста с изображений
• Два режима: Offline (Tesseract) и Online (ИИ)
• Поддержка множества языков и форматов
• Пакетная обработка файлов

📁 ДОБАВЛЕНИЕ ФАЙЛОВ:
• Перетащите файлы в область Drag & Drop
• Используйте кнопки "Добавить файлы" / "Добавить папку"
• Поддерживаемые форматы: PNG, JPG, JPEG, TIFF, BMP, GIF

⚙️ НАСТРОЙКИ:
• Offline режим: выбор языка и PSM режима Tesseract
• Online режим: выбор промпта и количества потоков
• Сортировка файлов по различным критериям

🚀 ОБРАБОТКА:
• Настройте параметры в правой панели
• Укажите выходной файл
• Нажмите "Начать обработку OCR"
• Следите за прогрессом в диалоге

⌨️ ГОРЯЧИЕ КЛАВИШИ:
• Ctrl+O - Добавить файлы
• Ctrl+Shift+O - Добавить папку
• F9 - Начать обработку
• Escape - Остановить обработку
• F5 - Обновить список файлов
• F1 - Эта справка

💡 СОВЕТЫ:
• Для лучшего качества используйте Online режим
• Для скорости и автономности - Offline режим
• Сортируйте файлы для правильного порядка обработки
• Сохраняйте настройки для повторного использования"""

        # Создаем окно справки
        help_window = tk.Toplevel(self.root)
        help_window.title("📖 Справка - OCR AI or Offline")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        help_window.transient(self.root)

        # Центрируем окно
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (help_window.winfo_width() // 2)
        y = (help_window.winfo_screenheight() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")

        # Текстовое поле с прокруткой
        frame = tk.Frame(help_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(
            frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#2c3e50",
            padx=10,
            pady=10
        )

        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Вставляем текст
        text_widget.insert(tk.END, help_text)
        text_widget.configure(state=tk.DISABLED)

        # Кнопка закрытия
        close_button = tk.Button(
            help_window,
            text="Закрыть",
            command=help_window.destroy,
            bg="#3498db",
            fg="white",
            padx=20,
            pady=5
        )
        close_button.pack(pady=10)

    def _menu_show_about(self) -> None:
        """Обработчик показа информации о программе."""
        about_text = """🔍 OCR AI or Offline

Версия: 1.0.0
Автор: OCR Team

Мощный инструмент для распознавания текста с изображений
с поддержкой как offline (Tesseract), так и online (ИИ) режимов.

Особенности:
• Два режима OCR обработки
• Поддержка множества языков
• Специализированные промпты для разных типов контента
• Пакетная обработка с прогресс-баром
• Гибкие настройки сортировки и форматирования

Технологии:
• Python + Tkinter для интерфейса
• Tesseract OCR для offline режима
• OpenAI/OpenRouter API для online режима
• MVP архитектура для maintainability

© 2024 OCR AI or Offline Team"""

        messagebox.showinfo("О программе", about_text, parent=self.root)

    # ========================
    # Обработчики событий окна
    # ========================

    def _on_window_configure(self, event) -> None:
        """
        Обработчик изменения размера окна.

        :param event: Событие изменения размера
        """
        # Обновляем размер окна в настройках только для главного окна
        if event.widget == self.root:
            width = self.root.winfo_width()
            height = self.root.winfo_height()

            # Обновляем настройки
            self.presenter.on_window_resize(width, height)

    def _on_closing(self) -> None:
        """Обработчик закрытия приложения."""
        # Проверяем, идет ли обработка
        if self.presenter.get_processing_state().is_running:
            result = messagebox.askyesnocancel(
                "Выход из программы",
                "Обработка OCR еще выполняется.\n\n"
                "Да - Остановить обработку и выйти\n"
                "Нет - Продолжить работу\n"
                "Отмена - Отменить выход",
                parent=self.root
            )

            if result is True:  # Да - остановить и выйти
                self.presenter.cancel_processing()
            elif result is False:  # Нет - продолжить работу
                return
            else:  # None - отмена
                return

        # Сохраняем настройки перед выходом
        try:
            self.presenter.on_application_exit()
        except Exception as e:
            self.logger.error(f"Ошибка при завершении приложения: {e}")

        # Закрываем приложение
        self.root.quit()
        self.root.destroy()

    # ========================
    # Публичные методы
    # ========================

    def run(self) -> None:
        """Запускает главный цикл приложения."""
        try:
            self.logger.info("Запуск главного цикла приложения")
            self.status_bar.set_status("Приложение готово к работе", "success")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Критическая ошибка в главном цикле: {e}")
            messagebox.showerror(
                "Критическая ошибка",
                f"Произошла критическая ошибка:\n{e}\n\nПриложение будет закрыто.",
                parent=self.root
            )
        finally:
            self.logger.info("Главный цикл приложения завершен")

    def get_root(self) -> tk.Tk:
        """
        Возвращает корневой виджет.

        :return: Корневой виджет Tk
        """
        return self.root

    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """
        Показывает сообщение пользователю.

        :param title: Заголовок сообщения
        :param message: Текст сообщения
        :param message_type: Тип сообщения ('info', 'warning', 'error')
        """
        if message_type == "info":
            messagebox.showinfo(title, message, parent=self.root)
        elif message_type == "warning":
            messagebox.showwarning(title, message, parent=self.root)
        elif message_type == "error":
            messagebox.showerror(title, message, parent=self.root)

        # Обновляем статусную строку
        self.status_bar.set_status(message, message_type)

    def set_busy(self, is_busy: bool, message: str = "Обработка") -> None:
        """
        Устанавливает состояние загрузки.

        :param is_busy: True для показа загрузки
        :param message: Сообщение для отображения
        """
        if is_busy:
            self.status_bar.start_busy_animation(message)
        else:
            self.status_bar.stop_busy_animation()

    def update_title(self, subtitle: str = "") -> None:
        """
        Обновляет заголовок окна.

        :param subtitle: Дополнительный текст для заголовка
        """
        base_title = "🔍 OCR AI or Offline - Распознавание текста"
        if subtitle:
            self.root.title(f"{base_title} - {subtitle}")
        else:
            self.root.title(base_title)
