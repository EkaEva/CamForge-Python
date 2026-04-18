"""CamForge 主题管理器

管理浅色/深色主题切换，使用控件缓存替代递归遍历。
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt

from ui.constants import THEME, THEME_DARK


class ThemeManager:
    """管理浅色/深色主题切换。

    使用 register_widget() 在 GUI 构建时缓存可主题化控件，
    切换主题时遍历缓存列表而非递归遍历整棵控件树。
    """

    def __init__(self, dark_mode=False):
        self._dark_mode = dark_mode
        self._themed_widgets = []  # [(widget, wclass), ...]

    @property
    def is_dark(self):
        return self._dark_mode

    @property
    def current_theme(self):
        return THEME_DARK if self._dark_mode else THEME

    def register_widget(self, widget, wclass=None):
        """注册一个控件用于主题切换更新。

        Parameters
        ----------
        widget : tk.Widget
            需要更新颜色的控件。
        wclass : str or None
            控件类名。如果为 None，从 widget.winfo_class() 获取。
        """
        try:
            cls = wclass or widget.winfo_class()
            self._themed_widgets.append((widget, cls))
        except tk.TclError:
            pass

    def register_children(self, parent):
        """递归注册父控件下所有子控件。

        用于初始化时批量注册已创建的控件。

        Parameters
        ----------
        parent : tk.Widget
            父控件。
        """
        try:
            cls = parent.winfo_class()
            self._themed_widgets.append((parent, cls))
        except tk.TclError:
            pass
        for child in parent.winfo_children():
            self.register_children(child)

    def toggle(self, is_dark):
        """切换主题。

        Parameters
        ----------
        is_dark : bool
            True 为深色主题，False 为浅色主题。

        Returns
        -------
        bool
            主题是否实际发生了变化。
        """
        if is_dark == self._dark_mode:
            return False
        self._dark_mode = is_dark
        return True

    def apply_theme(self, root, sb_canvas=None, axes=None, canvas=None):
        """应用当前主题到所有已注册控件和 matplotlib 坐标轴。

        Parameters
        ----------
        root : tk.Tk
            根窗口（用于更新 ttk 样式）。
        sb_canvas : tk.Canvas or None
            侧边栏画布。
        axes : list or None
            matplotlib 坐标轴列表。
        canvas : FigureCanvasTkAgg or None
            matplotlib 画布。
        """
        theme = self.current_theme

        # 更新侧边栏画布背景
        if sb_canvas is not None:
            try:
                sb_canvas.config(bg=theme['sidebar_bg'])
            except tk.TclError:
                pass

        # 更新所有已注册控件
        for widget, wclass in self._themed_widgets:
            self._update_single_widget(widget, wclass, theme)

        # 更新 ttk Combobox 样式
        self._update_ttk_style(root)

        # 更新 matplotlib 样式
        self._update_mpl_style()

        # 更新 matplotlib 坐标轴
        if axes and canvas:
            for ax in axes:
                try:
                    ax.set_facecolor(plt.rcParams['axes.facecolor'])
                    ax.tick_params(colors=plt.rcParams['xtick.color'])
                    for spine in ax.spines.values():
                        spine.set_edgecolor(plt.rcParams['axes.edgecolor'])
                    ax.xaxis.label.set_color(plt.rcParams['axes.labelcolor'])
                    ax.yaxis.label.set_color(plt.rcParams['axes.labelcolor'])
                    ax.title.set_color(plt.rcParams['text.color'])
                except Exception:
                    pass

    def _update_single_widget(self, widget, wclass, theme):
        """更新单个控件的颜色。"""
        is_dark = self._dark_mode
        sidebar_bg = theme['sidebar_bg']
        toolbar_bg = theme['toolbar_bg']
        light_sidebar = THEME['sidebar_bg']
        light_toolbar = THEME['toolbar_bg']
        light_status = THEME['status_bg']
        dark_sidebar = THEME_DARK['sidebar_bg']
        dark_toolbar = THEME_DARK['toolbar_bg']
        dark_status = THEME_DARK['status_bg']

        def is_sidebar_bg(c):
            return c in (light_sidebar, dark_sidebar)

        def is_toolbar_bg(c):
            return c in (light_toolbar, dark_toolbar, light_status, dark_status)

        def is_themed_bg(c):
            return is_sidebar_bg(c) or is_toolbar_bg(c)

        try:
            if wclass in ('Frame', 'Labelframe'):
                bg = widget.cget('bg')
                if is_sidebar_bg(bg):
                    widget.config(bg=sidebar_bg)
                elif is_toolbar_bg(bg):
                    widget.config(bg=toolbar_bg)
                elif is_dark and not is_themed_bg(bg):
                    widget.config(bg=toolbar_bg)
            elif wclass == 'Label':
                bg = widget.cget('bg')
                if is_sidebar_bg(bg):
                    widget.config(bg=sidebar_bg)
                elif is_toolbar_bg(bg):
                    widget.config(bg=toolbar_bg)
                elif is_dark and not is_themed_bg(bg):
                    widget.config(bg=toolbar_bg)
                fg = widget.cget('fg')
                if fg in (THEME['group_fg'], THEME_DARK['group_fg']):
                    widget.config(fg=theme['group_fg'])
                elif fg in (THEME['logo_fg'], THEME_DARK['logo_fg']):
                    widget.config(fg=theme['logo_fg'])
                elif fg in (THEME['status_fg'], THEME_DARK['status_fg']):
                    widget.config(fg=theme['status_fg'])
                elif fg in (THEME['info_text'], THEME_DARK['info_text']):
                    widget.config(fg=theme['info_text'])
                elif is_dark and fg == 'black':
                    widget.config(fg='#e2e8f0')
            elif wclass == 'Checkbutton':
                bg = widget.cget('bg')
                if is_sidebar_bg(bg):
                    widget.config(bg=sidebar_bg)
                elif is_toolbar_bg(bg):
                    widget.config(bg=toolbar_bg)
                elif is_dark and not is_themed_bg(bg):
                    widget.config(bg=toolbar_bg)
                if is_dark:
                    widget.config(fg='#e2e8f0', selectcolor='#4a5568',
                                  activebackground=toolbar_bg, activeforeground='#e2e8f0')
                else:
                    widget.config(fg='black', selectcolor='white',
                                  activebackground=toolbar_bg, activeforeground='black')
            elif wclass == 'Entry':
                if is_dark:
                    widget.config(bg='#4a5568', fg='#e2e8f0', insertbackground='#e2e8f0',
                                  selectbackground='#4a5568')
                else:
                    widget.config(bg='white', fg='black', insertbackground='black',
                                  selectbackground='#b4d5fe')
            elif wclass == 'Scale':
                if is_dark:
                    widget.config(bg=toolbar_bg, fg='#e2e8f0',
                                  troughcolor='#4a5568', highlightbackground=toolbar_bg)
                else:
                    widget.config(bg=toolbar_bg, fg='black',
                                  troughcolor='#d0d0d0', highlightbackground=toolbar_bg)
            elif wclass == 'Button':
                pass  # 按钮保持自定义颜色
            elif wclass == 'Scrollbar':
                if is_dark:
                    widget.config(bg=sidebar_bg, troughcolor='#4a5568',
                                  activebackground='#4a5568')
                else:
                    widget.config(bg=light_sidebar, troughcolor='#d0d0d0',
                                  activebackground='#e2e8f0')
        except (tk.TclError, TypeError):
            pass

    def _update_ttk_style(self, root):
        """更新 ttk Combobox 样式。"""
        style = ttk.Style()
        if self._dark_mode:
            style.configure('TCombobox',
                            fieldbackground='#4a5568', background='#4a5568',
                            foreground='#e2e8f0', arrowcolor='#e2e8f0')
            style.map('TCombobox',
                      fieldbackground=[('readonly', '#4a5568')],
                      selectbackground=[('readonly', '#4a5568')],
                      selectforeground=[('readonly', '#e2e8f0')])
        else:
            style.configure('TCombobox',
                            fieldbackground='white', background='white',
                            foreground='black', arrowcolor='black')
            style.map('TCombobox',
                      fieldbackground=[('readonly', 'white')],
                      selectbackground=[('readonly', 'white')],
                      selectforeground=[('readonly', 'black')])

    def _update_mpl_style(self):
        """更新 matplotlib 全局样式参数。"""
        if self._dark_mode:
            plt.rcParams.update({
                'figure.facecolor': '#2d3748',
                'axes.facecolor':   '#374151',
                'axes.edgecolor':   '#6b7280',
                'axes.labelcolor':  '#e2e8f0',
                'xtick.color':      '#a0aec0',
                'ytick.color':      '#a0aec0',
                'text.color':       '#e2e8f0',
                'grid.color':       '#4a5568',
                'legend.facecolor': '#374151',
                'legend.edgecolor': '#4a5568',
            })
        else:
            plt.rcParams.update({
                'figure.facecolor': 'white',
                'axes.facecolor': 'white',
                'axes.edgecolor': 'black',
                'axes.labelcolor': 'black',
                'xtick.color': 'black',
                'ytick.color': 'black',
                'text.color': 'black',
                'grid.color': '#d0d0d0',
                'legend.facecolor': 'white',
                'legend.edgecolor': '#d0d0d0',
            })
