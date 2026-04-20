"""CamForge CustomTkinter 组件模块

封装可复用的现代化 UI 组件：
- CardGroup: 圆角卡片容器
- EntryRow: 标签 + 输入框行
- SwitchRow: 标签 + 拨动开关行
- ComboRow: 标签 + 下拉菜单行
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional

from ui.ctk_constants import (
    UI_PADDING, CARD_PADDING, CORNER_RADIUS, SMALL_CORNER_RADIUS,
    COLORS_LIGHT, COLORS_DARK,
    FONT_SIZE_SECTION, FONT_SIZE_LABEL,
    ENTRY_STYLE, SWITCH_STYLE, OPTION_MENU_STYLE,
    OPTION_MENU_DROPDOWN_STYLE,
    create_ctk_font, get_colors,
)


class CardGroup(ctk.CTkFrame):
    """iOS 设置风格的圆角卡片容器

    将相关控件包裹在一个有细微背景色差的圆角卡片中。

    Attributes
    ----------
    title : str
        卡片标题（显示在卡片上方）
    """

    def __init__(self, parent, title: str = "", **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        title : str
            卡片标题（可选）
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        # 设置卡片默认样式
        default_style = {
            'corner_radius': CORNER_RADIUS,
            'fg_color': COLORS_LIGHT['card_bg'],
        }
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        self.title = title
        self._title_label = None
        self._parent = parent

    def pack_with_title(self, **kwargs):
        """打包卡片（包含标题）"""
        # 先创建并打包标题
        if self.title:
            self._title_label = ctk.CTkLabel(
                self._parent,
                text=self.title.upper(),
                font=create_ctk_font(size=FONT_SIZE_SECTION, weight="bold"),
                text_color=COLORS_LIGHT['text_secondary'],
                anchor='w',
            )
            title_kwargs = {
                'fill': 'x',
                'padx': UI_PADDING,
                'pady': (15, 2),
                'anchor': 'w',
            }
            self._title_label.pack(**title_kwargs)

        # 再打包卡片
        default_kwargs = {
            'fill': 'x',
            'padx': UI_PADDING,
            'pady': (0, 10),
        }
        default_kwargs.update(kwargs)
        super().pack(**default_kwargs)


class EntryRow(ctk.CTkFrame):
    """标签 + 输入框的行布局

    左侧显示标签，右侧显示输入框，类似 iOS 设置页的输入项。

    Attributes
    ----------
    entry : CTkEntry
        输入框控件
    label : CTkLabel
        标签控件
    """

    def __init__(self, parent, label_text: str, default_value: str = "",
                 width: int = 70, tooltip: str = None, **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        label_text : str
            标签文本
        default_value : str
            默认值
        width : int
            输入框宽度
        tooltip : str, optional
            悬浮提示文本
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        default_style = {'fg_color': 'transparent'}
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        # 标签（左侧）
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        self.label.pack(side='left', fill='x', expand=True)

        # 输入框（右侧）
        entry_style = ENTRY_STYLE.copy()
        entry_style['width'] = width
        self.entry = ctk.CTkEntry(self, **entry_style)
        self.entry.insert(0, default_value)
        self.entry.pack(side='right')

        # 悬浮提示
        self._tooltip = None
        if tooltip:
            self._create_tooltip(tooltip)

    def _create_tooltip(self, text: str):
        """创建悬浮提示"""
        # 绑定鼠标事件
        self.entry.bind('<Enter>', lambda e: self._show_tooltip(text))
        self.entry.bind('<Leave>', self._hide_tooltip)

    def _show_tooltip(self, text: str):
        """显示悬浮提示"""
        if self._tooltip:
            return
        x = self.entry.winfo_rootx() + 25
        y = self.entry.winfo_rooty() + 25
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self._tooltip, text=text, background="#ffffe0",
                         relief="solid", borderwidth=1, font=("Microsoft YaHei", 9))
        label.pack()

    def _hide_tooltip(self, event=None):
        """隐藏悬浮提示"""
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None

    def get(self) -> str:
        """获取输入框值"""
        return self.entry.get()

    def set(self, value: str):
        """设置输入框值"""
        self.entry.delete(0, 'end')
        self.entry.insert(0, str(value))

    def pack_in_card(self, **kwargs):
        """在卡片内打包"""
        default_kwargs = {'fill': 'x', 'padx': CARD_PADDING, 'pady': 6}
        default_kwargs.update(kwargs)
        self.pack(**default_kwargs)


class SwitchRow(ctk.CTkFrame):
    """标签 + 拨动开关的行布局

    左侧显示标签，右侧显示 Apple 风格拨动开关。

    Attributes
    ----------
    var : BooleanVar
        开关状态变量
    switch : CTkSwitch
        开关控件
    """

    def __init__(self, parent, label_text: str, default: bool = False,
                 command: Optional[Callable] = None, **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        label_text : str
            标签文本
        default : bool
            默认状态
        command : callable, optional
            状态改变回调
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        default_style = {'fg_color': 'transparent'}
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        # 状态变量
        self.var = tk.BooleanVar(value=default)

        # 标签（左侧）
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        self.label.pack(side='left', fill='x', expand=True)

        # 开关（右侧）
        switch_style = SWITCH_STYLE.copy()
        self.switch = ctk.CTkSwitch(
            self,
            text="",
            variable=self.var,
            command=command,
            **switch_style
        )
        self.switch.pack(side='right')

    def get(self) -> bool:
        """获取开关状态"""
        return self.var.get()

    def set(self, value: bool):
        """设置开关状态"""
        self.var.set(value)

    def pack_in_card(self, **kwargs):
        """在卡片内打包"""
        default_kwargs = {'fill': 'x', 'padx': CARD_PADDING, 'pady': 8}
        default_kwargs.update(kwargs)
        self.pack(**default_kwargs)


class ComboRow(ctk.CTkFrame):
    """标签 + 下拉菜单的行布局

    左侧显示标签，右侧显示下拉菜单。

    Attributes
    ----------
    combo : CTkOptionMenu
        下拉菜单控件
    """

    def __init__(self, parent, label_text: str, values: list,
                 default_index: int = 0, command: Optional[Callable] = None,
                 **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        label_text : str
            标签文本
        values : list
            下拉选项列表
        default_index : int
            默认选中索引
        command : callable, optional
            选择改变回调
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        default_style = {'fg_color': 'transparent'}
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        # 标签（左侧）
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        self.label.pack(side='left', fill='x', expand=True)

        # 下拉菜单（右侧）- 保持默认按钮样式，仅自定义下拉列表样式
        combo_style = OPTION_MENU_STYLE.copy()
        self.combo = ctk.CTkOptionMenu(
            self,
            values=values,
            command=command,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            dropdown_font=create_ctk_font(size=FONT_SIZE_LABEL),
            dropdown_fg_color=OPTION_MENU_DROPDOWN_STYLE['fg_color'],
            dropdown_hover_color=OPTION_MENU_DROPDOWN_STYLE['hover_color'],
            dropdown_text_color=OPTION_MENU_DROPDOWN_STYLE['text_color'],
            **combo_style
        )
        if values and 0 <= default_index < len(values):
            self.combo.set(values[default_index])
        self.combo.pack(side='right')

    def get(self) -> str:
        """获取当前选中值"""
        return self.combo.get()

    def set(self, value: str):
        """设置当前选中值"""
        self.combo.set(value)

    def current(self) -> int:
        """获取当前选中索引"""
        values = list(self.combo.cget('values'))
        current = self.combo.get()
        return values.index(current) if current in values else -1

    def set_index(self, index: int):
        """通过索引设置选中值"""
        values = list(self.combo.cget('values'))
        if 0 <= index < len(values):
            self.combo.set(values[index])

    def pack_in_card(self, **kwargs):
        """在卡片内打包"""
        default_kwargs = {'fill': 'x', 'padx': CARD_PADDING, 'pady': 6}
        default_kwargs.update(kwargs)
        self.pack(**default_kwargs)


class ButtonRow(ctk.CTkFrame):
    """按钮行布局

    水平排列多个按钮。

    Attributes
    ----------
    buttons : dict
        按钮名称 -> CTkButton 映射
    """

    def __init__(self, parent, **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        default_style = {'fg_color': 'transparent'}
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        self.buttons = {}

    def add_button(self, name: str, text: str, command: Optional[Callable] = None,
                   style: str = 'primary', **kwargs):
        """
        添加按钮

        Parameters
        ----------
        name : str
            按钮名称（用于后续引用）
        text : str
            按钮文本
        command : callable, optional
            点击回调
        style : str
            按钮样式 ('primary', 'success', 'warning', 'outline', 'secondary')
        **kwargs
            传递给 CTkButton 的其他参数
        """
        from ui.ctk_constants import get_button_style

        button_style = get_button_style(style)
        button_style.update(kwargs)
        button_style['text'] = text
        button_style['command'] = command

        btn = ctk.CTkButton(self, **button_style)
        btn.pack(side='left', padx=(0, 10))
        self.buttons[name] = btn

        return btn

    def get_button(self, name: str) -> Optional[ctk.CTkButton]:
        """获取按钮"""
        return self.buttons.get(name)


class StatusLabel(ctk.CTkFrame):
    """状态标签

    显示状态信息，支持不同颜色主题。

    Attributes
    ----------
    label : CTkLabel
        标签控件
    """

    def __init__(self, parent, text: str = "", style: str = 'default', **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        text : str
            初始文本
        style : str
            样式 ('default', 'success', 'warning', 'danger')
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        default_style = {'fg_color': 'transparent'}
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        # 获取颜色
        colors = get_colors()
        text_colors = {
            'default': colors['text_primary'],
            'success': colors['success'],
            'warning': colors['warning'],
            'danger': colors['danger'],
        }

        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            text_color=text_colors.get(style, colors['text_primary']),
            anchor='w',
        )
        self.label.pack(side='left')

    def set(self, text: str, style: str = 'default'):
        """设置文本和样式"""
        colors = get_colors()
        text_colors = {
            'default': colors['text_primary'],
            'success': colors['success'],
            'warning': colors['warning'],
            'danger': colors['danger'],
        }
        self.label.configure(text=text, text_color=text_colors.get(style, colors['text_primary']))

    def get(self) -> str:
        """获取文本"""
        return self.label.cget('text')


class ProgressBar(ctk.CTkFrame):
    """进度条

    显示进度信息。

    Attributes
    ----------
    progressbar : CTkProgressBar
        进度条控件
    label : CTkLabel
        进度文本标签
    """

    def __init__(self, parent, **kwargs):
        """
        Parameters
        ----------
        parent : widget
            父控件
        **kwargs
            传递给 CTkFrame 的其他参数
        """
        default_style = {'fg_color': 'transparent'}
        default_style.update(kwargs)

        super().__init__(parent, **default_style)

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.pack(side='left', fill='x', expand=True)

        self.label = ctk.CTkLabel(
            self,
            text="0%",
            font=create_ctk_font(size=FONT_SIZE_LABEL - 2),
            width=40,
        )
        self.label.pack(side='right', padx=(10, 0))

    def set(self, value: float):
        """设置进度 (0.0 - 1.0)"""
        self.progressbar.set(value)
        self.label.configure(text=f"{int(value * 100)}%")

    def get(self) -> float:
        """获取进度"""
        return self.progressbar.get()
