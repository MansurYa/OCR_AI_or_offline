"""
Кастомные tkinter виджеты для улучшения пользовательского интерфейса.
Содержит переиспользуемые компоненты с улучшенным дизайном.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional, Callable, Any


class AnimatedProgressBar(tk.Frame):
    """
    Анимированный прогресс-бар с эффектами и дополнительной информацией.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        """
        Инициализация анимированного прогресс-бара.

        :param parent: Родительский виджет
        :param kwargs: Дополнительные параметры
        """
        super().__init__(parent, **kwargs)

        # Переменные
        self.progress_var = tk.DoubleVar()
        self.max_value = 100
        self.current_value = 0
        self.is_animating = False
        self.animation_speed = 50  # миллисекунды

        # Цвета
        self.colors = {
            'bg': '#ecf0f1',
            'fill': '#3498db',
            'text': '#2c3e50',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c'
        }

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создает виджеты прогресс-бара."""
        # Основной прогресс-бар
        self.progressbar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=self.max_value,
            length=300,
            style="Custom.Horizontal.TProgressbar"
        )
        self.progressbar.pack(fill=tk.X, pady=(0, 5))

        # Текстовая информация
        self.info_frame = tk.Frame(self)
        self.info_frame.pack(fill=tk.X)

        # Процент выполнения
        self.percent_label = tk.Label(
            self.info_frame,
            text="0%",
            font=("Arial", 9, "bold"),
            fg=self.colors['text']
        )
        self.percent_label.pack(side=tk.LEFT)

        # Дополнительная информация
        self.info_label = tk.Label(
            self.info_frame,
            text="",
            font=("Arial", 8),
            fg=self.colors['text']
        )
        self.info_label.pack(side=tk.RIGHT)

    def set_progress(self, value: float, info_text: str = "") -> None:
        """
        Устанавливает прогресс с анимацией.

        :param value: Значение прогресса (0-100)
        :param info_text: Дополнительная информация
        """
        target_value = max(0, min(value, self.max_value))

        if not self.is_animating:
            self._animate_to_value(target_value)

        # Обновляем текст
        self.percent_label.configure(text=f"{target_value:.1f}%")
        self.info_label.configure(text=info_text)

        # Изменяем цвет в зависимости от прогресса
        if target_value >= 100:
            color = self.colors['success']
        elif target_value >= 75:
            color = self.colors['fill']
        elif target_value >= 50:
            color = self.colors['warning']
        else:
            color = self.colors['fill']

        self.percent_label.configure(fg=color)

    def _animate_to_value(self, target_value: float) -> None:
        """
        Анимирует прогресс до целевого значения.

        :param target_value: Целевое значение
        """
        self.is_animating = True

        def animate():
            start_value = self.current_value
            steps = 20
            step_size = (target_value - start_value) / steps

            for i in range(steps + 1):
                new_value = start_value + (step_size * i)
                self.after(self.animation_speed * i, lambda v=new_value: self._update_value(v))

            self.after(self.animation_speed * (steps + 1), lambda: setattr(self, 'is_animating', False))

        threading.Thread(target=animate, daemon=True).start()

    def _update_value(self, value: float) -> None:
        """
        Обновляет значение прогресс-бара.

        :param value: Новое значение
        """
        self.current_value = value
        self.progress_var.set(value)

    def set_style(self, style_name: str) -> None:
        """
        Устанавливает стиль прогресс-бара.

        :param style_name: Название стиля ('normal', 'success', 'warning', 'error')
        """
        style_colors = {
            'normal': self.colors['fill'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        color = style_colors.get(style_name, self.colors['fill'])
        self.percent_label.configure(fg=color)


class StatusBar(tk.Frame):
    """
    Улучшенная статусная строка с поддержкой иконок и анимации.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        """
        Инициализация статусной строки.

        :param parent: Родительский виджет
        :param kwargs: Дополнительные параметры
        """
        super().__init__(parent, relief=tk.SUNKEN, bd=1, **kwargs)

        # Переменные
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")

        # Анимация статуса
        self.animation_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.animation_index = 0
        self.is_busy = False
        self.animation_job = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создает виджеты статусной строки."""
        # Левая часть - основной статус
        left_frame = tk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = tk.Label(
            left_frame,
            textvariable=self.status_var,
            anchor=tk.W,
            padx=5,
            pady=2,
            font=("Arial", 9)
        )
        self.status_label.pack(fill=tk.X)

        # Правая часть - дополнительная информация
        right_frame = tk.Frame(self)
        right_frame.pack(side=tk.RIGHT)

        self.info_label = tk.Label(
            right_frame,
            text="",
            anchor=tk.E,
            padx=5,
            pady=2,
            font=("Arial", 8),
            fg="#7f8c8d"
        )
        self.info_label.pack()

    def set_status(self, message: str, status_type: str = "normal") -> None:
        """
        Устанавливает статус с типом.

        :param message: Сообщение статуса
        :param status_type: Тип статуса ('normal', 'info', 'warning', 'error', 'success')
        """
        # Останавливаем анимацию
        self.stop_busy_animation()

        # Цвета для разных типов статуса
        colors = {
            'normal': '#2c3e50',
            'info': '#3498db',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'success': '#27ae60'
        }

        # Иконки для разных типов
        icons = {
            'normal': '',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }

        color = colors.get(status_type, colors['normal'])
        icon = icons.get(status_type, '')

        full_message = f"{icon} {message}" if icon else message

        self.status_var.set(full_message)
        self.status_label.configure(fg=color)

    def set_info(self, info_text: str) -> None:
        """
        Устанавливает дополнительную информацию.

        :param info_text: Информационный текст
        """
        self.info_label.configure(text=info_text)

    def start_busy_animation(self, message: str = "Обработка") -> None:
        """
        Запускает анимацию загрузки.

        :param message: Сообщение для отображения
        """
        self.is_busy = True
        self.base_message = message
        self._animate_busy()

    def stop_busy_animation(self) -> None:
        """Останавливает анимацию загрузки."""
        self.is_busy = False
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def _animate_busy(self) -> None:
        """Анимирует индикатор загрузки."""
        if not self.is_busy:
            return

        # Обновляем символ анимации
        char = self.animation_chars[self.animation_index]
        self.status_var.set(f"{char} {self.base_message}...")

        # Переходим к следующему символу
        self.animation_index = (self.animation_index + 1) % len(self.animation_chars)

        # Планируем следующее обновление
        self.animation_job = self.after(100, self._animate_busy)


class ToolTip:
    """
    Всплывающая подсказка для виджетов.
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        """
        Инициализация всплывающей подсказки.

        :param widget: Виджет для которого создается подсказка
        :param text: Текст подсказки
        :param delay: Задержка перед показом в миллисекундах
        """
        self.widget = widget
        self.text = text
        self.delay = delay

        self.tooltip_window = None
        self.show_job = None
        self.hide_job = None

        # Привязываем события
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Motion>", self._on_motion)

    def _on_enter(self, event) -> None:
        """Обработчик входа мыши в виджет."""
        self._schedule_show()

    def _on_leave(self, event) -> None:
        """Обработчик выхода мыши из виджета."""
        self._cancel_show()
        self._hide_tooltip()

    def _on_motion(self, event) -> None:
        """Обработчик движения мыши."""
        # Обновляем позицию если подсказка показана
        if self.tooltip_window:
            self._update_position(event)

    def _schedule_show(self) -> None:
        """Планирует показ подсказки с задержкой."""
        self._cancel_show()
        self.show_job = self.widget.after(self.delay, self._show_tooltip)

    def _cancel_show(self) -> None:
        """Отменяет запланированный показ подсказки."""
        if self.show_job:
            self.widget.after_cancel(self.show_job)
            self.show_job = None

    def _show_tooltip(self) -> None:
        """Показывает всплывающую подсказку."""
        if self.tooltip_window:
            return

        # Создаем окно подсказки
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_attributes("-topmost", True)

        # Создаем содержимое
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffcc",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            wraplength=250,
            justify=tk.LEFT,
            padx=5,
            pady=3
        )
        label.pack()

        # Позиционируем подсказку
        self._position_tooltip()

    def _position_tooltip(self) -> None:
        """Позиционирует всплывающую подсказку."""
        if not self.tooltip_window:
            return

        # Получаем позицию виджета
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Обновляем геометрию для получения размеров
        self.tooltip_window.update_idletasks()

        # Проверяем, не выходит ли подсказка за границы экрана
        screen_width = self.tooltip_window.winfo_screenwidth()
        screen_height = self.tooltip_window.winfo_screenheight()

        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()

        # Корректируем позицию если нужно
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 10

        if y + tooltip_height > screen_height:
            y = self.widget.winfo_rooty() - tooltip_height - 5

        self.tooltip_window.geometry(f"+{x}+{y}")

    def _update_position(self, event) -> None:
        """
        Обновляет позицию подсказки при движении мыши.

        :param event: Событие движения мыши
        """
        if self.tooltip_window:
            x = event.x_root + 10
            y = event.y_root + 10
            self.tooltip_window.geometry(f"+{x}+{y}")

    def _hide_tooltip(self) -> None:
        """Скрывает всплывающую подсказку."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, new_text: str) -> None:
        """
        Обновляет текст подсказки.

        :param new_text: Новый текст подсказки
        """
        self.text = new_text

        # Если подсказка сейчас показана, обновляем ее
        if self.tooltip_window:
            self._hide_tooltip()
            self._show_tooltip()


class RoundedButton(tk.Canvas):
    """
    Кнопка с закругленными углами и эффектами наведения.
    """

    def __init__(self, parent: tk.Widget, text: str = "", command: Optional[Callable] = None,
                 width: int = 100, height: int = 30, radius: int = 10, **kwargs):
        """
        Инициализация закругленной кнопки.

        :param parent: Родительский виджет
        :param text: Текст кнопки
        :param command: Команда при нажатии
        :param width: Ширина кнопки
        :param height: Высота кнопки
        :param radius: Радиус закругления
        :param kwargs: Дополнительные параметры
        """
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)

        self.text = text
        self.command = command
        self.radius = radius
        self.is_pressed = False
        self.is_hovered = False

        # Цвета
        self.colors = {
            'normal_bg': '#3498db',
            'normal_fg': '#ffffff',
            'hover_bg': '#2980b9',
            'hover_fg': '#ffffff',
            'pressed_bg': '#21618c',
            'pressed_fg': '#ffffff',
            'disabled_bg': '#bdc3c7',
            'disabled_fg': '#7f8c8d'
        }

        # Обновляем цвета из kwargs
        for key, value in kwargs.items():
            if key in self.colors:
                self.colors[key] = value

        self._draw_button()
        self._bind_events()

    def _draw_button(self) -> None:
        """Рисует кнопку на canvas."""
        self.delete("all")

        # Определяем цвета в зависимости от состояния
        if str(self.cget('state')) == 'disabled':
            bg_color = self.colors['disabled_bg']
            fg_color = self.colors['disabled_fg']
        elif self.is_pressed:
            bg_color = self.colors['pressed_bg']
            fg_color = self.colors['pressed_fg']
        elif self.is_hovered:
            bg_color = self.colors['hover_bg']
            fg_color = self.colors['hover_fg']
        else:
            bg_color = self.colors['normal_bg']
            fg_color = self.colors['normal_fg']

        # Получаем размеры
        width = self.winfo_width() or self.cget('width')
        height = self.winfo_height() or self.cget('height')

        # Рисуем закругленный прямоугольник
        self._draw_rounded_rectangle(2, 2, width-2, height-2, self.radius, bg_color)

        # Добавляем текст
        self.create_text(
            width//2, height//2,
            text=self.text,
            fill=fg_color,
            font=("Arial", 10, "bold"),
            anchor=tk.CENTER
        )

    def _draw_rounded_rectangle(self, x1: int, y1: int, x2: int, y2: int,
                               radius: int, fill_color: str) -> None:
        """
        Рисует закругленный прямоугольник.

        :param x1, y1, x2, y2: Координаты прямоугольника
        :param radius: Радиус закругления
        :param fill_color: Цвет заливки
        """
        # Создаем точки для закругленного прямоугольника
        points = []

        # Верхняя сторона
        points.extend([x1 + radius, y1])
        points.extend([x2 - radius, y1])

        # Верхний правый угол
        for i in range(0, 91, 10):
            angle = i * 3.14159 / 180
            px = x2 - radius + radius * (1 - tk.cos(angle))
            py = y1 + radius - radius * tk.sin(angle)
            points.extend([px, py])

        # Правая сторона
        points.extend([x2, y1 + radius])
        points.extend([x2, y2 - radius])

        # Нижний правый угол
        for i in range(0, 91, 10):
            angle = i * 3.14159 / 180
            px = x2 - radius + radius * tk.sin(angle)
            py = y2 - radius + radius * (1 - tk.cos(angle))
            points.extend([px, py])

        # Нижняя сторона
        points.extend([x2 - radius, y2])
        points.extend([x1 + radius, y2])

        # Нижний левый угол
        for i in range(0, 91, 10):
            angle = i * 3.14159 / 180
            px = x1 + radius - radius * (1 - tk.cos(angle))
            py = y2 - radius + radius * tk.sin(angle)
            points.extend([px, py])

        # Левая сторона
        points.extend([x1, y2 - radius])
        points.extend([x1, y1 + radius])

        # Верхний левый угол
        for i in range(0, 91, 10):
            angle = i * 3.14159 / 180
            px = x1 + radius - radius * tk.sin(angle)
            py = y1 + radius - radius * (1 - tk.cos(angle))
            points.extend([px, py])

        # Рисуем многоугольник
        if points:
            try:
                self.create_polygon(points, fill=fill_color, outline="", smooth=True)
            except:
                # Fallback к обычному прямоугольнику
                self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")

    def _bind_events(self) -> None:
        """Привязывает события мыши."""
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_press(self, event) -> None:
        """Обработчик нажатия кнопки."""
        if str(self.cget('state')) != 'disabled':
            self.is_pressed = True
            self._draw_button()

    def _on_release(self, event) -> None:
        """Обработчик отпускания кнопки."""
        if str(self.cget('state')) != 'disabled':
            self.is_pressed = False
            self._draw_button()

            # Выполняем команду если курсор все еще над кнопкой
            if self.is_hovered and self.command:
                self.command()

    def _on_enter(self, event) -> None:
        """Обработчик входа курсора."""
        if str(self.cget('state')) != 'disabled':
            self.is_hovered = True
            self._draw_button()

    def _on_leave(self, event) -> None:
        """Обработчик выхода курсора."""
        self.is_hovered = False
        self.is_pressed = False
        self._draw_button()

    def configure_text(self, text: str) -> None:
        """
        Обновляет текст кнопки.

        :param text: Новый текст
        """
        self.text = text
        self._draw_button()

    def configure_command(self, command: Optional[Callable]) -> None:
        """
        Обновляет команду кнопки.

        :param command: Новая команда
        """
        self.command = command


def add_tooltip(widget: tk.Widget, text: str, delay: int = 500) -> ToolTip:
    """
    Добавляет всплывающую подсказку к виджету.

    :param widget: Виджет для добавления подсказки
    :param text: Текст подсказки
    :param delay: Задержка перед показом
    :return: Объект ToolTip
    """
    return ToolTip(widget, text, delay)


def create_rounded_button(parent: tk.Widget, text: str, command: Optional[Callable] = None,
                         **kwargs) -> RoundedButton:
    """
    Создает закругленную кнопку.

    :param parent: Родительский виджет
    :param text: Текст кнопки
    :param command: Команда при нажатии
    :param kwargs: Дополнительные параметры
    :return: Объект RoundedButton
    """
    return RoundedButton(parent, text=text, command=command, **kwargs)
