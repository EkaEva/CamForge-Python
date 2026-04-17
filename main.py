"""
CamForge - 尖顶凸轮仿真
使用 tkinter + matplotlib 实现凸轮机构运动学仿真
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import os
import threading
import json
from io import BytesIO
from tkinter import filedialog

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

from cam_mechanics import (
    compute_full_motion, compute_cam_profile, compute_pressure_angle,
    compute_rotated_cam, compute_anim_frame_data,
    compute_pressure_angle_arc, validate_params,
    compute_roller_profile, compute_curvature_radius,
    DEG2RAD, __version__,
)

from i18n import t, SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP, LANG_DISPLAY_NAMES, get_motion_law_list, get_rotation_list, get_offset_dir_list, get_lang_display_list, detect_mpl_fonts

import sys
import platform

plt.rcParams['font.sans-serif'] = detect_mpl_fonts(DEFAULT_LANG)
plt.rcParams['axes.unicode_minus'] = False

# 从 ui 包导入常量、绘图函数和参数模型
from ui.constants import *
from ui.drawing import draw_fixed_support
from ui.params import ParameterModel, generate_random_params
from ui.plots import (draw_displacement_curve, draw_velocity_curve,
                      draw_acceleration_curve, draw_profile_plot,
                      draw_pressure_angle_curve, draw_curvature_radius_curve)
from ui.constants import THEME_DARK


class CamSimulator:
    """凸轮机构仿真主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{t('app.title', DEFAULT_LANG)} v{__version__}")

        self.lang = DEFAULT_LANG
        self._tk_font_family = FONT_MAP[DEFAULT_LANG]["tk"]
        self._translatable = {}  # key -> (widget, font_size)
        self._pause_state = "paused"
        self._dark_mode = False

        # 跨平台窗口最大化
        if platform.system() == 'Windows':
            try:
                self.root.state('zoomed')
            except tk.TclError:
                self.root.geometry("1400x800")
        elif platform.system() == 'Darwin':
            self.root.attributes('-fullscreen', True)
        else:
            self.root.attributes('-zoomed', True)

        # 动画控制
        self.animating = False
        self.paused = False
        self.anim_id = None
        self.current_frame = 0

        # 预计算缓存
        self.sim_data = None
        self._sim_data_lock = threading.Lock()
        self._anim_artists = None

        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 键盘快捷键（Entry/Combobox 聚焦时屏蔽单字母快捷键）
        self.root.bind('<Return>', lambda e: self._on_start() if not isinstance(self.root.focus_get(), (tk.Entry, ttk.Combobox)) else None)
        self.root.bind('<space>', lambda e: self._on_pause() if not isinstance(self.root.focus_get(), (tk.Entry, ttk.Combobox)) else None)
        self.root.bind('<r>', lambda e: self._on_random() if not isinstance(self.root.focus_get(), (tk.Entry, ttk.Combobox)) else None)

        self._build_gui()

        # 延迟刷新侧边栏，确保初始内容正确显示
        self.root.after(50, self._refresh_sidebar)

    # ===================================================================
    # i18n helpers
    # ===================================================================

    def _reg(self, key, widget, font_size=None):
        """Register a widget for language-switch updates"""
        self._translatable[key] = (widget, font_size)

    def _law_name(self, law_id):
        """Get motion law name in current language"""
        return t(f"law.{law_id}", self.lang)

    def _on_language_change(self, event=None):
        """Handle language switch"""
        idx = self.popup_lang.current()
        new_lang = SUPPORTED_LANGS[idx]
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self._tk_font_family = FONT_MAP[new_lang]["tk"]
        self._apply_language()
        self._update_mpl_fonts(new_lang)
        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self._init_info_panel()
                self.ax_anim.set_title(t("plot.title.animation", self.lang), fontsize=12)
                self.canvas.draw_idle()

    def _apply_language(self):
        """Update all registered widgets for current language"""
        for key, (widget, font_size) in self._translatable.items():
            text = t(key, self.lang)
            try:
                widget.config(text=text)
            except tk.TclError:
                pass
            if font_size is not None:
                try:
                    widget.config(font=(self._tk_font_family, font_size))
                except tk.TclError:
                    pass
        # Update combobox values (preserve current index)
        tc_idx = self.popup_tc.current()
        hc_idx = self.popup_hc.current()
        sn_idx = self.popup_sn.current()
        pz_idx = self.popup_pz.current()
        self.popup_tc.config(values=get_motion_law_list(self.lang))
        self.popup_hc.config(values=get_motion_law_list(self.lang))
        self.popup_sn.config(values=get_rotation_list(self.lang))
        self.popup_pz.config(values=get_offset_dir_list(self.lang))
        self.popup_tc.current(tc_idx)
        self.popup_hc.current(hc_idx)
        self.popup_sn.current(sn_idx)
        self.popup_pz.current(pz_idx)
        self.root.title(f"{t('app.title', self.lang)} v{__version__}")

    def _update_mpl_fonts(self, lang):
        """Update matplotlib font config"""
        plt.rcParams['font.sans-serif'] = detect_mpl_fonts(lang)
        plt.rcParams['axes.unicode_minus'] = False

    def _on_theme_change(self, event=None):
        """Handle theme switch (light/dark)"""
        is_dark = self.popup_theme.current() == 1
        if is_dark == self._dark_mode:
            return
        self._dark_mode = is_dark
        self._apply_theme()

    def _apply_theme(self):
        """Apply current theme to all widgets"""
        theme = THEME_DARK if self._dark_mode else THEME

        # Update sidebar background
        self._sb_canvas.config(bg=theme['sidebar_bg'])
        # Recursively update all widget colors
        self._update_widget_colors(self.root, theme)

        # Update matplotlib style
        if self._dark_mode:
            plt.rcParams.update({
                'figure.facecolor': '#0f172a',
                'axes.facecolor': '#1e293b',
                'axes.edgecolor': '#475569',
                'axes.labelcolor': '#e2e8f0',
                'xtick.color': '#94a3b8',
                'ytick.color': '#94a3b8',
                'text.color': '#e2e8f0',
                'grid.color': '#334155',
                'legend.facecolor': '#1e293b',
                'legend.edgecolor': '#334155',
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

        # Redraw if simulation data exists
        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self.ax_anim.set_facecolor(plt.rcParams['axes.facecolor'])
                self.canvas.draw_idle()

    def _update_widget_colors(self, widget, theme):
        """Recursively update widget background/foreground colors"""
        try:
            wclass = widget.winfo_class()
            if wclass in ('Frame', 'Labelframe'):
                bg = widget.cget('bg')
                if bg in (THEME['sidebar_bg'], THEME_DARK['sidebar_bg'],
                          THEME['toolbar_bg'], THEME_DARK['toolbar_bg']):
                    new_bg = theme['sidebar_bg'] if bg in (THEME['sidebar_bg'], THEME_DARK['sidebar_bg']) else theme['toolbar_bg']
                    widget.config(bg=new_bg)
            elif wclass == 'Label':
                bg = widget.cget('bg')
                if bg in (THEME['sidebar_bg'], THEME_DARK['sidebar_bg']):
                    widget.config(bg=theme['sidebar_bg'])
                elif bg in (THEME['toolbar_bg'], THEME_DARK['toolbar_bg']):
                    widget.config(bg=theme['toolbar_bg'])
                fg = widget.cget('fg')
                if fg in (THEME['group_fg'], THEME_DARK['group_fg']):
                    widget.config(fg=theme['group_fg'])
                elif fg in (THEME['logo_fg'], THEME_DARK['logo_fg']):
                    widget.config(fg=theme['logo_fg'])
                elif fg in (THEME['status_fg'], THEME_DARK['status_fg']):
                    widget.config(fg=theme['status_fg'])
                elif fg in (THEME['info_text'], THEME_DARK['info_text']):
                    widget.config(fg=theme['info_text'])
            elif wclass == 'Checkbutton':
                bg = widget.cget('bg')
                if bg in (THEME['sidebar_bg'], THEME_DARK['sidebar_bg']):
                    widget.config(bg=theme['sidebar_bg'])
                elif bg in (THEME['toolbar_bg'], THEME_DARK['toolbar_bg']):
                    widget.config(bg=theme['toolbar_bg'])
            elif wclass == 'Button':
                # Re-apply button colors from theme
                pass  # Buttons keep their styled colors
        except (tk.TclError, TypeError):
            pass
        for child in widget.winfo_children():
            self._update_widget_colors(child, theme)

    # ===================================================================
    # GUI 构建（拆分为子方法）
    # ===================================================================

    def _build_gui(self):
        """构建整体界面布局"""
        # ---- 整体布局：左侧边栏（可滚动） + 右侧主区域 ----
        sidebar_outer = tk.Frame(self.root, width=280, bg=THEME['sidebar_bg'],
                                 highlightbackground=THEME['sidebar_border'], highlightthickness=1)
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_outer.pack_propagate(False)

        # 可滚动侧边栏：Canvas + Scrollbar + 内部Frame
        self._sb_canvas = tk.Canvas(sidebar_outer, bg=THEME['sidebar_bg'], highlightthickness=0, width=260)
        sb_scrollbar = tk.Scrollbar(sidebar_outer, orient=tk.VERTICAL, command=self._sb_canvas.yview)
        sb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._sb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(self._sb_canvas, bg=THEME['sidebar_bg'])
        self._sb_win = self._sb_canvas.create_window(0, 0, window=sidebar, anchor='nw')

        sidebar.bind('<Configure>', self._on_sidebar_configure)
        self._sb_canvas.configure(yscrollcommand=sb_scrollbar.set)

        # 鼠标滚轮绑定（仅悬停时，跨平台兼容）
        self._sb_canvas.bind('<Enter>', self._bind_mousewheel)
        self._sb_canvas.bind('<Leave>', self._unbind_mousewheel)

        main_area = tk.Frame(self.root)
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 拆分为子方法构建
        self._build_sidebar(sidebar)
        toolbar, status_bar = self._build_toolbar(main_area)
        self._build_figure(main_area)

    def _build_sidebar(self, sidebar):
        """构建侧边栏内容"""
        lbl_font = (self._tk_font_family, 10)
        ent_font = (self._tk_font_family, 10)
        lbl_kw = {'font': lbl_font, 'bg': THEME['sidebar_bg'], 'anchor': 'w'}
        ent_kw = {'font': ent_font, 'width': 14}

        # Logo
        tk.Label(sidebar, text="CamForge", font=(self._tk_font_family, 16, 'bold'),
                 fg=THEME['logo_fg'], bg=THEME['sidebar_bg'], anchor='w').pack(fill=tk.X, padx=16, pady=(16, 20))

        # ---- 语言选择组 ----
        self._sidebar_group(sidebar, t("sidebar.group.language", self.lang), i18n_key="sidebar.group.language")
        self.popup_lang = ttk.Combobox(sidebar, values=get_lang_display_list(), state='readonly', width=14)
        self.popup_lang.current(SUPPORTED_LANGS.index(DEFAULT_LANG))
        self.popup_lang.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.popup_lang.bind('<<ComboboxSelected>>', self._on_language_change)

        # ---- 主题选择组 ----
        self._sidebar_group(sidebar, t("sidebar.group.theme", self.lang), i18n_key="sidebar.group.theme")
        theme_values = [t("theme.light", self.lang), t("theme.dark", self.lang)]
        self.popup_theme = ttk.Combobox(sidebar, values=theme_values, state='readonly', width=14)
        self.popup_theme.current(0)
        self.popup_theme.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.popup_theme.bind('<<ComboboxSelected>>', self._on_theme_change)

        # ---- 运动参数组 ----
        self._sidebar_group(sidebar, t("sidebar.group.motion", self.lang), i18n_key="sidebar.group.motion")

        self._sidebar_item(sidebar, t("sidebar.label.delta_0", self.lang), lbl_kw, i18n_key="sidebar.label.delta_0")
        self.entry_delta_0 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_0.insert(0, str(DEFAULT_PARAMS['delta_0']))
        self.entry_delta_0.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_delta_0.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_delta_0, float))

        self._sidebar_item(sidebar, t("sidebar.label.delta_01", self.lang), lbl_kw, i18n_key="sidebar.label.delta_01")
        self.entry_delta_01 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_01.insert(0, str(DEFAULT_PARAMS['delta_01']))
        self.entry_delta_01.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_delta_01.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_delta_01, float))

        self._sidebar_item(sidebar, t("sidebar.label.delta_ret", self.lang), lbl_kw, i18n_key="sidebar.label.delta_ret")
        self.entry_delta_ret = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_ret.insert(0, str(DEFAULT_PARAMS['delta_ret']))
        self.entry_delta_ret.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_delta_ret.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_delta_ret, float))

        self._sidebar_item(sidebar, t("sidebar.label.delta_02", self.lang), lbl_kw, i18n_key="sidebar.label.delta_02")
        self.entry_delta_02 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_02.insert(0, str(DEFAULT_PARAMS['delta_02']))
        self.entry_delta_02.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_delta_02.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_delta_02, float))

        self._sidebar_item(sidebar, t("sidebar.label.h", self.lang), lbl_kw, i18n_key="sidebar.label.h")
        self.entry_h = tk.Entry(sidebar, **ent_kw)
        self.entry_h.insert(0, str(DEFAULT_PARAMS['h']))
        self.entry_h.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_h.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_h, float))

        self._sidebar_item(sidebar, t("sidebar.label.omega", self.lang), lbl_kw, i18n_key="sidebar.label.omega")
        self.entry_omega = tk.Entry(sidebar, **ent_kw)
        self.entry_omega.insert(0, str(DEFAULT_PARAMS['omega']))
        self.entry_omega.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_omega.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_omega, float))

        # ---- 几何参数组 ----
        self._sidebar_group(sidebar, t("sidebar.group.geometry", self.lang), i18n_key="sidebar.group.geometry")

        self._sidebar_item(sidebar, t("sidebar.label.r_0", self.lang), lbl_kw, i18n_key="sidebar.label.r_0")
        self.entry_r0 = tk.Entry(sidebar, **ent_kw)
        self.entry_r0.insert(0, str(DEFAULT_PARAMS['r_0']))
        self.entry_r0.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_r0.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_r0, float))

        self._sidebar_item(sidebar, t("sidebar.label.e", self.lang), lbl_kw, i18n_key="sidebar.label.e")
        self.entry_e = tk.Entry(sidebar, **ent_kw)
        self.entry_e.insert(0, str(DEFAULT_PARAMS['e']))
        self.entry_e.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_e.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_e, float))

        self._sidebar_item(sidebar, t("sidebar.label.r_r", self.lang), lbl_kw, i18n_key="sidebar.label.r_r")
        self.entry_rr = tk.Entry(sidebar, **ent_kw)
        self.entry_rr.insert(0, str(DEFAULT_PARAMS['r_r']))
        self.entry_rr.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_rr.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_rr, float))

        self._sidebar_item(sidebar, t("sidebar.label.alpha_threshold", self.lang), lbl_kw, i18n_key="sidebar.label.alpha_threshold")
        self.entry_alpha_threshold = tk.Entry(sidebar, **ent_kw)
        self.entry_alpha_threshold.insert(0, str(DEFAULT_PARAMS['alpha_threshold']))
        self.entry_alpha_threshold.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_alpha_threshold.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_alpha_threshold, float))

        self._sidebar_item(sidebar, t("sidebar.label.n_points", self.lang), lbl_kw, i18n_key="sidebar.label.n_points")
        self.entry_n_points = tk.Entry(sidebar, **ent_kw)
        self.entry_n_points.insert(0, str(DEFAULT_PARAMS['n_points']))
        self.entry_n_points.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entry_n_points.bind('<FocusOut>', lambda e: self._validate_entry(self.entry_n_points, int))

        # ---- 运动规律组 ----
        self._sidebar_group(sidebar, t("sidebar.group.law", self.lang), i18n_key="sidebar.group.law")

        motion_laws = get_motion_law_list(self.lang)
        combo_kw = {'state': 'readonly', 'width': 14}

        self._sidebar_item(sidebar, t("sidebar.label.tc_law", self.lang), lbl_kw, i18n_key="sidebar.label.tc_law")
        self.popup_tc = ttk.Combobox(sidebar, values=motion_laws, **combo_kw)
        self.popup_tc.current(0)
        self.popup_tc.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.hc_law", self.lang), lbl_kw, i18n_key="sidebar.label.hc_law")
        self.popup_hc = ttk.Combobox(sidebar, values=motion_laws, **combo_kw)
        self.popup_hc.current(0)
        self.popup_hc.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.rotation", self.lang), lbl_kw, i18n_key="sidebar.label.rotation")
        self.popup_sn = ttk.Combobox(sidebar, values=get_rotation_list(self.lang), **combo_kw)
        self.popup_sn.current(0)
        self.popup_sn.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.offset_dir", self.lang), lbl_kw, i18n_key="sidebar.label.offset_dir")
        self.popup_pz = ttk.Combobox(sidebar, values=get_offset_dir_list(self.lang), **combo_kw)
        self.popup_pz.current(0)
        self.popup_pz.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 动态显示组 ----
        self._sidebar_group(sidebar, t("sidebar.group.display", self.lang), i18n_key="sidebar.group.display")

        cb_kw = {'font': (self._tk_font_family, 10), 'anchor': 'w', 'bg': THEME['sidebar_bg']}

        self.show_tangent = tk.BooleanVar(value=False)
        cb_tangent = tk.Checkbutton(sidebar, text=t("sidebar.cb.tangent", self.lang), variable=self.show_tangent,
                       **cb_kw)
        cb_tangent.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.tangent", cb_tangent, font_size=10)

        self.show_normal = tk.BooleanVar(value=False)
        cb_normal = tk.Checkbutton(sidebar, text=t("sidebar.cb.normal", self.lang), variable=self.show_normal,
                       **cb_kw)
        cb_normal.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.normal", cb_normal, font_size=10)

        self.show_arc = tk.BooleanVar(value=False)
        cb_arc = tk.Checkbutton(sidebar, text=t("sidebar.cb.arc", self.lang), variable=self.show_arc,
                       command=self._on_arc_toggle, **cb_kw)
        cb_arc.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.arc", cb_arc, font_size=10)

        self.show_boundaries = tk.BooleanVar(value=False)
        cb_boundaries = tk.Checkbutton(sidebar, text=t("sidebar.cb.boundaries", self.lang), variable=self.show_boundaries,
                       **cb_kw)
        cb_boundaries.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.boundaries", cb_boundaries, font_size=10)

        self.show_base_circle = tk.BooleanVar(value=False)
        cb_base_circle = tk.Checkbutton(sidebar, text=t("sidebar.cb.base_circle", self.lang), variable=self.show_base_circle,
                       **cb_kw)
        cb_base_circle.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.base_circle", cb_base_circle, font_size=10)

        self.show_offset_circle = tk.BooleanVar(value=False)
        cb_offset_circle = tk.Checkbutton(sidebar, text=t("sidebar.cb.offset_circle", self.lang), variable=self.show_offset_circle,
                       **cb_kw)
        cb_offset_circle.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.offset_circle", cb_offset_circle, font_size=10)

        self.show_limits = tk.BooleanVar(value=False)
        cb_limits = tk.Checkbutton(sidebar, text=t("sidebar.cb.limits", self.lang), variable=self.show_limits,
                       **cb_kw)
        cb_limits.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.limits", cb_limits, font_size=10)

        self.show_grid = tk.BooleanVar(value=False)
        cb_grid = tk.Checkbutton(sidebar, text=t("sidebar.cb.grid", self.lang), variable=self.show_grid,
                       command=self._on_grid_toggle, **cb_kw)
        cb_grid.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.grid", cb_grid, font_size=10)

    def _build_toolbar(self, main_area):
        """构建工具栏与状态栏"""
        toolbar = tk.Frame(main_area, bg=THEME['toolbar_bg'], pady=6)
        toolbar.pack(fill=tk.X, padx=12, pady=(8, 0))

        btn_kw = {'font': (self._tk_font_family, 10), 'width': 10, 'height': 1,
                  'relief': tk.FLAT, 'cursor': 'hand2', 'bd': 0}

        self.btn_start = tk.Button(toolbar, text=t("toolbar.btn.start", self.lang), command=self._on_start,
                                   bg=THEME['btn_start'], fg=THEME['btn_fg'], activebackground=THEME['btn_start_active'],
                                   **btn_kw)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))
        self._reg("toolbar.btn.start", self.btn_start, font_size=10)

        self.btn_pause = tk.Button(toolbar, text=t("toolbar.btn.pause", self.lang), command=self._on_pause,
                                   bg=THEME['btn_pause'], fg=THEME['btn_fg'], activebackground=THEME['btn_pause_active'],
                                   **btn_kw)
        self.btn_pause.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.pause", self.btn_pause, font_size=10)

        self.btn_clear_params = tk.Button(toolbar, text=t("toolbar.btn.clear_params", self.lang),
                                          command=self._on_clear_params,
                                          bg=THEME['btn_clear'], fg=THEME['btn_fg'],
                                          activebackground=THEME['btn_clear_active'],
                                          relief=tk.FLAT, bd=0,
                                          font=(self._tk_font_family, 10), width=10, height=1,
                                          cursor='hand2')
        self.btn_clear_params.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.clear_params", self.btn_clear_params, font_size=10)

        self.btn_clear_plots = tk.Button(toolbar, text=t("toolbar.btn.clear_plots", self.lang),
                                         command=self._on_clear_plots,
                                         bg=THEME['btn_clear2'], fg=THEME['btn_fg'],
                                         activebackground=THEME['btn_clear2_active'],
                                         relief=tk.FLAT, bd=0,
                                         font=(self._tk_font_family, 10), width=10, height=1,
                                         cursor='hand2')
        self.btn_clear_plots.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.clear_plots", self.btn_clear_plots, font_size=10)

        self.btn_random = tk.Button(toolbar, text=t("toolbar.btn.random", self.lang),
                                    command=self._on_random,
                                    bg=THEME['btn_random'], fg=THEME['btn_fg'],
                                    activebackground=THEME['btn_random_active'],
                                    relief=tk.FLAT, bd=0,
                                    font=(self._tk_font_family, 10), width=10, height=1,
                                    cursor='hand2')
        self.btn_random.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.random", self.btn_random, font_size=10)

        self.btn_download = tk.Button(toolbar, text=t("toolbar.btn.download", self.lang),
                                      command=self._on_download,
                                      bg=THEME['btn_download'], fg=THEME['btn_fg'],
                                      activebackground=THEME['btn_download_active'],
                                      relief=tk.FLAT, bd=0,
                                      font=(self._tk_font_family, 10), width=10, height=1,
                                      cursor='hand2')
        self.btn_download.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.download", self.btn_download, font_size=10)

        self.btn_save_preset = tk.Button(toolbar, text=t("toolbar.btn.save_preset", self.lang),
                                         command=self._on_save_preset,
                                         bg=THEME['btn_clear'], fg=THEME['btn_fg'],
                                         activebackground=THEME['btn_clear_active'],
                                         relief=tk.FLAT, bd=0,
                                         font=(self._tk_font_family, 10), width=10, height=1,
                                         cursor='hand2')
        self.btn_save_preset.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.save_preset", self.btn_save_preset, font_size=10)

        self.btn_load_preset = tk.Button(toolbar, text=t("toolbar.btn.load_preset", self.lang),
                                         command=self._on_load_preset,
                                         bg=THEME['btn_clear2'], fg=THEME['btn_fg'],
                                         activebackground=THEME['btn_clear2_active'],
                                         relief=tk.FLAT, bd=0,
                                         font=(self._tk_font_family, 10), width=10, height=1,
                                         cursor='hand2')
        self.btn_load_preset.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.load_preset", self.btn_load_preset, font_size=10)

        # 下载勾选项
        dl_cb_kw = {'font': (self._tk_font_family, 9), 'bg': THEME['toolbar_bg'], 'anchor': 'w'}
        self.dl_s = tk.BooleanVar(value=True)
        cb_dl_s = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_s", self.lang), variable=self.dl_s, **dl_cb_kw)
        cb_dl_s.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_s", cb_dl_s, font_size=9)
        self.dl_v = tk.BooleanVar(value=True)
        cb_dl_v = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_v", self.lang), variable=self.dl_v, **dl_cb_kw)
        cb_dl_v.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_v", cb_dl_v, font_size=9)
        self.dl_a = tk.BooleanVar(value=True)
        cb_dl_a = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_a", self.lang), variable=self.dl_a, **dl_cb_kw)
        cb_dl_a.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_a", cb_dl_a, font_size=9)
        self.dl_profile = tk.BooleanVar(value=True)
        cb_dl_profile = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_profile", self.lang), variable=self.dl_profile, **dl_cb_kw)
        cb_dl_profile.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_profile", cb_dl_profile, font_size=9)
        self.dl_anim = tk.BooleanVar(value=True)
        cb_dl_anim = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_anim", self.lang), variable=self.dl_anim, **dl_cb_kw)
        cb_dl_anim.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_anim", cb_dl_anim, font_size=9)
        self.dl_excel = tk.BooleanVar(value=True)
        cb_dl_excel = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_excel", self.lang), variable=self.dl_excel, **dl_cb_kw)
        cb_dl_excel.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_excel", cb_dl_excel, font_size=9)
        self.dl_alpha = tk.BooleanVar(value=True)
        cb_dl_alpha = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_alpha", self.lang), variable=self.dl_alpha, **dl_cb_kw)
        cb_dl_alpha.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_alpha", cb_dl_alpha, font_size=9)
        self.dl_curvature = tk.BooleanVar(value=False)
        cb_dl_curvature = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_curvature", self.lang), variable=self.dl_curvature, **dl_cb_kw)
        cb_dl_curvature.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_curvature", cb_dl_curvature, font_size=9)
        self.dl_svg = tk.BooleanVar(value=False)
        cb_dl_svg = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_svg", self.lang), variable=self.dl_svg, **dl_cb_kw)
        cb_dl_svg.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_svg", cb_dl_svg, font_size=9)
        self.dl_csv = tk.BooleanVar(value=False)
        cb_dl_csv = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_csv", self.lang), variable=self.dl_csv, **dl_cb_kw)
        cb_dl_csv.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_csv", cb_dl_csv, font_size=9)

        # 速度滑块（靠右，标签在左滑块在右）
        speed_frame = tk.Frame(toolbar, bg=THEME['toolbar_bg'])
        speed_frame.pack(side=tk.RIGHT, padx=(0, 8))
        lbl_speed = tk.Label(speed_frame, text=t("toolbar.label.speed", self.lang), font=(self._tk_font_family, 10),
                 bg=THEME['toolbar_bg'])
        lbl_speed.pack(side=tk.LEFT, padx=(0, 4))
        self._reg("toolbar.label.speed", lbl_speed, font_size=10)
        self.speed_var = tk.IntVar(value=3)
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                    variable=self.speed_var, length=120,
                                    font=(self._tk_font_family, 9), bg=THEME['toolbar_bg'],
                                    highlightthickness=0)
        self.speed_scale.pack(side=tk.LEFT)

        # 帧进度条（P7-2）
        frame_frame = tk.Frame(toolbar, bg=THEME['toolbar_bg'])
        frame_frame.pack(side=tk.RIGHT, padx=(0, 8))
        lbl_frame = tk.Label(frame_frame, text=t("toolbar.label.frame", self.lang),
                              font=(self._tk_font_family, 10), bg=THEME['toolbar_bg'])
        lbl_frame.pack(side=tk.LEFT, padx=(0, 4))
        self._reg("toolbar.label.frame", lbl_frame, font_size=10)
        self.frame_var = tk.IntVar(value=0)
        self.frame_scale = tk.Scale(frame_frame, from_=0, to=359, orient=tk.HORIZONTAL,
                                     variable=self.frame_var, length=120,
                                     font=(self._tk_font_family, 9), bg=THEME['toolbar_bg'],
                                     highlightthickness=0, command=self._on_frame_seek)
        self.frame_scale.pack(side=tk.LEFT)

        # 状态/警告行
        status_bar = tk.Frame(main_area, bg=THEME['toolbar_bg'])
        status_bar.pack(fill=tk.X, padx=12, pady=(2, 0))

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(status_bar, textvariable=self.status_var, fg=THEME['status_fg'],
                                     font=(self._tk_font_family, 10), anchor='w', bg=THEME['toolbar_bg'])
        self.status_label.pack(side=tk.LEFT)

        self.alpha_var = tk.StringVar()
        self.alpha_label = tk.Label(status_bar, textvariable=self.alpha_var,
                                    font=(self._tk_font_family, 11, 'bold'), anchor='w', bg=THEME['toolbar_bg'])
        self.alpha_label.pack(side=tk.LEFT, padx=16)

        return toolbar, status_bar

    def _build_figure(self, main_area):
        """构建图表区域"""
        self.fig = Figure(figsize=(14, 7), dpi=100)

        gs = GridSpec(2, 4, figure=self.fig,
                      left=0.04, right=0.80, top=0.95, bottom=0.08,
                      wspace=0.30, hspace=0.35,
                      width_ratios=[1, 1, 1, 1.6])

        self.ax_s = self.fig.add_subplot(gs[0, 0])
        self.ax_v = self.fig.add_subplot(gs[0, 1])
        self.ax_alpha = self.fig.add_subplot(gs[0, 2])
        self.ax_a = self.fig.add_subplot(gs[1, 0])
        self.ax_profile = self.fig.add_subplot(gs[1, 1])
        self.ax_rho = self.fig.add_subplot(gs[1, 2])
        self.ax_anim = self.fig.add_subplot(gs[:, 3])

        # 信息面板：紧贴动态图右侧，上下对齐
        self.ax_info = self.fig.add_axes([0.83, 0.08, 0.14, 0.87])
        self.ax_info.set_xticks([])
        self.ax_info.set_yticks([])
        self.ax_info.set_frame_on(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=main_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # 窗口缩放自适应（P7-3）
        self.canvas.get_tk_widget().bind('<Configure>', self._on_canvas_resize)
        self._resize_after_id = None

    # ===================================================================
    # 侧边栏辅助
    # ===================================================================

    def _on_sidebar_configure(self, event):
        """侧边栏内容变化时更新滚动区域"""
        self._sb_canvas.configure(scrollregion=self._sb_canvas.bbox('all'))
        self._sb_canvas.itemconfig(self._sb_win, width=self._sb_canvas.winfo_width())

    def _on_mousewheel(self, event):
        """鼠标滚轮滚动侧边栏（跨平台）"""
        if platform.system() == 'Darwin':
            self._sb_canvas.yview_scroll(int(-1 * event.delta), 'units')
        elif platform.system() == 'Linux':
            self._sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        else:
            self._sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _bind_mousewheel(self, event):
        """绑定鼠标滚轮事件（跨平台）"""
        self._sb_canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        if platform.system() == 'Linux':
            self._sb_canvas.bind_all('<Button-4>', lambda e: self._sb_canvas.yview_scroll(-1, 'units'))
            self._sb_canvas.bind_all('<Button-5>', lambda e: self._sb_canvas.yview_scroll(1, 'units'))

    def _unbind_mousewheel(self, event):
        """解绑鼠标滚轮事件（跨平台）"""
        self._sb_canvas.unbind_all('<MouseWheel>')
        if platform.system() == 'Linux':
            self._sb_canvas.unbind_all('<Button-4>')
            self._sb_canvas.unbind_all('<Button-5>')

    def _refresh_sidebar(self):
        """强制刷新侧边栏显示"""
        self._sb_canvas.update_idletasks()
        self._sb_canvas.configure(scrollregion=self._sb_canvas.bbox('all'))
        self._sb_canvas.itemconfig(self._sb_win, width=self._sb_canvas.winfo_width())

    def _sidebar_group(self, parent, title, i18n_key=None):
        """侧边栏分组标题"""
        frame = tk.Frame(parent, bg=THEME['sidebar_bg'])
        frame.pack(fill=tk.X, padx=16, pady=(12, 4))
        lbl = tk.Label(frame, text=title, font=(self._tk_font_family, 9),
                 fg=THEME['group_fg'], bg=THEME['sidebar_bg'], anchor='w')
        lbl.pack(fill=tk.X)
        tk.Frame(frame, height=1, bg=THEME['separator']).pack(fill=tk.X, pady=(2, 0))
        if i18n_key:
            self._reg(i18n_key, lbl, font_size=9)

    def _sidebar_item(self, parent, text, lbl_kw, i18n_key=None):
        """侧边栏参数标签"""
        lbl = tk.Label(parent, text=text, **lbl_kw)
        lbl.pack(fill=tk.X, padx=16, pady=(4, 0))
        if i18n_key:
            self._reg(i18n_key, lbl, font_size=10)

    # ===================================================================
    # 参数读取与校验
    # ===================================================================

    def _read_params(self):
        """读取并校验参数，返回 dict 或 None"""
        try:
            raw_angles = {
                'delta_0': float(self.entry_delta_0.get()),
                'delta_01': float(self.entry_delta_01.get()),
                'delta_ret': float(self.entry_delta_ret.get()),
                'delta_02': float(self.entry_delta_02.get()),
            }
            vals = {
                'delta_0': int(raw_angles['delta_0']),
                'delta_01': int(raw_angles['delta_01']),
                'delta_ret': int(raw_angles['delta_ret']),
                'delta_02': int(raw_angles['delta_02']),
                'h': float(self.entry_h.get()),
                'r_0': float(self.entry_r0.get()),
                'e': float(self.entry_e.get()),
                'omega': float(self.entry_omega.get()),
                'r_r': float(self.entry_rr.get()),
                'n_points': int(float(self.entry_n_points.get())),
                'alpha_threshold': float(self.entry_alpha_threshold.get()),
            }
        except ValueError:
            self.status_var.set(t("status.incomplete_params", self.lang))
            return None

        # 检查角度浮点截断，提示用户
        truncation_warnings = []
        angle_names = {
            'delta_0': t("sidebar.label.delta_0", self.lang),
            'delta_01': t("sidebar.label.delta_01", self.lang),
            'delta_ret': t("sidebar.label.delta_ret", self.lang),
            'delta_02': t("sidebar.label.delta_02", self.lang),
        }
        for key, raw_val in raw_angles.items():
            int_val = int(raw_val)
            if abs(raw_val - int_val) > 1e-9:
                truncation_warnings.append(
                    t("status.angle_truncated", self.lang, name=angle_names[key], raw=raw_val, rounded=int_val)
                )

        ok, err = validate_params(
            vals['delta_0'], vals['delta_01'], vals['delta_ret'], vals['delta_02'],
            vals['h'], vals['r_0'], vals['e'], vals['omega']
        )
        if not ok:
            if isinstance(err, tuple):
                key, name_key = err
                name = t(name_key, self.lang)
                self.status_var.set(t(key, self.lang, name=name))
            else:
                self.status_var.set(t(err, self.lang))
            return None

        # 读取下拉菜单
        vals['tc_law'] = self.popup_tc.current() + 1
        vals['hc_law'] = self.popup_hc.current() + 1
        vals['sn'] = 1 if self.popup_sn.current() == 0 else -1
        vals['pz'] = 1 if self.popup_pz.current() == 0 else -1
        vals['e'] = abs(vals['e'])  # 偏距取正值，方向由 pz 控制

        # 显示截断提示（如有）
        if truncation_warnings:
            self.status_var.set(" | ".join(truncation_warnings))
        else:
            self.status_var.set("")
        self.alpha_var.set("")
        return vals

    # ===================================================================
    # 计算与启动
    # ===================================================================

    def _on_start(self):
        """开始仿真"""
        self._stop_animation()

        params = self._read_params()
        if params is None:
            return

        # 设置离散点数（P6-6: N_POINTS 可配置）
        n_points = params.get('n_points', 360)
        if n_points < 36:
            n_points = 36
        elif n_points > 3600:
            n_points = 3600
        cam_mechanics.N_POINTS = n_points

        # 压力角阈值（P6-5: 可配置）
        alpha_threshold = params.get('alpha_threshold', MAX_PRESSURE_ANGLE)
        if alpha_threshold <= 0:
            alpha_threshold = MAX_PRESSURE_ANGLE

        # 滚子半径
        r_r = params.get('r_r', 0)
        if r_r < 0:
            r_r = 0

        # 计算运动
        try:
            delta_deg, s, v, a, ds_ddelta, phase_bounds = compute_full_motion(
                params['delta_0'], params['delta_01'],
                params['delta_ret'], params['delta_02'],
                params['h'], params['r_0'], params['e'],
                params['omega'], params['tc_law'], params['hc_law']
            )

            # 计算凸轮廓形
            x, y, s_0 = compute_cam_profile(
                s, params['r_0'], params['e'], params['sn'], params['pz']
            )

            # 计算滚子实际廓形
            x_actual, y_actual = compute_roller_profile(x, y, r_r, params['sn'])

            # 计算曲率半径
            rho = compute_curvature_radius(x, y)
        except ValueError as exc:
            self.status_var.set(str(exc))
            return

        # 预计算基圆/偏距圆坐标
        delta_full = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        x_base = params['r_0'] * np.cos(delta_full)
        y_base = params['r_0'] * np.sin(delta_full)
        x_offset = x_base / params['r_0'] * params['e']
        y_offset = y_base / params['r_0'] * params['e']

        # 预计算 Rmax
        R = np.hypot(x, y)
        Rmax = np.max(R)

        # 解析压力角
        alpha_all = compute_pressure_angle(s, ds_ddelta, s_0, params['e'], params['pz'])
        max_alpha = np.max(np.abs(alpha_all))

        # 警告累积显示
        warnings = []
        if max_alpha > alpha_threshold:
            warnings.append(t("status.warning_max_alpha", self.lang, val=max_alpha, threshold=alpha_threshold))
        if params['h'] > params['r_0']:
            warnings.append(t("status.warning_h_gt_r0", self.lang, h=params['h'], r0=params['r_0']))
        # 曲率半径干涉警告
        rho_finite = rho[np.isfinite(rho)]
        if len(rho_finite) > 0 and r_r > 0:
            min_rho = np.min(rho_finite)
            if min_rho < r_r:
                warnings.append(t("status.warning_min_curvature", self.lang, val=min_rho, r_r=r_r))
        if warnings:
            self.status_var.set(" | ".join(warnings))

        # 保存计算结果（加锁保护，防止 GIF 导出线程并发读取不一致）
        with self._sim_data_lock:
            self.sim_data = {
                'delta_deg': delta_deg, 's': s, 'v': v, 'a': a,
                'ds_ddelta': ds_ddelta, 'phase_bounds': phase_bounds,
                'x': x, 'y': y, 's_0': s_0,
                'r_0': params['r_0'], 'e': params['e'], 'h': params['h'],
                'omega': params['omega'], 'sn': params['sn'], 'pz': params['pz'],
                'tc_law': params['tc_law'], 'hc_law': params['hc_law'],
                'x_base': x_base, 'y_base': y_base,
                'x_offset': x_offset, 'y_offset': y_offset,
                'Rmax': Rmax, 'max_alpha': max_alpha,
                'alpha_all': alpha_all,
                'r_r': r_r, 'x_actual': x_actual, 'y_actual': y_actual,
                'rho': rho, 'alpha_threshold': alpha_threshold,
                'n_points': n_points,
            }
            # 标记最小曲率半径位置
            rho_finite = rho[np.isfinite(rho)]
            if len(rho_finite) > 0:
                self.sim_data['min_rho_idx'] = int(np.argmin(np.abs(rho_finite)))
            else:
                self.sim_data['min_rho_idx'] = 0

        # 绘制静态图
        self._plot_static()

        # 开始动画
        self._start_animation()

    # ===================================================================
    # 静态图表（委托给 ui.plots 模块）
    # ===================================================================

    def _draw_displacement_curve(self, ax, data, show_law_names=False):
        draw_displacement_curve(ax, data, self.lang, show_law_names)

    def _draw_velocity_curve(self, ax, data):
        draw_velocity_curve(ax, data, self.lang)

    def _draw_acceleration_curve(self, ax, data):
        draw_acceleration_curve(ax, data, self.lang)

    def _draw_profile_plot(self, ax, data):
        draw_profile_plot(ax, data, self.lang)

    def _draw_pressure_angle_curve(self, ax, data):
        draw_pressure_angle_curve(ax, data, self.lang)

    def _draw_curvature_radius_curve(self, ax, data):
        draw_curvature_radius_curve(ax, data, self.lang)

    def _plot_static(self):
        """绘制静态图表"""
        data = self.sim_data

        for ax in [self.ax_s, self.ax_v, self.ax_a,
                   self.ax_alpha, self.ax_profile, self.ax_rho]:
            ax.clear()

        self._draw_displacement_curve(self.ax_s, data, show_law_names=True)
        self._draw_velocity_curve(self.ax_v, data)
        self._draw_pressure_angle_curve(self.ax_alpha, data)
        self._draw_acceleration_curve(self.ax_a, data)
        self._draw_profile_plot(self.ax_profile, data)
        self._draw_curvature_radius_curve(self.ax_rho, data)

        self.canvas.draw()

    # ===================================================================
    # 动画
    # ===================================================================

    def _init_anim_artists(self):
        """初始化动画图形对象（只创建一次，后续用 set_data 更新）"""
        ax = self.ax_anim
        ax.clear()

        data = self.sim_data
        r_0 = data['r_0']
        h = data['h']
        Rmax = data['Rmax']

        line_cam, = ax.plot([], [], 'r-', linewidth=2)
        line_base, = ax.plot([], [], 'm-', linewidth=1)
        line_offset, = ax.plot([], [], 'c-', linewidth=1)
        line_tangent, = ax.plot([], [], 'm-', linewidth=1)
        line_normal, = ax.plot([], [], 'm-', linewidth=1)
        line_rod, = ax.plot([], [], 'k-', linewidth=3, solid_capstyle='butt')
        line_tip, = ax.plot([], [], 'k-', linewidth=2)
        line_center, = ax.plot([], [], 'k--', linewidth=0.8)
        line_lower, = ax.plot([], [], 'c-.', linewidth=1)
        line_upper, = ax.plot([], [], 'm--', linewidth=1)
        lines_boundary = []
        for _ in range(4):
            lb, = ax.plot([], [], 'k-', linewidth=0.8)
            lines_boundary.append(lb)
        line_arc, = ax.plot([], [], 'k-', linewidth=1)

        ax.set_xlim(-Rmax - h, Rmax + h)
        ax.set_ylim(-Rmax - r_0, Rmax + r_0)
        ax.set_aspect('equal')
        ax.grid(self.show_grid.get())
        ax.set_title(t("plot.title.animation", self.lang), fontsize=12)
        ax.set_xlabel(r'$x$ (mm)')
        ax.set_ylabel(r'$y$ (mm)')

        draw_fixed_support(ax, r_0)

        anim_pos = ax.get_position()
        info_x0 = anim_pos.x1 + 0.01
        info_w = 0.14
        self.ax_info.set_position([info_x0, anim_pos.y0, info_w, anim_pos.y1 - anim_pos.y0])
        self._init_info_panel()

        self._anim_artists = {
            'cam': line_cam, 'base': line_base, 'offset': line_offset,
            'tangent': line_tangent, 'normal': line_normal,
            'rod': line_rod, 'tip': line_tip, 'center': line_center,
            'lower': line_lower, 'upper': line_upper,
            'boundaries': lines_boundary, 'arc': line_arc,
        }

    def _init_info_panel(self):
        """初始化信息面板"""
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

        info_items = [
            ('delta', t("info.label.delta", self.lang)),
            ('alpha', t("info.label.alpha", self.lang)),
            ('s',     t("info.label.s", self.lang)),
            ('h',     t("info.label.h", self.lang)),
            ('s0',    t("info.label.s0", self.lang)),
        ]
        self._info_labels = {}
        for idx, (key, name) in enumerate(info_items):
            y_pos = 0.95 - idx * 0.10
            lbl = ax.text(0.05, y_pos, f'{name}: --', transform=ax.transAxes,
                          fontsize=10, ha='left', va='top', color=THEME['info_text'])
            self._info_labels[key] = lbl

    def _start_animation(self):
        """开始凸轮旋转动画"""
        self.animating = True
        self.paused = False
        self.current_frame = 0
        self.btn_pause.config(text=t("toolbar.btn.pause", self.lang))
        self._pause_state = "paused"
        self._init_anim_artists()
        # 设置帧进度条范围
        if self.sim_data is not None:
            n = len(self.sim_data['s'])
            self.frame_scale.config(to=n - 1)
        self._animate_frame()

    def _stop_animation(self):
        """停止动画"""
        self.animating = False
        self.paused = False
        if self.anim_id is not None:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self._anim_artists = None

    def _on_pause(self):
        """暂停/继续/重播"""
        if self.animating:
            self.paused = not self.paused
            if self.paused:
                self.btn_pause.config(text=t("toolbar.btn.resume", self.lang))
                self._pause_state = "paused_running"
            else:
                self.btn_pause.config(text=t("toolbar.btn.pause", self.lang))
                self._pause_state = "paused"
                self._animate_frame()
        elif self.sim_data is not None and self._pause_state == "replay":
            self._start_animation()

    def _animate_frame(self):
        """绘制一帧动画"""
        if not self.animating or self.paused:
            return

        data = self.sim_data
        artists = self._anim_artists
        if artists is None:
            return

        r_0 = data['r_0']
        h = data['h']
        sn = data['sn']
        pb = data['phase_bounds']
        s = data['s']
        s_0 = data['s_0']
        e = data['e']
        pz = data['pz']
        alpha_all = data['alpha_all']

        N = len(s)
        i = self.current_frame

        if i >= N:
            self.animating = False
            self.btn_pause.config(text=t("toolbar.btn.replay", self.lang))
            self._pause_state = "replay"
            self.alpha_var.set(t("status.max_alpha", self.lang, val=data['max_alpha']))
            label_delta = t("info.label.delta", self.lang)
            label_alpha = t("info.label.alpha", self.lang)
            label_s = t("info.label.s", self.lang)
            label_h = t("info.label.h", self.lang)
            label_s0 = t("info.label.s0", self.lang)
            self._info_labels['delta'].set_text(rf'{label_delta}: 360°/360°')
            self._info_labels['alpha'].set_text(rf'{label_alpha}: {data["max_alpha"]:.2f}°')
            self._info_labels['s'].set_text(rf'{label_s}: 0.00 mm')
            self._info_labels['h'].set_text(rf'{label_h}: {h:.1f} mm')
            self._info_labels['s0'].set_text(rf'{label_s0}: {s_0:.2f} mm')
            self.canvas.draw_idle()
            return

        angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
        x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)
        artists['cam'].set_data(x_rot, y_rot)

        if self.show_base_circle.get():
            artists['base'].set_data(data['x_base'], data['y_base'])
        else:
            artists['base'].set_data([], [])

        if self.show_offset_circle.get():
            artists['offset'].set_data(data['x_offset'], data['y_offset'])
        else:
            artists['offset'].set_data([], [])

        frame = compute_anim_frame_data(s, data['ds_ddelta'], s_0, e, r_0, sn, pz, i, alpha_all)
        follower_x = frame['follower_x']
        cy = frame['contact_y']
        cx = follower_x
        nx, ny = frame['nx'], frame['ny']
        tx, ty = frame['tx'], frame['ty']
        alpha_i = frame['alpha_i']

        if self.show_tangent.get():
            artists['tangent'].set_data([cx - r_0 * tx, cx + r_0 * tx], [cy - r_0 * ty, cy + r_0 * ty])
        else:
            artists['tangent'].set_data([], [])

        if self.show_normal.get():
            artists['normal'].set_data([cx + r_0 * nx, cx - r_0 * nx], [cy + r_0 * ny, cy - r_0 * ny])
        else:
            artists['normal'].set_data([], [])

        tip_w = r_0 * TIP_WIDTH_RATIO
        tip_h = r_0 * TIP_HEIGHT_RATIO
        rod_top = cy + r_0 * ROD_LENGTH_RATIO
        artists['rod'].set_data([follower_x, follower_x], [cy + tip_h, rod_top])
        artists['tip'].set_data([follower_x - tip_w, follower_x, follower_x + tip_w, follower_x - tip_w], [cy + tip_h, cy, cy + tip_h, cy + tip_h])

        if self.show_limits.get():
            artists['lower'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0])
            artists['upper'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h])
        else:
            artists['lower'].set_data([], [])
            artists['upper'].set_data([], [])

        if self.show_boundaries.get():
            for j, lb in enumerate(artists['boundaries']):
                if j < len(pb) - 1:
                    b_deg = pb[j + 1]
                    idx = int(b_deg)
                    if idx < N:
                        lb.set_data([0, x_rot[idx]], [0, y_rot[idx]])
                    else:
                        lb.set_data([], [])
                else:
                    lb.set_data([], [])
        else:
            for lb in artists['boundaries']:
                lb.set_data([], [])

        if self.show_arc.get():
            arc_r = r_0 * ARC_RADIUS_RATIO
            x_arc, y_arc = compute_pressure_angle_arc(cx, cy, nx, ny, alpha_i, arc_r)
            artists['arc'].set_data(x_arc, y_arc)
            artists['center'].set_data([follower_x, follower_x], [cy - r_0 * 2, cy + r_0 * 5])
        else:
            artists['arc'].set_data([], [])
            artists['center'].set_data([], [])

        label_delta = t("info.label.delta", self.lang)
        label_alpha = t("info.label.alpha", self.lang)
        label_s = t("info.label.s", self.lang)
        label_h = t("info.label.h", self.lang)
        label_s0 = t("info.label.s0", self.lang)
        self._info_labels['delta'].set_text(rf'{label_delta}: {i:3d}°/360°')
        self._info_labels['alpha'].set_text(rf'{label_alpha}: {alpha_i:.1f}°')
        self._info_labels['s'].set_text(rf'{label_s}: {frame["s_i"]:.2f} mm')
        self._info_labels['h'].set_text(rf'{label_h}: {h:.1f} mm')
        self._info_labels['s0'].set_text(rf'{label_s0}: {s_0:.2f} mm')

        if i % ANIM_FRAME_SKIP == 0:
            self.canvas.draw_idle()

        # 同步帧进度条
        self.frame_var.set(i)

        self.current_frame += 1
        delay = max(ANIM_MIN_DELAY_MS, int(ANIM_BASE_DELAY_MS / (self.speed_var.get() ** 1.5)))
        self.anim_id = self.root.after(delay, self._animate_frame)

    def _draw_single_frame(self, i):
        """绘制指定帧（用于帧进度条拖动跳转）"""
        data = self.sim_data
        if data is None:
            return
        if self._anim_artists is None:
            self._init_anim_artists()
        artists = self._anim_artists
        r_0 = data['r_0']
        h = data['h']
        sn = data['sn']
        pb = data['phase_bounds']
        s = data['s']
        s_0 = data['s_0']
        e = data['e']
        pz = data['pz']
        alpha_all = data['alpha_all']
        N = len(s)
        if i < 0 or i >= N:
            return

        angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
        x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)
        artists['cam'].set_data(x_rot, y_rot)

        if self.show_base_circle.get():
            artists['base'].set_data(data['x_base'], data['y_base'])
        else:
            artists['base'].set_data([], [])
        if self.show_offset_circle.get():
            artists['offset'].set_data(data['x_offset'], data['y_offset'])
        else:
            artists['offset'].set_data([], [])

        frame = compute_anim_frame_data(s, data['ds_ddelta'], s_0, e, r_0, sn, pz, i, alpha_all)
        follower_x = frame['follower_x']
        cy = frame['contact_y']
        cx = follower_x
        nx, ny = frame['nx'], frame['ny']
        tx, ty = frame['tx'], frame['ty']
        alpha_i = frame['alpha_i']

        if self.show_tangent.get():
            artists['tangent'].set_data([cx - r_0 * tx, cx + r_0 * tx], [cy - r_0 * ty, cy + r_0 * ty])
        else:
            artists['tangent'].set_data([], [])
        if self.show_normal.get():
            artists['normal'].set_data([cx + r_0 * nx, cx - r_0 * nx], [cy + r_0 * ny, cy - r_0 * ny])
        else:
            artists['normal'].set_data([], [])

        tip_w = r_0 * TIP_WIDTH_RATIO
        tip_h = r_0 * TIP_HEIGHT_RATIO
        rod_top = cy + r_0 * ROD_LENGTH_RATIO
        artists['rod'].set_data([follower_x, follower_x], [cy + tip_h, rod_top])
        artists['tip'].set_data([follower_x - tip_w, follower_x, follower_x + tip_w, follower_x - tip_w],
                                [cy + tip_h, cy, cy + tip_h, cy + tip_h])

        if self.show_limits.get():
            artists['lower'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0])
            artists['upper'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h])
        else:
            artists['lower'].set_data([], [])
            artists['upper'].set_data([], [])

        if self.show_boundaries.get():
            for j, lb in enumerate(artists['boundaries']):
                if j < len(pb) - 1:
                    b_deg = pb[j + 1]
                    idx = int(b_deg)
                    if idx < N:
                        lb.set_data([0, x_rot[idx]], [0, y_rot[idx]])
                    else:
                        lb.set_data([], [])
                else:
                    lb.set_data([], [])
        else:
            for lb in artists['boundaries']:
                lb.set_data([], [])

        if self.show_arc.get():
            arc_r = r_0 * ARC_RADIUS_RATIO
            x_arc, y_arc = compute_pressure_angle_arc(cx, cy, nx, ny, alpha_i, arc_r)
            artists['arc'].set_data(x_arc, y_arc)
            artists['center'].set_data([follower_x, follower_x], [cy - r_0 * 2, cy + r_0 * 5])
        else:
            artists['arc'].set_data([], [])
            artists['center'].set_data([], [])

        # 更新信息面板
        label_delta = t("info.label.delta", self.lang)
        label_alpha = t("info.label.alpha", self.lang)
        label_s = t("info.label.s", self.lang)
        label_h = t("info.label.h", self.lang)
        label_s0 = t("info.label.s0", self.lang)
        self._info_labels['delta'].set_text(rf'{label_delta}: {i:3d}°/360°')
        self._info_labels['alpha'].set_text(rf'{label_alpha}: {alpha_i:.1f}°')
        self._info_labels['s'].set_text(rf'{label_s}: {frame["s_i"]:.2f} mm')
        self._info_labels['h'].set_text(rf'{label_h}: {h:.1f} mm')
        self._info_labels['s0'].set_text(rf'{label_s0}: {s_0:.2f} mm')

        self.canvas.draw_idle()

    # ===================================================================
    # 按钮回调
    # ===================================================================

    def _on_arc_toggle(self):
        if self.show_arc.get():
            self.show_normal.set(True)
        else:
            self.show_normal.set(False)
            if self._anim_artists:
                self._anim_artists['arc'].set_data([], [])
                self._anim_artists['normal'].set_data([], [])
                self._anim_artists['center'].set_data([], [])
                self.canvas.draw_idle()

    def _on_grid_toggle(self):
        self.ax_anim.grid(self.show_grid.get())
        self.canvas.draw_idle()

    def _on_canvas_resize(self, event):
        """窗口缩放时自适应调整图表（防抖）"""
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(200, self._do_canvas_resize)

    def _do_canvas_resize(self):
        """执行图表缩放调整"""
        self._resize_after_id = None
        try:
            self.canvas.draw_idle()
        except Exception:
            pass

    def _on_frame_seek(self, value):
        """拖动帧进度条跳转到指定帧"""
        if not self.animating and self.sim_data is not None:
            # 动画未运行时，允许拖动查看任意帧
            self.current_frame = int(value)
            self._draw_single_frame(self.current_frame)

    def _validate_entry(self, entry, conv_type):
        """实时校验输入框（FocusOut 时检查数值有效性）"""
        try:
            val = entry.get().strip()
            if val:
                conv_type(val)
            # 输入有效，恢复正常背景
            entry.config(bg='white')
        except ValueError:
            # 输入无效，高亮提示
            entry.config(bg='#fecaca')

    def _on_download(self):
        """下载勾选的图片"""
        if not any([self.dl_s.get(), self.dl_v.get(), self.dl_a.get(),
                     self.dl_profile.get(), self.dl_anim.get(), self.dl_excel.get(),
                     self.dl_alpha.get(), self.dl_curvature.get(),
                     self.dl_svg.get(), self.dl_csv.get()]):
            self.status_var.set(t("status.no_download_selection", self.lang))
            return

        if self.sim_data is None:
            self.status_var.set(t("status.run_first", self.lang))
            return

        folder = filedialog.askdirectory(title=t("export.folder_dialog.title", self.lang))
        if not folder:
            return

        dpi = STATIC_DPI
        saved = []
        data = self.sim_data
        errors = []

        if self.dl_s.get():
            try:
                fig_s = Figure(figsize=(6, 4), dpi=dpi)
                ax_s = fig_s.add_subplot(111)
                self._draw_displacement_curve(ax_s, data)
                filename_s = t("export.filename.displacement", self.lang) + ".tiff"
                fig_s.savefig(os.path.join(folder, filename_s), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_s)
                saved.append(filename_s)
            except Exception as exc:
                errors.append(f"displacement: {exc}")

        if self.dl_v.get():
            try:
                fig_v = Figure(figsize=(6, 4), dpi=dpi)
                ax_v = fig_v.add_subplot(111)
                self._draw_velocity_curve(ax_v, data)
                filename_v = t("export.filename.velocity", self.lang) + ".tiff"
                fig_v.savefig(os.path.join(folder, filename_v), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_v)
                saved.append(filename_v)
            except Exception as exc:
                errors.append(f"velocity: {exc}")

        if self.dl_a.get():
            try:
                fig_a = Figure(figsize=(6, 4), dpi=dpi)
                ax_a = fig_a.add_subplot(111)
                self._draw_acceleration_curve(ax_a, data)
                filename_a = t("export.filename.acceleration", self.lang) + ".tiff"
                fig_a.savefig(os.path.join(folder, filename_a), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_a)
                saved.append(filename_a)
            except Exception as exc:
                errors.append(f"acceleration: {exc}")

        if self.dl_profile.get():
            try:
                fig_p = Figure(figsize=(6, 6), dpi=dpi)
                ax_p = fig_p.add_subplot(111)
                self._draw_profile_plot(ax_p, data)
                filename_p = t("export.filename.profile", self.lang) + ".tiff"
                fig_p.savefig(os.path.join(folder, filename_p), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_p)
                saved.append(filename_p)
            except Exception as exc:
                errors.append(f"profile: {exc}")

        if self.dl_alpha.get():
            try:
                fig_alpha = Figure(figsize=(6, 4), dpi=dpi)
                ax_alpha = fig_alpha.add_subplot(111)
                self._draw_pressure_angle_curve(ax_alpha, data)
                filename_alpha = t("export.filename.pressure_angle", self.lang) + ".tiff"
                fig_alpha.savefig(os.path.join(folder, filename_alpha), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_alpha)
                saved.append(filename_alpha)
            except Exception as exc:
                errors.append(f"pressure_angle: {exc}")

        if self.dl_curvature.get():
            try:
                fig_rho = Figure(figsize=(6, 4), dpi=dpi)
                ax_rho = fig_rho.add_subplot(111)
                self._draw_curvature_radius_curve(ax_rho, data)
                filename_rho = t("export.filename.curvature", self.lang) + ".tiff"
                fig_rho.savefig(os.path.join(folder, filename_rho), dpi=dpi, bbox_inches='tight', format='tiff')
                plt.close(fig_rho)
                saved.append(filename_rho)
            except Exception as exc:
                errors.append(f"curvature: {exc}")

        # SVG 矢量图导出（P7-5）
        if self.dl_svg.get():
            try:
                fig_svg = Figure(figsize=(14, 7), dpi=100)
                gs_svg = GridSpec(2, 2, figure=fig_svg, wspace=0.30, hspace=0.35)
                ax_s_svg = fig_svg.add_subplot(gs_svg[0, 0])
                ax_v_svg = fig_svg.add_subplot(gs_svg[0, 1])
                ax_a_svg = fig_svg.add_subplot(gs_svg[1, 0])
                ax_p_svg = fig_svg.add_subplot(gs_svg[1, 1])
                self._draw_displacement_curve(ax_s_svg, data)
                self._draw_velocity_curve(ax_v_svg, data)
                self._draw_acceleration_curve(ax_a_svg, data)
                self._draw_profile_plot(ax_p_svg, data)
                filename_svg = "camforge_all.svg"
                fig_svg.savefig(os.path.join(folder, filename_svg), format='svg', bbox_inches='tight')
                plt.close(fig_svg)
                saved.append(filename_svg)
            except Exception as exc:
                errors.append(f"svg: {exc}")

        # CSV 数据表导出（P7-5）
        if self.dl_csv.get():
            try:
                import csv as csv_mod
                filename_csv = "camforge_data.csv"
                filepath_csv = os.path.join(folder, filename_csv)
                delta_deg = data['delta_deg']
                s_arr = data['s']
                v_arr = data['v']
                a_arr = data['a']
                x_arr = data['x']
                y_arr = data['y']
                R_arr = np.hypot(x_arr, y_arr)
                alpha_arr = data['alpha_all']
                with open(filepath_csv, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv_mod.writer(f)
                    writer.writerow(['delta_deg', 's_mm', 'v_mm_s', 'a_mm_s2',
                                     'x_mm', 'y_mm', 'R_mm', 'alpha_deg'])
                    for i in range(len(delta_deg)):
                        writer.writerow([
                            round(delta_deg[i], 2), round(s_arr[i], 4),
                            round(v_arr[i], 4), round(a_arr[i], 4),
                            round(x_arr[i], 4), round(y_arr[i], 4),
                            round(R_arr[i], 4), round(alpha_arr[i], 4),
                        ])
                saved.append(filename_csv)
            except Exception as exc:
                errors.append(f"csv: {exc}")

        if self.dl_excel.get():
            self._export_excel(folder, saved)

        if self.dl_anim.get():
            filename_anim = t("export.filename.animation", self.lang) + ".gif"
            filepath = os.path.join(folder, filename_anim)
            self._export_gif(filepath, folder, saved)

        if saved:
            self.status_var.set(t("status.saved", self.lang, files=', '.join(saved), folder=folder))
        elif self.dl_anim.get():
            self.status_var.set(t("status.gif_exporting", self.lang))
        if errors:
            self.status_var.set(t("status.export_failed", self.lang, error='; '.join(errors)))

    def _export_excel(self, folder, saved_list):
        """导出凸轮数据为 Excel 表格"""
        if openpyxl is None:
            self.status_var.set(t("error.openpyxl_missing", self.lang))
            return

        try:
            data = self.sim_data
            delta_deg = data['delta_deg']
            v = data['v']
            a = data['a']
            x = data['x']
            y = data['y']
            R = np.hypot(x, y)

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = t("excel.sheet_name", self.lang)

            headers = [
                t("excel.col.delta", self.lang),
                t("excel.col.radius", self.lang),
                t("excel.col.velocity", self.lang),
                t("excel.col.acceleration", self.lang),
            ]
            ws.append(headers)

            for i in range(len(delta_deg)):
                ws.append([round(delta_deg[i], 1), round(R[i], 4), round(v[i], 4), round(a[i], 4)])

            for col in range(1, 5):
                max_len = len(str(ws.cell(row=1, column=col).value))
                for row in range(2, min(10, len(delta_deg) + 2)):
                    cell_len = len(str(ws.cell(row=row, column=col).value))
                    if cell_len > max_len:
                        max_len = cell_len
                ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max_len + 4

            filename = t("export.filename.excel", self.lang) + ".xlsx"
            filepath = os.path.join(folder, filename)
            wb.save(filepath)
            saved_list.append(filename)
        except Exception as exc:
            self.status_var.set(t("status.export_failed", self.lang, error=str(exc)))

    def _export_gif(self, filepath, folder, saved_list):
        """在后台线程中导出GIF动画"""
        if PILImage is None:
            self.status_var.set(t("status.gif_failed", self.lang, error="Pillow not installed"))
            return

        lang = self.lang
        show_base = self.show_base_circle.get()
        show_offset = self.show_offset_circle.get()
        show_limits = self.show_limits.get()
        show_tangent_gif = self.show_tangent.get()
        show_normal_gif = self.show_normal.get()
        show_arc_gif = self.show_arc.get()
        show_boundaries_gif = self.show_boundaries.get()

        with self._sim_data_lock:
            data = self.sim_data
            if data is None:
                return
            s = data['s'].copy()
            ds_ddelta = data['ds_ddelta'].copy()
            alpha_all = data['alpha_all'].copy()
            x_cam = data['x'].copy()
            y_cam = data['y'].copy()
            x_base = data['x_base'].copy()
            y_base = data['y_base'].copy()
            x_offset = data['x_offset'].copy()
            y_offset = data['y_offset'].copy()
            s_0 = data['s_0']
            e = data['e']
            r_0 = data['r_0']
            h = data['h']
            sn = data['sn']
            pz = data['pz']
            pb = list(data['phase_bounds'])
            Rmax = data['Rmax']
            max_alpha = data['max_alpha']
            delta_deg = data['delta_deg'].copy()
            v_arr = data['v'].copy()
            a_arr = data['a'].copy()
            tc_law = data['tc_law']
            hc_law = data['hc_law']
        N = len(s)
        xlim = self.ax_anim.get_xlim()
        ylim = self.ax_anim.get_ylim()

        progress_win = tk.Toplevel(self.root)
        progress_win.title(t("export.gif_dialog.title", lang))
        progress_win.geometry("320x100")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        progress_win.grab_set()
        tk.Label(progress_win, text=t("export.gif_dialog.message", lang),
                 font=(self._tk_font_family, 10)).pack(pady=(12, 4))
        progress_bar = ttk.Progressbar(progress_win, length=280, mode='determinate', maximum=N)
        progress_bar.pack(pady=4)
        progress_label = tk.Label(progress_win, text="0 / 360", font=(self._tk_font_family, 9))
        progress_label.pack()

        gif_result = {'error': None}

        def generate():
            try:
                fig_gif = Figure(figsize=(8, 6), dpi=GIF_DPI)
                ax_gif = fig_gif.add_axes([0.05, 0.08, 0.65, 0.87])
                ax_info_gif = fig_gif.add_axes([0.73, 0.08, 0.25, 0.87])

                label_delta_gif = t("info.label.delta", lang)
                label_alpha_gif = t("info.label.alpha", lang)
                label_s_gif = t("info.label.s", lang)
                label_h_gif = t("info.label.h", lang)
                label_s0_gif = t("info.label.s0", lang)
                title_anim_gif = t("plot.title.animation", lang)

                frame_images = []

                for i in range(N):
                    angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
                    x_rot, y_rot = compute_rotated_cam(x_cam, y_cam, angle_rad)

                    ax_gif.clear()
                    ax_gif.plot(x_rot, y_rot, 'r-', linewidth=2)
                    if show_base:
                        ax_gif.plot(x_base, y_base, 'm-', linewidth=1)
                    if show_offset:
                        ax_gif.plot(x_offset, y_offset, 'c-', linewidth=1)

                    frame_data = compute_anim_frame_data(s, ds_ddelta, s_0, e, r_0, sn, pz, i, alpha_all)
                    fx = frame_data['follower_x']
                    cy = frame_data['contact_y']
                    alpha_i = frame_data['alpha_i']
                    nx_i, ny_i = frame_data['nx'], frame_data['ny']
                    tx_i, ty_i = frame_data['tx'], frame_data['ty']
                    tip_w = r_0 * TIP_WIDTH_RATIO
                    tip_h = r_0 * TIP_HEIGHT_RATIO
                    ax_gif.plot([fx, fx], [cy + tip_h, cy + r_0 * ROD_LENGTH_RATIO], 'k-', linewidth=3)
                    ax_gif.plot([fx - tip_w, fx, fx + tip_w, fx - tip_w], [cy + tip_h, cy, cy + tip_h, cy + tip_h], 'k-', linewidth=2)
                    if show_limits:
                        ax_gif.plot([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0], 'c-.', linewidth=1)
                        ax_gif.plot([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h], 'm--', linewidth=1)
                    if show_tangent_gif:
                        ax_gif.plot([fx - r_0 * tx_i, fx + r_0 * tx_i], [cy - r_0 * ty_i, cy + r_0 * ty_i], 'm-', linewidth=1)
                    if show_normal_gif:
                        ax_gif.plot([fx + r_0 * nx_i, fx - r_0 * nx_i], [cy + r_0 * ny_i, cy - r_0 * ny_i], 'm-', linewidth=1)
                    if show_boundaries_gif:
                        for j_b in range(len(pb) - 1):
                            idx_b = int(pb[j_b + 1])
                            if idx_b < N:
                                ax_gif.plot([0, x_rot[idx_b]], [0, y_rot[idx_b]], 'k-', linewidth=0.8)
                    if show_arc_gif:
                        arc_r = r_0 * ARC_RADIUS_RATIO
                        x_arc, y_arc = compute_pressure_angle_arc(fx, cy, nx_i, ny_i, alpha_i, arc_r)
                        ax_gif.plot(x_arc, y_arc, 'k-', linewidth=1)
                        ax_gif.plot([fx, fx], [cy - r_0 * 2, cy + r_0 * 5], 'k--', linewidth=0.8)
                    draw_fixed_support(ax_gif, r_0)
                    ax_gif.set_xlim(xlim)
                    ax_gif.set_ylim(ylim)
                    ax_gif.set_aspect('equal')
                    ax_gif.set_title(f'{title_anim_gif}  {i:3d}°/360°', fontsize=11)

                    ax_info_gif.clear()
                    ax_info_gif.set_xticks([])
                    ax_info_gif.set_yticks([])
                    ax_info_gif.set_frame_on(False)
                    info_items = [
                        (0.95, rf'{label_delta_gif}: {i:3d}°/360°'),
                        (0.85, rf'{label_alpha_gif}: {alpha_i:.1f}°'),
                        (0.75, rf'{label_s_gif}: {frame_data["s_i"]:.2f} mm'),
                        (0.65, rf'{label_h_gif}: {h:.1f} mm'),
                        (0.55, rf'{label_s0_gif}: {s_0:.2f} mm'),
                    ]
                    for y_pos, text in info_items:
                        ax_info_gif.text(0.05, y_pos, text, transform=ax_info_gif.transAxes,
                                         fontsize=10, ha='left', va='top', color=THEME['info_text'])

                    buf = BytesIO()
                    fig_gif.savefig(buf, format='png', dpi=GIF_DPI)
                    buf.seek(0)
                    img = PILImage.open(buf).copy()
                    buf.close()
                    frame_images.append(img)

                    self.root.after(0, lambda idx=i: (
                        progress_bar.configure(value=idx + 1),
                        progress_label.configure(text=f"{idx + 1} / {N}")
                    ))

                plt.close(fig_gif)
                self.root.after(0, lambda: progress_label.configure(text=t("status.gif_composing", lang)))
                if frame_images:
                    frame_images[0].save(filepath, save_all=True, append_images=frame_images[1:],
                                         duration=GIF_DURATION_MS, loop=0, optimize=True)
                saved_list.append(os.path.basename(filepath))
            except Exception as exc:
                gif_result['error'] = str(exc)
            finally:
                def _on_done():
                    progress_win.destroy()
                    if gif_result['error']:
                        self.status_var.set(t("status.gif_failed", lang, error=gif_result['error']))
                    else:
                        self.status_var.set(t("status.saved", lang, files=', '.join(saved_list), folder=folder))
                self.root.after(0, _on_done)

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def _on_clear_params(self):
        """清除参数并恢复默认值"""
        defaults = {
            self.entry_delta_0: str(DEFAULT_PARAMS['delta_0']),
            self.entry_delta_01: str(DEFAULT_PARAMS['delta_01']),
            self.entry_delta_ret: str(DEFAULT_PARAMS['delta_ret']),
            self.entry_delta_02: str(DEFAULT_PARAMS['delta_02']),
            self.entry_h: str(DEFAULT_PARAMS['h']),
            self.entry_omega: str(DEFAULT_PARAMS['omega']),
            self.entry_r0: str(DEFAULT_PARAMS['r_0']),
            self.entry_e: str(DEFAULT_PARAMS['e']),
            self.entry_rr: str(DEFAULT_PARAMS['r_r']),
            self.entry_n_points: str(DEFAULT_PARAMS['n_points']),
            self.entry_alpha_threshold: str(DEFAULT_PARAMS['alpha_threshold']),
        }
        for entry, val in defaults.items():
            entry.delete(0, tk.END)
            entry.insert(0, val)
        self.popup_tc.current(0)
        self.popup_hc.current(0)
        self.popup_sn.current(0)
        self.popup_pz.current(0)
        self.status_var.set("")
        self.alpha_var.set("")

    def _on_clear_plots(self):
        """清除图像"""
        self._stop_animation()
        for ax in [self.ax_s, self.ax_v, self.ax_a,
                   self.ax_alpha, self.ax_profile, self.ax_rho,
                   self.ax_anim, self.ax_info]:
            ax.clear()
        self.canvas.draw()

    def _on_random(self):
        """随机凸轮参数"""
        params = generate_random_params()
        for entry in [self.entry_delta_0, self.entry_delta_01,
                      self.entry_delta_ret, self.entry_delta_02,
                      self.entry_h, self.entry_r0, self.entry_e,
                      self.entry_omega]:
            entry.delete(0, tk.END)

        self.entry_delta_0.insert(0, str(params['delta_0']))
        self.entry_delta_01.insert(0, str(params['delta_01']))
        self.entry_delta_ret.insert(0, str(params['delta_ret']))
        self.entry_delta_02.insert(0, str(params['delta_02']))
        self.entry_h.insert(0, str(params['h']))
        self.entry_r0.insert(0, str(params['r_0']))
        self.entry_e.insert(0, str(params['e']))
        self.entry_omega.insert(0, str(params['omega']))

        self.popup_tc.current(params['tc_law'] - 1)
        self.popup_hc.current(params['hc_law'] - 1)
        self.popup_sn.current(0 if params['sn'] == 1 else 1)
        self.popup_pz.current(0 if params['pz'] == 1 else 1)

        # 新参数保持默认值
        self.entry_rr.delete(0, tk.END)
        self.entry_rr.insert(0, str(DEFAULT_PARAMS['r_r']))
        self.entry_n_points.delete(0, tk.END)
        self.entry_n_points.insert(0, str(DEFAULT_PARAMS['n_points']))
        self.entry_alpha_threshold.delete(0, tk.END)
        self.entry_alpha_threshold.insert(0, str(DEFAULT_PARAMS['alpha_threshold']))

    # ===================================================================
    # 参数预设系统（P6-4）
    # ===================================================================

    def _on_save_preset(self):
        """保存当前参数为 JSON 预设文件"""
        import json
        try:
            preset = {
                'delta_0': self.entry_delta_0.get(),
                'delta_01': self.entry_delta_01.get(),
                'delta_ret': self.entry_delta_ret.get(),
                'delta_02': self.entry_delta_02.get(),
                'h': self.entry_h.get(),
                'omega': self.entry_omega.get(),
                'r_0': self.entry_r0.get(),
                'e': self.entry_e.get(),
                'r_r': self.entry_rr.get(),
                'n_points': self.entry_n_points.get(),
                'alpha_threshold': self.entry_alpha_threshold.get(),
                'tc_law': self.popup_tc.current(),
                'hc_law': self.popup_hc.current(),
                'sn': self.popup_sn.current(),
                'pz': self.popup_pz.current(),
            }
            filepath = filedialog.asksaveasfilename(
                title=t("export.preset_dialog.save_title", self.lang),
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("All", "*.*")]
            )
            if not filepath:
                return
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(preset, f, indent=2, ensure_ascii=False)
            self.status_var.set(t("status.preset_saved", self.lang, file=os.path.basename(filepath)))
        except Exception as exc:
            self.status_var.set(t("status.preset_save_failed", self.lang, error=str(exc)))

    def _on_load_preset(self):
        """从 JSON 预设文件加载参数"""
        import json
        try:
            filepath = filedialog.askopenfilename(
                title=t("export.preset_dialog.load_title", self.lang),
                filetypes=[("JSON", "*.json"), ("All", "*.*")]
            )
            if not filepath:
                return
            with open(filepath, 'r', encoding='utf-8') as f:
                preset = json.load(f)

            entry_map = {
                'delta_0': self.entry_delta_0,
                'delta_01': self.entry_delta_01,
                'delta_ret': self.entry_delta_ret,
                'delta_02': self.entry_delta_02,
                'h': self.entry_h,
                'omega': self.entry_omega,
                'r_0': self.entry_r0,
                'e': self.entry_e,
                'r_r': self.entry_rr,
                'n_points': self.entry_n_points,
                'alpha_threshold': self.entry_alpha_threshold,
            }
            for key, entry in entry_map.items():
                if key in preset:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(preset[key]))

            combo_map = {
                'tc_law': self.popup_tc,
                'hc_law': self.popup_hc,
                'sn': self.popup_sn,
                'pz': self.popup_pz,
            }
            for key, combo in combo_map.items():
                if key in preset:
                    idx = int(preset[key])
                    combo.current(idx)

            self.status_var.set(t("status.preset_loaded", self.lang, file=os.path.basename(filepath)))
        except Exception as exc:
            self.status_var.set(t("status.preset_load_failed", self.lang, error=str(exc)))

    def _on_close(self):
        """窗口关闭处理"""
        self._stop_animation()
        self.root.destroy()

    def run(self):
        """运行主窗口"""
        self.root.mainloop()


def main():
    """Entry point for pip-installed camforge command."""
    app = CamSimulator()
    app.run()


if __name__ == '__main__':
    main()
