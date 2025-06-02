"""
Представление панели настроек OCR.
Содержит все настройки для offline и online режимов обработки.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import Optional, Dict, Any

# Импорт для типов
try:
    from ..presenters.main_presenter import MainPresenter
    from ..models.settings_model import SettingsModel
except ImportError:
    MainPresenter = None
    SettingsModel = None


class SettingsView(tk.Frame):
    """
    Представление панели настроек OCR.
    Позволяет настраивать параметры обработки для offline и online режимов.
    """

    def __init__(self, parent: tk.Widget):
        """
        Инициализация представления настроек.

        :param parent: Родительский виджет
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Presenter будет установлен позже
        self.presenter: Optional[MainPresenter] = None

        # Переменные для виджетов
        self.mode_var = tk.StringVar(value="offline")
        self.sort_var = tk.StringVar(value="natural")
        self.output_file_var = tk.StringVar(value="result.txt")

        # Offline настройки
        self.language_var = tk.StringVar(value="rus")
        self.psm_var = tk.IntVar(value=3)

        # Online настройки
        self.prompt_var = tk.StringVar(value="classic_ocr")
        self.threads_var = tk.IntVar(value=5)

        # Дополнительные настройки
        self.metadata_var = tk.BooleanVar(value=True)

        # Виджеты
        self.mode_frame: Optional[tk.LabelFrame] = None
        self.offline_frame: Optional[tk.LabelFrame] = None
        self.online_frame: Optional[tk.LabelFrame] = None
        self.output_frame: Optional[tk.LabelFrame] = None
        self.sort_frame: Optional[tk.LabelFrame] = None

        # Создаем GUI
        self._create_gui()
        self._setup_bindings()

    def set_presenter(self, presenter) -> None:
        """
        Устанавливает presenter для взаимодействия.

        :param presenter: Экземпляр MainPresenter
        """
        self.presenter = presenter
        self.update_from_model()

    def _create_gui(self) -> None:
        """Создает интерфейс панели настроек."""
        # Создаем прокручиваемую область
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Размещаем компоненты
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Создаем разделы настроек
        self._create_mode_section(scrollable_frame)
        self._create_sort_section(scrollable_frame)
        self._create_offline_section(scrollable_frame)
        self._create_online_section(scrollable_frame)
        self._create_output_section(scrollable_frame)
        self._create_additional_section(scrollable_frame)

        # Привязываем прокрутку колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def _create_mode_section(self, parent: tk.Widget) -> None:
        """
        Создает секцию выбора режима OCR.

        :param parent: Родительский виджет
        """
        self.mode_frame = tk.LabelFrame(parent, text="🔧 Режим OCR", padx=10, pady=10)
        self.mode_frame.pack(fill=tk.X, padx=5, pady=5)

        # Описание режимов
        desc_label = tk.Label(
            self.mode_frame,
            text="Выберите способ распознавания текста:",
            font=("Arial", 9)
        )
        desc_label.pack(anchor=tk.W, pady=(0, 10))

        # Offline режим
        offline_radio = tk.Radiobutton(
            self.mode_frame,
            text="📴 Offline (Tesseract OCR)",
            variable=self.mode_var,
            value="offline",
            font=("Arial", 10, "bold"),
            command=self._on_mode_change
        )
        offline_radio.pack(anchor=tk.W, pady=2)

        offline_desc = tk.Label(
            self.mode_frame,
            text="• Быстрая обработка без интернета\n• Поддержка множества языков\n• Базовое качество распознавания",
            font=("Arial", 8),
            fg="#555555",
            justify=tk.LEFT
        )
        offline_desc.pack(anchor=tk.W, padx=20, pady=(0, 10))

        # Online режим
        online_radio = tk.Radiobutton(
            self.mode_frame,
            text="🌐 Online (ИИ модели)",
            variable=self.mode_var,
            value="online",
            font=("Arial", 10, "bold"),
            command=self._on_mode_change
        )
        online_radio.pack(anchor=tk.W, pady=2)

        online_desc = tk.Label(
            self.mode_frame,
            text="• Высокое качество распознавания\n• Понимание контекста и структуры\n• Требует подключение к интернету",
            font=("Arial", 8),
            fg="#555555",
            justify=tk.LEFT
        )
        online_desc.pack(anchor=tk.W, padx=20)

    def _create_sort_section(self, parent: tk.Widget) -> None:
        """
        Создает секцию настроек сортировки.

        :param parent: Родительский виджет
        """
        self.sort_frame = tk.LabelFrame(parent, text="🔢 Сортировка файлов", padx=10, pady=10)
        self.sort_frame.pack(fill=tk.X, padx=5, pady=5)

        sort_label = tk.Label(
            self.sort_frame,
            text="Порядок обработки файлов:",
            font=("Arial", 9)
        )
        sort_label.pack(anchor=tk.W, pady=(0, 5))

        # Combobox для выбора метода сортировки
        self.sort_combo = ttk.Combobox(
            self.sort_frame,
            textvariable=self.sort_var,
            state="readonly",
            width=30
        )
        self.sort_combo.pack(fill=tk.X, pady=5)

    def _create_offline_section(self, parent: tk.Widget) -> None:
        """
        Создает секцию настроек offline OCR.

        :param parent: Родительский виджет
        """
        self.offline_frame = tk.LabelFrame(parent, text="📴 Настройки Offline OCR", padx=10, pady=10)
        self.offline_frame.pack(fill=tk.X, padx=5, pady=5)

        # Выбор языка
        lang_frame = tk.Frame(self.offline_frame)
        lang_frame.pack(fill=tk.X, pady=5)

        tk.Label(lang_frame, text="Язык:", font=("Arial", 9)).pack(side=tk.LEFT)

        self.language_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            state="readonly",
            width=15
        )
        self.language_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # PSM режим
        psm_frame = tk.Frame(self.offline_frame)
        psm_frame.pack(fill=tk.X, pady=5)

        tk.Label(psm_frame, text="PSM режим:", font=("Arial", 9)).pack(side=tk.LEFT)

        self.psm_combo = ttk.Combobox(
            psm_frame,
            textvariable=self.psm_var,
            state="readonly",
            width=15
        )
        self.psm_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Информация о PSM
        psm_info = tk.Label(
            self.offline_frame,
            text="PSM (Page Segmentation Mode) - алгоритм анализа структуры страницы",
            font=("Arial", 8),
            fg="#777777",
            wraplength=250
        )
        psm_info.pack(anchor=tk.W, pady=(5, 0))

    def _create_online_section(self, parent: tk.Widget) -> None:
        """
        Создает секцию настроек online OCR.

        :param parent: Родительский виджет
        """
        self.online_frame = tk.LabelFrame(parent, text="🌐 Настройки Online OCR", padx=10, pady=10)
        self.online_frame.pack(fill=tk.X, padx=5, pady=5)

        # Выбор промпта
        prompt_frame = tk.Frame(self.online_frame)
        prompt_frame.pack(fill=tk.X, pady=5)

        tk.Label(prompt_frame, text="Тип OCR:", font=("Arial", 9)).pack(side=tk.LEFT)

        self.prompt_combo = ttk.Combobox(
            prompt_frame,
            textvariable=self.prompt_var,
            state="readonly",
            width=15
        )
        self.prompt_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Количество потоков
        threads_frame = tk.Frame(self.online_frame)
        threads_frame.pack(fill=tk.X, pady=5)

        tk.Label(threads_frame, text="Потоков:", font=("Arial", 9)).pack(side=tk.LEFT)

        self.threads_spinbox = tk.Spinbox(
            threads_frame,
            from_=1,
            to=20,
            textvariable=self.threads_var,
            width=10
        )
        self.threads_spinbox.pack(side=tk.RIGHT, padx=(10, 0))

        # Информация о потоках
        threads_info = tk.Label(
            self.online_frame,
            text="Больше потоков = быстрее обработка, но больше нагрузка на API",
            font=("Arial", 8),
            fg="#777777",
            wraplength=250
        )
        threads_info.pack(anchor=tk.W, pady=(5, 0))

        # Кнопка тестирования соединения
        test_button = tk.Button(
            self.online_frame,
            text="🔗 Тест соединения",
            command=self._on_test_connection,
            bg="#3498db",
            fg="white",
            pady=3
        )
        test_button.pack(fill=tk.X, pady=(10, 0))

    def _create_output_section(self, parent: tk.Widget) -> None:
        """
        Создает секцию настроек выходного файла.

        :param parent: Родительский виджет
        """
        self.output_frame = tk.LabelFrame(parent, text="💾 Выходной файл", padx=10, pady=10)
        self.output_frame.pack(fill=tk.X, padx=5, pady=5)

        # Поле для пути к файлу
        file_frame = tk.Frame(self.output_frame)
        file_frame.pack(fill=tk.X, pady=5)

        self.output_entry = tk.Entry(
            file_frame,
            textvariable=self.output_file_var,
            font=("Arial", 9)
        )
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_button = tk.Button(
            file_frame,
            text="📁",
            command=self._on_browse_output_file,
            width=3
        )
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Быстрые кнопки для типичных имен
        quick_frame = tk.Frame(self.output_frame)
        quick_frame.pack(fill=tk.X, pady=(5, 0))

        quick_label = tk.Label(quick_frame, text="Быстрый выбор:", font=("Arial", 8))
        quick_label.pack(side=tk.LEFT)

        quick_names = ["result.txt", "ocr_output.txt", "extracted_text.txt"]
        for name in quick_names:
            btn = tk.Button(
                quick_frame,
                text=name,
                command=lambda n=name: self.output_file_var.set(n),
                font=("Arial", 7),
                pady=1
            )
            btn.pack(side=tk.RIGHT, padx=1)

    def _create_additional_section(self, parent: tk.Widget) -> None:
        """
        Создает секцию дополнительных настроек.

        :param parent: Родительский виджет
        """
        additional_frame = tk.LabelFrame(parent, text="➕ Дополнительно", padx=10, pady=10)
        additional_frame.pack(fill=tk.X, padx=5, pady=5)

        # Включение метаданных
        metadata_check = tk.Checkbutton(
            additional_frame,
            text="Включать метаданные в результат",
            variable=self.metadata_var,
            command=self._on_metadata_change
        )
        metadata_check.pack(anchor=tk.W, pady=2)

        metadata_desc = tk.Label(
            additional_frame,
            text="Добавляет информацию о файлах, времени обработки и статистику",
            font=("Arial", 8),
            fg="#777777",
            wraplength=250
        )
        metadata_desc.pack(anchor=tk.W, padx=20, pady=(0, 10))

        # Кнопки управления настройками
        buttons_frame = tk.Frame(additional_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        save_button = tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=self._on_save_settings,
            bg="#27ae60",
            fg="white",
            pady=3
        )
        save_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        reset_button = tk.Button(
            buttons_frame,
            text="🔄 Сброс",
            command=self._on_reset_settings,
            bg="#e74c3c",
            fg="white",
            pady=3
        )
        reset_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

    def _setup_bindings(self) -> None:
        """Настраивает обработчики событий."""
        # Обработчики изменений в виджетах
        self.sort_combo.bind("<<ComboboxSelected>>", self._on_sort_change)
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        self.psm_combo.bind("<<ComboboxSelected>>", self._on_psm_change)
        self.prompt_combo.bind("<<ComboboxSelected>>", self._on_prompt_change)
        self.threads_spinbox.bind("<FocusOut>", self._on_threads_change)
        self.output_entry.bind("<FocusOut>", self._on_output_file_change)

    def update_from_model(self) -> None:
        """Обновляет виджеты на основе данных из модели."""
        if not self.presenter:
            return

        settings = self.presenter.get_settings()

        # Обновляем основные настройки
        self.mode_var.set(settings.ocr_mode)
        self.sort_var.set(settings.sort_method)
        self.output_file_var.set(settings.output_file)
        self.metadata_var.set(settings.include_metadata)

        # Обновляем offline настройки
        self.language_var.set(settings.offline_settings.language)
        self.psm_var.set(settings.offline_settings.psm_mode)

        # Обновляем online настройки
        self.prompt_var.set(settings.online_settings.prompt_name)
        self.threads_var.set(settings.online_settings.max_threads)

        # Обновляем списки доступных опций
        self._update_combo_options()

        # Обновляем видимость секций
        self._update_sections_visibility()

    def _update_combo_options(self) -> None:
        """Обновляет опции в выпадающих списках."""
        if not self.presenter:
            return

        settings = self.presenter.get_settings()

        # Обновляем методы сортировки
        sort_options = [method['name'] for method in settings.available_sort_methods]
        sort_values = [method['key'] for method in settings.available_sort_methods]

        self.sort_combo['values'] = sort_options
        # Устанавливаем отображаемое значение
        current_method = settings.sort_method
        for i, key in enumerate(sort_values):
            if key == current_method:
                self.sort_combo.current(i)
                break

        # Обновляем языки
        languages = self.presenter.get_available_languages()
        self.language_combo['values'] = languages

        # Обновляем PSM режимы
        psm_options = [f"{mode['name']}" for mode in settings.available_psm_modes]
        self.psm_combo['values'] = psm_options

        # Устанавливаем текущий PSM
        current_psm = settings.offline_settings.psm_mode
        for i, mode in enumerate(settings.available_psm_modes):
            if mode['value'] == current_psm:
                self.psm_combo.current(i)
                break

        # Обновляем промпты
        prompts = self.presenter.get_available_prompts()
        self.prompt_combo['values'] = prompts

    def _update_sections_visibility(self) -> None:
        """Обновляет видимость секций в зависимости от режима."""
        mode = self.mode_var.get()

        if mode == "offline":
            self.offline_frame.pack(fill=tk.X, padx=5, pady=5)
            self.online_frame.pack_forget()
        else:
            self.online_frame.pack(fill=tk.X, padx=5, pady=5)
            self.offline_frame.pack_forget()

    # ========================
    # Обработчики событий
    # ========================

    def _on_mode_change(self) -> None:
        """Обработчик изменения режима OCR."""
        if self.presenter:
            mode = self.mode_var.get()
            self.presenter.set_ocr_mode(mode)
            self._update_sections_visibility()

    def _on_sort_change(self, event=None) -> None:
        """Обработчик изменения метода сортировки."""
        if self.presenter:
            settings = self.presenter.get_settings()
            selected_index = self.sort_combo.current()

            if 0 <= selected_index < len(settings.available_sort_methods):
                method_key = settings.available_sort_methods[selected_index]['key']
                self.presenter.set_sort_method(method_key)

    def _on_language_change(self, event=None) -> None:
        """Обработчик изменения языка OCR."""
        if self.presenter:
            language = self.language_var.get()
            self.presenter.update_offline_settings(language=language)

    def _on_psm_change(self, event=None) -> None:
        """Обработчик изменения PSM режима."""
        if self.presenter:
            settings = self.presenter.get_settings()
            selected_index = self.psm_combo.current()

            if 0 <= selected_index < len(settings.available_psm_modes):
                psm_value = settings.available_psm_modes[selected_index]['value']
                self.presenter.update_offline_settings(psm_mode=psm_value)

    def _on_prompt_change(self, event=None) -> None:
        """Обработчик изменения промпта."""
        if self.presenter:
            prompt = self.prompt_var.get()
            self.presenter.update_online_settings(prompt_name=prompt)

    def _on_threads_change(self, event=None) -> None:
        """Обработчик изменения количества потоков."""
        if self.presenter:
            try:
                threads = self.threads_var.get()
                if 1 <= threads <= 20:
                    self.presenter.update_online_settings(max_threads=threads)
            except tk.TclError:
                pass  # Игнорируем некорректные значения

    def _on_output_file_change(self, event=None) -> None:
        """Обработчик изменения выходного файла."""
        if self.presenter:
            output_file = self.output_file_var.get().strip()
            if output_file:
                self.presenter.set_output_file(output_file)

    def _on_metadata_change(self) -> None:
        """Обработчик изменения настройки метаданных."""
        if self.presenter:
            include_metadata = self.metadata_var.get()
            settings = self.presenter.get_settings()
            settings.include_metadata = include_metadata

    def _on_browse_output_file(self) -> None:
        """Обработчик выбора выходного файла."""
        filename = filedialog.asksaveasfilename(
            title="Выберите файл для сохранения результатов",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )

        if filename:
            self.output_file_var.set(filename)
            if self.presenter:
                self.presenter.set_output_file(filename)

    def _on_test_connection(self) -> None:
        """Обработчик тестирования соединения с OCR сервисом."""
        if not self.presenter:
            return

        # Показываем индикатор загрузки
        test_button = None
        for child in self.online_frame.winfo_children():
            if isinstance(child, tk.Button) and "Тест" in child.cget("text"):
                test_button = child
                break

        if test_button:
            original_text = test_button.cget("text")
            test_button.configure(text="⏳ Тестирование...", state=tk.DISABLED)
            self.update()

        try:
            # Выполняем тест
            success = self.presenter.test_ocr_connection()

            if success:
                messagebox.showinfo("Тест соединения", "✅ Соединение с OCR сервисом работает!")
            else:
                messagebox.showwarning("Тест соединения", "⚠️ Проблемы с подключением к OCR сервису")

        except Exception as e:
            messagebox.showerror("Ошибка теста", f"❌ Ошибка при тестировании:\n{e}")

        finally:
            # Восстанавливаем кнопку
            if test_button:
                test_button.configure(text=original_text, state=tk.NORMAL)

    def _on_save_settings(self) -> None:
        """Обработчик сохранения настроек."""
        if self.presenter:
            settings = self.presenter.get_settings()
            if settings.save_settings():
                messagebox.showinfo("Сохранение", "✅ Настройки успешно сохранены!")
            else:
                messagebox.showerror("Ошибка", "❌ Не удалось сохранить настройки")

    def _on_reset_settings(self) -> None:
        """Обработчик сброса настроек."""
        if messagebox.askyesno("Подтверждение", "Сбросить все настройки к значениям по умолчанию?"):
            if self.presenter:
                settings = self.presenter.get_settings()
                settings.reset_to_defaults()
                self.update_from_model()
                messagebox.showinfo("Сброс", "✅ Настройки сброшены к значениям по умолчанию!")
