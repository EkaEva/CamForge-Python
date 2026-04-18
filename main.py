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
import cam_mechanics

from i18n import t, SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP, detect_mpl_fonts

import sys
import platform

plt.rcParams['font.sans-serif'] = detect_mpl_fonts(DEFAULT_LANG)
plt.rcParams['axes.unicode_minus'] = False

# 从 ui 包导入常量、绘图函数和参数模型
from ui.constants import *
from ui.drawing import draw_fixed_support
from ui.params import ParameterModel
from ui.plots import (draw_motion_curves, draw_geometry_constraints, draw_displacement_curve, draw_velocity_curve,
                      draw_acceleration_curve, draw_profile_plot,
                      draw_pressure_angle_curve, draw_curvature_radius_curve)
from ui.constants import THEME_DARK
from ui.animation import render_frame_artists, update_info_panel, generate_gif_frames
from ui.i18n_manager import I18nManager
from ui.theme import ThemeManager
from ui.export import ExportManager
from ui.sidebar import SidebarBuilder


class CamSimulator:
    """凸轮机构仿真主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{t('app.title', DEFAULT_LANG)} v{__version__}")
        self.root.config(bg=THEME['toolbar_bg'])

        # 管理器
        self.i18n_mgr = I18nManager(DEFAULT_LANG)
        self.theme_mgr = ThemeManager()
        self.sidebar = None  # 在 _build_gui 中创建

        # 兼容属性（供旧代码引用）
        self.lang = self.i18n_mgr.lang
        self._tk_font_family = self.i18n_mgr.tk_font_family
        self._translatable = self.i18n_mgr._translatable
        self._dark_mode = False
        self._pause_state = "paused"

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

        # 注册所有控件到主题管理器（P5: 缓存替代递归遍历）
        self.theme_mgr.register_children(self.root)

        # 延迟刷新侧边栏，确保初始内容正确显示
        self.root.after(50, self._refresh_sidebar)

    # ===================================================================
    # i18n helpers（委托给 I18nManager）
    # ===================================================================

    def _reg(self, key, widget, font_size=None):
        """Register a widget for language-switch updates"""
        self.i18n_mgr.register(key, widget, font_size)
        self._translatable = self.i18n_mgr._translatable

    def _law_name(self, law_id):
        """Get motion law name in current language"""
        return self.i18n_mgr.law_name(law_id)

    def _on_language_change(self, event=None):
        """Handle language switch"""
        idx = self.sidebar.combos['lang'].current()
        new_lang = SUPPORTED_LANGS[idx]
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self.i18n_mgr.lang = new_lang
        self._tk_font_family = FONT_MAP[new_lang]["tk"]
        self.i18n_mgr._tk_font_family = self._tk_font_family
        self._apply_language()
        self.sidebar.update_combo_values(self.lang)
        self.i18n_mgr.update_mpl_fonts(new_lang)
        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self._init_info_panel()
                self.ax_anim.set_title(t("plot.title.animation", self.lang), fontsize=12)
                self.canvas.draw_idle()

    def _apply_language(self):
        """Update all registered widgets for current language"""
        combo_widgets = {
            'tc': self.sidebar.combos['tc_law'], 'hc': self.sidebar.combos['hc_law'],
            'sn': self.sidebar.combos['sn'], 'pz': self.sidebar.combos['pz'],
        }
        self.i18n_mgr.apply_language(self.lang, combo_widgets=combo_widgets)
        self.root.title(f"{t('app.title', self.lang)} v{__version__}")

    def _update_mpl_fonts(self, lang):
        """Update matplotlib font config"""
        self.i18n_mgr.update_mpl_fonts(lang)

    def _on_theme_change(self, event=None):
        """Handle theme switch (light/dark)"""
        is_dark = self.sidebar.combos['theme'].current() == 1
        if not self.theme_mgr.toggle(is_dark):
            return
        self._dark_mode = is_dark
        self._apply_theme()

    def _apply_theme(self):
        """Apply current theme to all widgets"""
        axes = [self.ax_s, self.ax_v, self.ax_a,
                self.ax_p, self.ax_alpha, self.ax_rho,
                self.ax_anim, self.ax_info]
        self.theme_mgr.apply_theme(
            self.root, sb_canvas=self._sb_canvas,
            axes=axes, canvas=self.canvas,
        )

        # Redraw if simulation data exists
        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self.canvas.draw_idle()
        else:
            self.canvas.draw_idle()

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

        main_area = tk.Frame(self.root, bg=THEME['toolbar_bg'])
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 拆分为子方法构建
        self.sidebar = SidebarBuilder(sidebar, self.i18n_mgr, self.theme_mgr,
                                      on_validate_entry=self._validate_entry)
        self.sidebar.build(self.lang,
                           arc_command=self._on_arc_toggle,
                           grid_command=self._on_grid_toggle)

        # 绑定语言/主题切换事件
        self.sidebar.combos['lang'].bind('<<ComboboxSelected>>', self._on_language_change)
        self.sidebar.combos['theme'].bind('<<ComboboxSelected>>', self._on_theme_change)

        toolbar, status_bar = self._build_toolbar(main_area)
        self._build_figure(main_area)

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

        # 下载勾选项 — 两行排列避免溢出
        dl_cb_kw = {'font': (self._tk_font_family, 9), 'bg': THEME['toolbar_bg'], 'anchor': 'w'}
        dl_frame = tk.Frame(toolbar, bg=THEME['toolbar_bg'])
        dl_frame.pack(side=tk.LEFT, fill=tk.Y)
        dl_row1 = tk.Frame(dl_frame, bg=THEME['toolbar_bg'])
        dl_row1.pack(side=tk.TOP, fill=tk.X)
        dl_row2 = tk.Frame(dl_frame, bg=THEME['toolbar_bg'])
        dl_row2.pack(side=tk.TOP, fill=tk.X)

        self.dl_s = tk.BooleanVar(value=True)
        cb_dl_s = tk.Checkbutton(dl_row1, text=t("toolbar.cb.dl_s", self.lang), variable=self.dl_s, **dl_cb_kw)
        cb_dl_s.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_s", cb_dl_s, font_size=9)
        self.dl_v = tk.BooleanVar(value=True)
        cb_dl_v = tk.Checkbutton(dl_row1, text=t("toolbar.cb.dl_v", self.lang), variable=self.dl_v, **dl_cb_kw)
        cb_dl_v.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_v", cb_dl_v, font_size=9)
        self.dl_a = tk.BooleanVar(value=True)
        cb_dl_a = tk.Checkbutton(dl_row1, text=t("toolbar.cb.dl_a", self.lang), variable=self.dl_a, **dl_cb_kw)
        cb_dl_a.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_a", cb_dl_a, font_size=9)
        self.dl_profile = tk.BooleanVar(value=True)
        cb_dl_profile = tk.Checkbutton(dl_row1, text=t("toolbar.cb.dl_profile", self.lang), variable=self.dl_profile, **dl_cb_kw)
        cb_dl_profile.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_profile", cb_dl_profile, font_size=9)
        self.dl_anim = tk.BooleanVar(value=True)
        cb_dl_anim = tk.Checkbutton(dl_row1, text=t("toolbar.cb.dl_anim", self.lang), variable=self.dl_anim, **dl_cb_kw)
        cb_dl_anim.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_anim", cb_dl_anim, font_size=9)

        self.dl_excel = tk.BooleanVar(value=True)
        cb_dl_excel = tk.Checkbutton(dl_row2, text=t("toolbar.cb.dl_excel", self.lang), variable=self.dl_excel, **dl_cb_kw)
        cb_dl_excel.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_excel", cb_dl_excel, font_size=9)
        self.dl_alpha = tk.BooleanVar(value=True)
        cb_dl_alpha = tk.Checkbutton(dl_row2, text=t("toolbar.cb.dl_alpha", self.lang), variable=self.dl_alpha, **dl_cb_kw)
        cb_dl_alpha.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_alpha", cb_dl_alpha, font_size=9)
        self.dl_curvature = tk.BooleanVar(value=False)
        cb_dl_curvature = tk.Checkbutton(dl_row2, text=t("toolbar.cb.dl_curvature", self.lang), variable=self.dl_curvature, **dl_cb_kw)
        cb_dl_curvature.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_curvature", cb_dl_curvature, font_size=9)
        self.dl_svg = tk.BooleanVar(value=False)
        cb_dl_svg = tk.Checkbutton(dl_row2, text=t("toolbar.cb.dl_svg", self.lang), variable=self.dl_svg, **dl_cb_kw)
        cb_dl_svg.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_svg", cb_dl_svg, font_size=9)
        self.dl_csv = tk.BooleanVar(value=False)
        cb_dl_csv = tk.Checkbutton(dl_row2, text=t("toolbar.cb.dl_csv", self.lang), variable=self.dl_csv, **dl_cb_kw)
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
        self.fig = Figure(figsize=(14, 8), dpi=100)

        # v0.3.2 新布局：左右两部分
        # 左侧：推杆运动线图（上）| 几何约束指标图（下）
        # 右侧：动画（主区域）| 信息面板（右侧小区域）
        gs = GridSpec(2, 3, figure=self.fig,
                      left=0.06, right=0.97, top=0.94, bottom=0.07,
                      wspace=0.25, hspace=0.30,
                      width_ratios=[1, 1.6, 0.4],
                      height_ratios=[1, 1])

        # 左侧静态图区域（第0列）
        self.ax_motion = self.fig.add_subplot(gs[0, 0])   # 推杆运动线图（三 Y 轴）
        self.ax_geom = self.fig.add_subplot(gs[1, 0])     # 几何约束指标图（双 Y 轴）

        # 右侧动态区域（第1、2列）
        self.ax_anim = self.fig.add_subplot(gs[:, 1])     # 动画（跨两行）
        self.ax_info = self.fig.add_subplot(gs[:, 2])     # 信息面板（跨两行）

        # 信息面板样式
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

    # ===================================================================
    # 参数读取与校验
    # ===================================================================

    def _read_params(self):
        """读取并校验参数，返回 ParameterModel 或 None"""
        result = self.sidebar.read_params(self.lang)
        if result is None:
            # 不应发生，read_params 总是返回 (model, warnings) 或 (None, error)
            return None

        model, detail = result
        if model is None:
            # detail 是错误消息字符串
            self.status_var.set(detail)
            return None

        # detail 是截断警告列表
        if detail:
            self.status_var.set(" | ".join(detail))
        else:
            self.status_var.set("")
        self.alpha_var.set("")
        return model

    # ===================================================================
    # 计算与启动
    # ===================================================================

    def _on_start(self):
        """开始仿真"""
        self._stop_animation()

        model = self._read_params()
        if model is None:
            return

        # 设置离散点数（P6-6: N_POINTS 可配置）
        n_points = model.n_points
        if n_points < 36:
            n_points = 36
        elif n_points > 3600:
            n_points = 3600
        cam_mechanics.N_POINTS = n_points

        # 压力角阈值（P6-5: 可配置）
        alpha_threshold = model.alpha_threshold
        if alpha_threshold <= 0:
            alpha_threshold = MAX_PRESSURE_ANGLE

        # 滚子半径
        r_r = model.r_r
        if r_r < 0:
            r_r = 0

        # 计算运动
        try:
            delta_deg, s, v, a, ds_ddelta, phase_bounds = compute_full_motion(
                model.delta_0, model.delta_01,
                model.delta_ret, model.delta_02,
                model.h, model.r_0, model.e,
                model.omega, model.tc_law, model.hc_law
            )

            # 计算凸轮廓形
            x, y, s_0 = compute_cam_profile(
                s, model.r_0, model.e, model.sn, model.pz
            )

            # 计算滚子实际廓形
            x_actual, y_actual = compute_roller_profile(x, y, r_r, model.sn)

            # 计算曲率半径
            rho = compute_curvature_radius(x, y)
        except ValueError as exc:
            self.status_var.set(str(exc))
            return

        # 预计算基圆/偏距圆坐标
        delta_full = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        x_base = model.r_0 * np.cos(delta_full)
        y_base = model.r_0 * np.sin(delta_full)
        x_offset = x_base / model.r_0 * model.e
        y_offset = y_base / model.r_0 * model.e

        # 预计算 Rmax
        R = np.hypot(x, y)
        Rmax = np.max(R)

        # 解析压力角
        alpha_all = compute_pressure_angle(s, ds_ddelta, s_0, model.e, model.pz)
        max_alpha = np.max(np.abs(alpha_all))

        # 警告累积显示
        warnings = []
        if max_alpha > alpha_threshold:
            warnings.append(t("status.warning_max_alpha", self.lang, val=max_alpha, threshold=alpha_threshold))
        if model.h > model.r_0:
            warnings.append(t("status.warning_h_gt_r0", self.lang, h=model.h, r0=model.r_0))
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
                'r_0': model.r_0, 'e': model.e, 'h': model.h,
                'omega': model.omega, 'sn': model.sn, 'pz': model.pz,
                'tc_law': model.tc_law, 'hc_law': model.hc_law,
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

    def _draw_motion_curves(self, ax, data, show_law_names=False):
        draw_motion_curves(ax, data, self.lang, show_law_names)

    def _draw_geometry_constraints(self, ax, data):
        draw_geometry_constraints(ax, data, self.lang)

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

    def _on_canvas_configure(self, event):
        """画布大小变化时自适应 figure 尺寸（防抖）"""
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(50, self._resize_figure_to_widget)

    def _resize_figure_to_widget(self):
        """将 figure 尺寸同步到 tkinter 控件实际大小"""
        self._resize_after_id = None
        widget = self.canvas.get_tk_widget()
        w_px = widget.winfo_width()
        h_px = widget.winfo_height()
        if w_px < 10 or h_px < 10:
            return
        dpi = self.fig.dpi
        new_w = w_px / dpi
        new_h = h_px / dpi
        cur_w, cur_h = self.fig.get_size_inches()
        if abs(new_w - cur_w) > 0.05 or abs(new_h - cur_h) > 0.05:
            self.fig.set_size_inches(new_w, new_h, forward=False)
            self.canvas.draw_idle()

    def _plot_static(self):
        """绘制静态图表"""
        data = self.sim_data

        # 清除所有静态图轴
        for ax in [self.ax_motion, self.ax_geom]:
            ax.clear()

        # 绘制三 Y 轴推杆运动线图
        self._draw_motion_curves(self.ax_motion, data, show_law_names=True)
        # 绘制双 Y 轴几何约束指标图（压力角+曲率半径）
        self._draw_geometry_constraints(self.ax_geom, data)

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

        # 不使用 set_aspect('equal')，手动计算等比例坐标范围
        # 根据轴框实际像素尺寸调整 xlim/ylim，使视觉上等比例且不裁剪
        self.fig.canvas.draw()
        bbox = ax.get_window_extent()
        px_w, px_h = bbox.width, bbox.height
        x_data = 2 * (Rmax + h)
        y_data = 2 * (Rmax + r_0)
        pixel_aspect = px_w / px_h if px_h > 0 else 1
        data_aspect = x_data / y_data
        if pixel_aspect > data_aspect:
            x_data = y_data * pixel_aspect
        else:
            y_data = x_data / pixel_aspect
        ax.set_xlim(-x_data / 2, x_data / 2)
        ax.set_ylim(-y_data / 2, y_data / 2)
        ax.grid(self.sidebar.checks['show_grid'].get())

        # 绘制前同步 figure 尺寸
        self._resize_figure_to_widget()
        self.fig.canvas.draw()
        ax.set_title(t("plot.title.animation", self.lang), fontsize=12)
        ax.set_xlabel(r'$x$ (mm)')
        ax.set_ylabel(r'$y$ (mm)')

        draw_fixed_support(ax, r_0)

        self._init_info_panel()

        self._anim_artists = {
            'cam': line_cam, 'base': line_base, 'offset': line_offset,
            'tangent': line_tangent, 'normal': line_normal,
            'rod': line_rod, 'tip': line_tip, 'center': line_center,
            'lower': line_lower, 'upper': line_upper,
            'boundaries': lines_boundary, 'arc': line_arc,
        }

    def _init_info_panel(self):
        """初始化信息面板（右下板块，垂直排列）"""
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
            y_pos = 0.90 - idx * 0.15
            lbl = ax.text(0.1, y_pos, f'{name}: --', transform=ax.transAxes,
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

        N = len(data['s'])
        i = self.current_frame

        if i >= N:
            self.animating = False
            self.btn_pause.config(text=t("toolbar.btn.replay", self.lang))
            self._pause_state = "replay"
            self.alpha_var.set(t("status.max_alpha", self.lang, val=data['max_alpha']))
            update_info_panel(self._info_labels, 360, data['max_alpha'], 0.0,
                              data['h'], data['s_0'], self.lang)
            self.canvas.draw_idle()
            return

        render_frame_artists(
            artists, data, i,
            show_base=self.sidebar.checks['show_base_circle'].get(),
            show_offset=self.sidebar.checks['show_offset_circle'].get(),
            show_tangent=self.sidebar.checks['show_tangent'].get(),
            show_normal=self.sidebar.checks['show_normal'].get(),
            show_limits=self.sidebar.checks['show_limits'].get(),
            show_boundaries=self.sidebar.checks['show_boundaries'].get(),
            show_arc=self.sidebar.checks['show_arc'].get(),
        )
        update_info_panel(self._info_labels, i, data['alpha_all'][i] if i < N else 0,
                          data['s'][i] if i < N else 0, data['h'], data['s_0'], self.lang)

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
        N = len(data['s'])
        if i < 0 or i >= N:
            return

        result = render_frame_artists(
            self._anim_artists, data, i,
            show_base=self.sidebar.checks['show_base_circle'].get(),
            show_offset=self.sidebar.checks['show_offset_circle'].get(),
            show_tangent=self.sidebar.checks['show_tangent'].get(),
            show_normal=self.sidebar.checks['show_normal'].get(),
            show_limits=self.sidebar.checks['show_limits'].get(),
            show_boundaries=self.sidebar.checks['show_boundaries'].get(),
            show_arc=self.sidebar.checks['show_arc'].get(),
        )
        update_info_panel(self._info_labels, i, result['alpha_i'],
                          result['s_i'], data['h'], data['s_0'], self.lang)
        self.canvas.draw_idle()

    # ===================================================================
    # 按钮回调
    # ===================================================================

    def _on_arc_toggle(self):
        if self.sidebar.checks['show_arc'].get():
            self.sidebar.checks['show_normal'].set(True)
        else:
            self.sidebar.checks['show_normal'].set(False)
            if self._anim_artists:
                self._anim_artists['arc'].set_data([], [])
                self._anim_artists['normal'].set_data([], [])
                self._anim_artists['center'].set_data([], [])
                self.canvas.draw_idle()

    def _on_grid_toggle(self):
        self.ax_anim.grid(self.sidebar.checks['show_grid'].get())
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

        data = self.sim_data
        saved = []
        errors = []

        # 使用 ExportManager 处理静态图导出
        export_mgr = ExportManager(self.root, self._sim_data_lock)
        toggles = {
            's': self.dl_s.get(), 'v': self.dl_v.get(),
            'a': self.dl_a.get(), 'profile': self.dl_profile.get(),
            'alpha': self.dl_alpha.get(), 'curvature': self.dl_curvature.get(),
            'svg': self.dl_svg.get(), 'csv': self.dl_csv.get(),
            'anim': False, 'excel': False,
        }
        draw_funcs = {
            'displacement': self._draw_displacement_curve,
            'velocity': self._draw_velocity_curve,
            'acceleration': self._draw_acceleration_curve,
            'profile': self._draw_profile_plot,
            'pressure_angle': self._draw_pressure_angle_curve,
            'curvature_radius': self._draw_curvature_radius_curve,
        }

        if any(toggles.values()):
            result = export_mgr.download(
                data, toggles, draw_funcs, self.lang,
                self._tk_font_family, {'ax_anim': self.ax_anim},
                self.status_var, folder,
            )
            if result is not None:
                saved, errors, folder = result

        # Excel 导出
        if self.dl_excel.get():
            export_mgr._export_excel(folder, saved, data, self.lang, errors)

        # GIF 动画导出
        if self.dl_anim.get():
            filename_anim = t("export.filename.animation", self.lang) + ".gif"
            filepath = os.path.join(folder, filename_anim)
            self._export_gif(filepath, folder, saved)

        if saved:
            self.status_var.set(t("status.saved", self.lang, files=', '.join(saved), folder=folder))
        elif self.dl_anim.get():
            self.status_var.set(t("status.gif_exporting", self.lang))
        if errors:
            err_msg = '; '.join(e for e in errors if e != 'openpyxl_missing')
            if 'openpyxl_missing' in errors:
                self.status_var.set(t("error.openpyxl_missing", self.lang))
            elif err_msg:
                self.status_var.set(t("status.export_failed", self.lang, error=err_msg))

    def _export_gif(self, filepath, folder, saved_list):
        """在后台线程中导出GIF动画"""
        if PILImage is None:
            self.status_var.set(t("status.gif_failed", self.lang, error="Pillow not installed"))
            return

        lang = self.lang
        show_base = self.sidebar.checks['show_base_circle'].get()
        show_offset = self.sidebar.checks['show_offset_circle'].get()
        show_limits = self.sidebar.checks['show_limits'].get()
        show_tangent_gif = self.sidebar.checks['show_tangent'].get()
        show_normal_gif = self.sidebar.checks['show_normal'].get()
        show_arc_gif = self.sidebar.checks['show_arc'].get()
        show_boundaries_gif = self.sidebar.checks['show_boundaries'].get()

        with self._sim_data_lock:
            data = self.sim_data
            if data is None:
                return
            # 复制数据以确保线程安全
            thread_data = {
                's': data['s'].copy(),
                'ds_ddelta': data['ds_ddelta'].copy(),
                'alpha_all': data['alpha_all'].copy(),
                'x': data['x'].copy(),
                'y': data['y'].copy(),
                'x_base': data['x_base'].copy(),
                'y_base': data['y_base'].copy(),
                'x_offset': data['x_offset'].copy(),
                'y_offset': data['y_offset'].copy(),
                's_0': data['s_0'],
                'e': data['e'],
                'r_0': data['r_0'],
                'h': data['h'],
                'sn': data['sn'],
                'pz': data['pz'],
                'phase_bounds': list(data['phase_bounds']),
            }

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
        N = len(thread_data['s'])
        progress_bar = ttk.Progressbar(progress_win, length=280, mode='determinate', maximum=N)
        progress_bar.pack(pady=4)
        progress_label = tk.Label(progress_win, text="0 / 360", font=(self._tk_font_family, 9))
        progress_label.pack()

        gif_result = {'error': None}

        def progress_callback(idx, total, phase_text):
            if phase_text is None:
                self.root.after(0, lambda: (
                    progress_bar.configure(value=idx + 1),
                    progress_label.configure(text=f"{idx + 1} / {total}")
                ))
            else:
                self.root.after(0, lambda: progress_label.configure(
                    text=t("status.gif_composing", lang)))

        def generate():
            try:
                generate_gif_frames(
                    thread_data, filepath, saved_list, folder,
                    show_base=show_base, show_offset=show_offset,
                    show_tangent=show_tangent_gif, show_normal=show_normal_gif,
                    show_limits=show_limits, show_boundaries=show_boundaries_gif,
                    show_arc=show_arc_gif, lang=lang,
                    xlim=xlim, ylim=ylim,
                    progress_callback=progress_callback,
                )
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
        self.sidebar.clear_params()
        self.status_var.set("")
        self.alpha_var.set("")

    def _on_clear_plots(self):
        """清除图像"""
        self._stop_animation()
        for ax in [self.ax_s, self.ax_v, self.ax_a,
                   self.ax_p, self.ax_alpha, self.ax_rho,
                   self.ax_anim, self.ax_info]:
            ax.clear()
        self.canvas.draw()

    def _on_random(self):
        """随机凸轮参数"""
        self.sidebar.set_random_params()

    # ===================================================================
    # 参数预设系统（P6-4）
    # ===================================================================

    def _on_save_preset(self):
        """保存当前参数为 JSON 预设文件"""
        import json
        try:
            preset = self.sidebar.get_preset_data()
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

            self.sidebar.load_preset_data(preset)

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
