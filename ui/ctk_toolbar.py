"""CamForge CustomTkinter 工具栏模块

使用 CustomTkinter 实现现代化的工具栏：
- 圆角按钮
- 进度滑块
- 下载选项复选框
"""

import customtkinter as ctk
import tkinter as tk
import webbrowser
import os
from typing import Callable, Optional, Dict

from ui.ctk_constants import (
    UI_PADDING, CORNER_RADIUS, COLORS_LIGHT, COLORS_DARK,
    FONT_SIZE_LABEL, FONT_SIZE_BUTTON,
    BUTTON_HEIGHT, create_ctk_font, get_colors, get_button_style,
)
from i18n import t

# 尝试加载 PIL 用于 GitHub 图标
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CTkToolbar:
    """CustomTkinter 工具栏构建器

    Attributes
    ----------
    frame : CTkFrame
        工具栏容器
    buttons : dict
        按钮名称 -> CTkButton 映射
    checkboxes : dict
        复选框名称 -> BooleanVar 映射
    """

    def __init__(self, parent_frame, lang: str = 'zh'):
        """
        Parameters
        ----------
        parent_frame : widget
            父容器
        lang : str
            当前语言代码
        """
        self.frame = ctk.CTkFrame(
            parent_frame,
            fg_color='transparent',
            height=50,
        )

        self.lang = lang
        self.buttons: Dict[str, ctk.CTkButton] = {}
        self.checkboxes: Dict[str, tk.BooleanVar] = {}

    def build(self, lang: str,
              on_start: Optional[Callable] = None,
              on_pause: Optional[Callable] = None,
              on_clear: Optional[Callable] = None,
              on_random: Optional[Callable] = None,
              on_load_preset: Optional[Callable] = None,
              on_save_preset: Optional[Callable] = None,
              on_export_all: Optional[Callable] = None,
              on_download: Optional[Callable] = None,
              on_frame_seek: Optional[Callable] = None,
              on_help: Optional[Callable] = None,
              on_github: Optional[Callable] = None):
        """构建工具栏 UI

        Parameters
        ----------
        lang : str
            当前语言代码
        on_start : callable, optional
            开始仿真回调
        on_pause : callable, optional
            暂停回调
        on_clear : callable, optional
            清除回调
        on_random : callable, optional
            随机参数回调
        on_load_preset : callable, optional
            加载预设回调
        on_save_preset : callable, optional
            保存预设回调
        on_export_all : callable, optional
            全部导出回调
        on_download : callable, optional
            下载回调
        on_frame_seek : callable, optional
            帧跳转回调
        on_help : callable, optional
            帮助回调
        on_github : callable, optional
            GitHub 链接回调
        """
        self.lang = lang

        # 清除现有内容
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.buttons.clear()
        self.checkboxes.clear()

        # 左侧按钮组
        self._build_buttons(on_start, on_pause, on_clear, on_random,
                           on_load_preset, on_save_preset, on_export_all, on_download,
                           on_help, on_github)

        # 右侧控件组
        self._build_right_controls(on_frame_seek)

    def _build_buttons(self, on_start, on_pause, on_clear, on_random,
                       on_load_preset, on_save_preset, on_export_all, on_download,
                       on_help, on_github):
        """构建按钮组"""
        btn_frame = ctk.CTkFrame(self.frame, fg_color='transparent')
        btn_frame.pack(side='left', fill='y')

        # 开始按钮（绿色填充）
        btn_start = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.start", self.lang),
            command=on_start,
            fg_color=COLORS_LIGHT['success'],
            hover_color=COLORS_LIGHT['success_hover'],
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON, weight='bold'),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=70,
        )
        btn_start.pack(side='left', padx=(0, 6))
        self.buttons['start'] = btn_start

        # 暂停按钮（橙色）
        btn_pause = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.pause", self.lang),
            command=on_pause,
            fg_color=COLORS_LIGHT['warning'],
            hover_color=COLORS_LIGHT['warning_hover'],
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=60,
        )
        btn_pause.pack(side='left', padx=6)
        self.buttons['pause'] = btn_pause

        # 清除按钮（灰色轮廓）
        btn_clear = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.clear", self.lang),
            command=on_clear,
            fg_color='transparent',
            border_width=2,
            text_color=COLORS_LIGHT['text_secondary'],
            hover_color='#f0f0f0',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=60,
        )
        btn_clear.pack(side='left', padx=6)
        self.buttons['clear'] = btn_clear

        # 随机按钮（紫色）
        btn_random = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.random", self.lang),
            command=on_random,
            fg_color='#8b5cf6',
            hover_color='#7c3aed',
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=60,
        )
        btn_random.pack(side='left', padx=6)
        self.buttons['random'] = btn_random

        # 加载预设按钮（灰色）
        btn_load = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.load_preset", self.lang),
            command=on_load_preset,
            fg_color='#64748b',
            hover_color='#475569',
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=70,
        )
        btn_load.pack(side='left', padx=6)
        self.buttons['load_preset'] = btn_load

        # 保存预设按钮
        btn_save = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.save_preset", self.lang),
            command=on_save_preset,
            fg_color='#64748b',
            hover_color='#475569',
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=70,
        )
        btn_save.pack(side='left', padx=6)
        self.buttons['save_preset'] = btn_save

        # 全部导出按钮
        btn_export_all = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.export_all", self.lang),
            command=on_export_all,
            fg_color='#8b5cf6',
            hover_color='#7c3aed',
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=70,
        )
        btn_export_all.pack(side='left', padx=6)
        self.buttons['export_all'] = btn_export_all

        # 下载按钮（蓝色）
        btn_download = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.download", self.lang),
            command=on_download,
            fg_color=COLORS_LIGHT['accent'],
            hover_color=COLORS_LIGHT['accent_hover'],
            text_color='white',
            font=create_ctk_font(size=FONT_SIZE_BUTTON, weight='bold'),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=70,
        )
        btn_download.pack(side='left', padx=6)
        self.buttons['download'] = btn_download

        # 帮助按钮（灰色轮廓）
        btn_help = ctk.CTkButton(
            btn_frame,
            text=t("toolbar.btn.help", self.lang),
            command=on_help,
            fg_color='transparent',
            border_width=2,
            text_color=COLORS_LIGHT['text_secondary'],
            hover_color='#f0f0f0',
            font=create_ctk_font(size=FONT_SIZE_BUTTON),
            corner_radius=CORNER_RADIUS,
            height=BUTTON_HEIGHT,
            width=60,
        )
        btn_help.pack(side='left', padx=6)
        self.buttons['help'] = btn_help

        # GitHub 按钮（图标）
        github_icon = self._load_github_icon()
        if github_icon:
            btn_github = ctk.CTkButton(
                btn_frame,
                text="",
                image=github_icon,
                command=on_github,
                fg_color='transparent',
                hover_color='#e0e0e0',
                corner_radius=CORNER_RADIUS,
                height=BUTTON_HEIGHT,
                width=40,
            )
        else:
            # 回退到文字按钮
            btn_github = ctk.CTkButton(
                btn_frame,
                text=t("toolbar.btn.github", self.lang),
                command=on_github,
                fg_color='#24292e',
                hover_color='#1a1e22',
                text_color='white',
                font=create_ctk_font(size=FONT_SIZE_BUTTON),
                corner_radius=CORNER_RADIUS,
                height=BUTTON_HEIGHT,
                width=70,
            )
        btn_github.pack(side='left', padx=6)
        self.buttons['github'] = btn_github

    def _load_github_icon(self):
        """加载 GitHub 图标"""
        if not PIL_AVAILABLE:
            return None
        try:
            # 尝试多个可能的路径
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'github.png'),
                os.path.join(os.path.dirname(__file__), 'github.png'),
                'github.png',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    img = PILImage.open(path)
                    # 调整大小以适应按钮（放大图标）
                    img = img.resize((28, 28), PILImage.Resampling.LANCZOS)
                    return ctk.CTkImage(light_image=img, dark_image=img, size=(28, 28))
        except Exception:
            pass
        return None

    def _build_right_controls(self, on_frame_seek):
        """构建右侧控件（速度滑块、帧进度条）"""
        right_frame = ctk.CTkFrame(self.frame, fg_color='transparent')
        right_frame.pack(side='right', padx=(0, UI_PADDING))

        # 帧进度条
        frame_frame = ctk.CTkFrame(right_frame, fg_color='transparent')
        frame_frame.pack(side='right', padx=(20, 0))

        frame_label = ctk.CTkLabel(
            frame_frame,
            text=t("toolbar.label.frame", self.lang),
            font=create_ctk_font(size=FONT_SIZE_LABEL),
        )
        frame_label.pack(side='left', padx=(0, 8))

        self.frame_var = tk.IntVar(value=0)
        self.frame_slider = ctk.CTkSlider(
            frame_frame,
            from_=0,
            to=359,
            number_of_steps=360,
            variable=self.frame_var,
            command=on_frame_seek,
            width=120,
        )
        self.frame_slider.pack(side='left')

        # 速度滑块
        speed_frame = ctk.CTkFrame(right_frame, fg_color='transparent')
        speed_frame.pack(side='right', padx=(20, 0))

        speed_label = ctk.CTkLabel(
            speed_frame,
            text=t("toolbar.label.speed", self.lang),
            font=create_ctk_font(size=FONT_SIZE_LABEL),
        )
        speed_label.pack(side='left', padx=(0, 8))

        self.speed_var = tk.IntVar(value=3)
        self.speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.speed_var,
            width=100,
        )
        self.speed_slider.pack(side='left')

    def update_pause_button(self, text: str):
        """更新暂停按钮文本"""
        if 'pause' in self.buttons:
            self.buttons['pause'].configure(text=text)

    def set_frame_range(self, max_frame: int):
        """设置帧进度条范围"""
        self.frame_slider.configure(to=max_frame, number_of_steps=max_frame)

    def set_frame(self, frame: int):
        """设置当前帧"""
        self.frame_var.set(frame)

    def get_speed(self) -> int:
        """获取速度值"""
        return self.speed_var.get()

    def is_checked(self, name: str) -> bool:
        """检查复选框是否选中"""
        return self.checkboxes.get(name, tk.BooleanVar(value=False)).get()


def show_help_dialog(parent, lang: str):
    """显示帮助对话框

    Parameters
    ----------
    parent : widget
        父窗口
    lang : str
        当前语言代码
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(t("help.title", lang))
    dialog.geometry("420x480")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # 居中显示
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 480) // 2
    dialog.geometry(f"+{x}+{y}")

    # 使用说明
    section1 = ctk.CTkLabel(
        dialog,
        text=t("help.section.usage", lang),
        font=create_ctk_font(size=FONT_SIZE_LABEL + 2, weight='bold'),
        anchor='w',
    )
    section1.pack(fill='x', padx=20, pady=(20, 8))

    for i in range(1, 4):
        label = ctk.CTkLabel(
            dialog,
            text=t(f"help.usage.{i}", lang),
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        label.pack(fill='x', padx=30, pady=2)

    # 键盘快捷键
    section2 = ctk.CTkLabel(
        dialog,
        text=t("help.section.shortcuts", lang),
        font=create_ctk_font(size=FONT_SIZE_LABEL + 2, weight='bold'),
        anchor='w',
    )
    section2.pack(fill='x', padx=20, pady=(20, 8))

    shortcuts = ['enter', 'space', 'left', 'right', 'home', 'end', 'esc', 'r']
    for key in shortcuts:
        label = ctk.CTkLabel(
            dialog,
            text=t(f"help.shortcuts.{key}", lang),
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        label.pack(fill='x', padx=30, pady=2)

    # 提示
    section3 = ctk.CTkLabel(
        dialog,
        text=t("help.section.tips", lang),
        font=create_ctk_font(size=FONT_SIZE_LABEL + 2, weight='bold'),
        anchor='w',
    )
    section3.pack(fill='x', padx=20, pady=(20, 8))

    for i in range(1, 5):
        label = ctk.CTkLabel(
            dialog,
            text=t(f"help.tips.{i}", lang),
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        label.pack(fill='x', padx=30, pady=2)

    # 关闭按钮
    btn_close = ctk.CTkButton(
        dialog,
        text="OK",
        command=dialog.destroy,
        corner_radius=CORNER_RADIUS,
        width=80,
    )
    btn_close.pack(pady=(20, 15))


def open_github():
    """打开 GitHub 项目页面"""
    webbrowser.open("https://github.com/EkaEva/CamForge")


class CTkStatusBar:
    """CustomTkinter 状态栏

    Attributes
    ----------
    frame : CTkFrame
        状态栏容器
    """

    def __init__(self, parent_frame, lang: str = 'zh'):
        """
        Parameters
        ----------
        parent_frame : widget
            父容器
        lang : str
            当前语言代码
        """
        self.frame = ctk.CTkFrame(
            parent_frame,
            fg_color='transparent',
        )

        self.lang = lang

    def build(self, lang: str):
        """构建状态栏 UI"""
        self.lang = lang

        # 清除现有内容
        for widget in self.frame.winfo_children():
            widget.destroy()

        # 第一行：状态消息
        row1 = ctk.CTkFrame(self.frame, fg_color='transparent')
        row1.pack(fill='x')

        self.status_var = tk.StringVar()
        self.status_label = ctk.CTkLabel(
            row1,
            textvariable=self.status_var,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            text_color=COLORS_LIGHT['danger'],
            anchor='w',
        )
        self.status_label.pack(side='left')

        # 第二行：行程 | 初始位移 | 最大压力角
        row2 = ctk.CTkFrame(self.frame, fg_color='transparent')
        row2.pack(fill='x')

        self.stroke_var = tk.StringVar()
        self.stroke_label = ctk.CTkLabel(
            row2,
            textvariable=self.stroke_var,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        self.stroke_label.pack(side='left', padx=(0, 20))

        self.s0_var = tk.StringVar()
        self.s0_label = ctk.CTkLabel(
            row2,
            textvariable=self.s0_var,
            font=create_ctk_font(size=FONT_SIZE_LABEL),
            anchor='w',
        )
        self.s0_label.pack(side='left', padx=20)

        self.alpha_var = tk.StringVar()
        self.alpha_label = ctk.CTkLabel(
            row2,
            textvariable=self.alpha_var,
            font=create_ctk_font(size=FONT_SIZE_LABEL, weight='bold'),
            anchor='w',
        )
        self.alpha_label.pack(side='left', padx=20)

    def set_status(self, text: str, style: str = 'default'):
        """设置状态消息"""
        colors = get_colors()
        text_colors = {
            'default': colors['text_primary'],
            'success': colors['success'],
            'warning': colors['warning'],
            'danger': colors['danger'],
        }
        self.status_var.set(text)
        self.status_label.configure(
            text_color=text_colors.get(style, colors['text_primary'])
        )

    def set_stroke(self, text: str):
        """设置行程文本"""
        self.stroke_var.set(text)

    def set_s0(self, text: str):
        """设置初始位移文本"""
        self.s0_var.set(text)

    def set_alpha(self, text: str):
        """设置最大压力角文本"""
        self.alpha_var.set(text)

    def clear(self):
        """清除所有状态"""
        self.status_var.set('')
        self.stroke_var.set('')
        self.s0_var.set('')
        self.alpha_var.set('')
