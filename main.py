"""
CamForge - 尖顶凸轮仿真
使用 CustomTkinter + matplotlib 实现现代化凸轮机构运动学仿真
"""

import json
import os
import platform
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

matplotlib.use('TkAgg')

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

from cam_mechanics import (
    DEG2RAD, __version__,
    compute_cam_profile, compute_curvature_radius,
    compute_full_motion, compute_pressure_angle,
    compute_roller_profile, validate_params,
)

from i18n import DEFAULT_LANG, FONT_MAP, SUPPORTED_LANGS, detect_mpl_fonts, t

# CustomTkinter 全局配置
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

plt.rcParams['font.sans-serif'] = detect_mpl_fonts(DEFAULT_LANG)
plt.rcParams['axes.unicode_minus'] = False

# 从 ui 包导入
from ui.constants import *
from ui.drawing import draw_fixed_support
from ui.params import ParameterModel
from ui.plots import (draw_motion_curves, draw_geometry_constraints, draw_profile_plot)
from ui.animation import render_frame_artists, update_info_panel, generate_gif_frames
from ui.i18n_manager import I18nManager
from ui.export import ExportManager
from ui.config import ConfigManager
from ui.dxf_export import export_cam_profile_to_dxf, export_both_profiles_to_dxf
from ui.shortcut import ShortcutManager, setup_animation_shortcuts

# CustomTkinter 组件
from ui.ctk_constants import COLORS_LIGHT, COLORS_DARK, UI_PADDING, SIDEBAR_WIDTH
from ui.ctk_sidebar import CTkSidebar
from ui.ctk_toolbar import CTkToolbar, CTkStatusBar


class CamSimulator(ctk.CTk):
    """凸轮机构仿真主窗口 (CustomTkinter 版本)"""

    def __init__(self):
        super().__init__()

        # 配置管理器
        self.config_mgr = ConfigManager()

        self.title(f"{t('app.title', DEFAULT_LANG)} v{__version__}")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # 管理器
        self.i18n_mgr = I18nManager(DEFAULT_LANG)
        self.sidebar = None
        self.toolbar = None
        self.status_bar = None
        self.shortcut_mgr = None

        # 兼容属性
        self.lang = self.i18n_mgr.lang
        self._tk_font_family = self.i18n_mgr.tk_font_family
        self._dark_mode = False
        self._pause_state = "paused"

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
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 构建界面
        self._build_gui()
        self._setup_shortcuts()
        self._load_saved_config()

        # 设置全屏（延迟执行确保窗口已创建）
        self.after(100, self._set_fullscreen)

    def _setup_shortcuts(self):
        """设置键盘快捷键"""
        self.shortcut_mgr = setup_animation_shortcuts(
            self,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_random=self._on_random,
            on_prev_frame=self._on_prev_frame,
            on_next_frame=self._on_next_frame,
            on_first_frame=self._on_first_frame,
            on_last_frame=self._on_last_frame,
            on_stop=self._stop_animation,
        )

    def _load_saved_config(self):
        """加载保存的配置"""
        last_params = self.config_mgr.get_last_params()
        if last_params:
            self.sidebar.load_preset_data(last_params)

        export_opts = self.config_mgr.get_export_options()
        for name, var in self.sidebar.download_checkboxes.items():
            if name in export_opts:
                var.set(export_opts[name])

        ui_settings = self.config_mgr.get_ui_settings()
        self.toolbar.speed_var.set(ui_settings.get('speed', 3))
        if ui_settings.get('dark_mode', False):
            self.sidebar.combos['theme'].set_index(1)
            self._on_theme_change()

    def _set_fullscreen(self):
        """设置全屏窗口"""
        if platform.system() == 'Windows':
            try:
                self.state('zoomed')
            except tk.TclError:
                pass
        elif platform.system() == 'Darwin':
            self.attributes('-fullscreen', True)
        else:
            self.attributes('-zoomed', True)

    def _save_current_config(self):
        """保存当前配置"""
        params = self.sidebar.get_preset_data()
        self.config_mgr.set_last_params(params)

        export_opts = {name: var.get() for name, var in self.sidebar.download_checkboxes.items()}
        self.config_mgr.set_export_options(export_opts)

        ui_settings = {
            'language': self.lang,
            'dark_mode': self._dark_mode,
            'speed': self.toolbar.speed_var.get(),
        }
        self.config_mgr.set_ui_settings(ui_settings)

    # ===================================================================
    # GUI 构建
    # ===================================================================

    def _build_gui(self):
        """构建整体界面布局"""
        # 整体布局：左侧边栏 + 右侧主区域
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 左侧边栏
        self.sidebar_frame = ctk.CTkScrollableFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=COLORS_LIGHT['sidebar_bg'],
        )
        self.sidebar_frame.grid(row=0, column=0, sticky='nsew')

        self.sidebar = CTkSidebar(self.sidebar_frame, self.i18n_mgr)
        self.sidebar.build(self.lang,
                          arc_command=self._on_arc_toggle,
                          grid_command=self._on_grid_toggle,
                          lang_command=self._on_language_change,
                          theme_command=self._on_theme_change,
                          preset_command=self._on_quick_preset_select)

        # 右侧主区域
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS_LIGHT['main_bg'])
        self.main_frame.grid(row=0, column=1, sticky='nsew')
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._build_toolbar()
        self._build_figure()
        self._build_status_bar()

    def _build_toolbar(self):
        """构建工具栏"""
        self.toolbar = CTkToolbar(self.main_frame, self.lang)
        self.toolbar.frame.grid(row=0, column=0, sticky='ew', padx=UI_PADDING, pady=(15, 0))
        self.toolbar.build(
            self.lang,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_clear=self._on_clear,
            on_random=self._on_random,
            on_load_preset=self._on_load_preset,
            on_save_preset=self._on_save_preset,
            on_export_all=self._on_export_all,
            on_download=self._on_download,
            on_frame_seek=self._on_frame_seek,
        )

    def _build_figure(self):
        """构建图表区域"""
        # 获取当前背景色
        bg_color = '#ffffff' if ctk.get_appearance_mode() == 'Light' else '#000000'

        self.fig = Figure(figsize=(14, 8), dpi=100, facecolor=bg_color)

        gs = GridSpec(2, 3, figure=self.fig,
                      left=0.055, right=0.98, top=0.94, bottom=0.07,
                      wspace=0.15, hspace=0.28,
                      width_ratios=[1, 0.25, 0.9],
                      height_ratios=[1, 1])

        self.ax_motion = self.fig.add_subplot(gs[0, 0])
        self.ax_geom = self.fig.add_subplot(gs[1, 0])
        self.ax_anim = self.fig.add_subplot(gs[:, 2])

        self.ax_info = self.ax_anim.inset_axes([0.02, 0.55, 0.40, 0.42])
        self.ax_info.set_xticks([])
        self.ax_info.set_yticks([])
        self.ax_info.set_frame_on(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew', padx=UI_PADDING, pady=10)

        self._resize_after_id = None

    def _build_status_bar(self):
        """构建状态栏"""
        self.status_bar = CTkStatusBar(self.main_frame, self.lang)
        self.status_bar.frame.grid(row=2, column=0, sticky='ew', padx=UI_PADDING, pady=(0, 10))
        self.status_bar.build(self.lang)

    # ===================================================================
    # 事件处理
    # ===================================================================

    def _on_language_change(self, event=None):
        """语言切换"""
        idx = self.sidebar.combos['lang'].current()
        new_lang = SUPPORTED_LANGS[idx]
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self.i18n_mgr.lang = new_lang
        self._tk_font_family = FONT_MAP[new_lang]["tk"]
        self.i18n_mgr._tk_font_family = self._tk_font_family

        self.sidebar.build(self.lang,
                          arc_command=self._on_arc_toggle,
                          grid_command=self._on_grid_toggle,
                          lang_command=self._on_language_change,
                          theme_command=self._on_theme_change,
                          preset_command=self._on_quick_preset_select)
        self.sidebar.combos['lang'].set_index(idx)
        self.toolbar.build(
            self.lang,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_clear=self._on_clear,
            on_random=self._on_random,
            on_load_preset=self._on_load_preset,
            on_save_preset=self._on_save_preset,
            on_export_all=self._on_export_all,
            on_download=self._on_download,
            on_frame_seek=self._on_frame_seek,
        )
        self.status_bar.build(self.lang)

        self.title(f"{t('app.title', self.lang)} v{__version__}")

        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self._init_info_panel()
                self.ax_anim.set_title(t("plot.title.animation", self.lang), fontsize=12)
                self.canvas.draw_idle()

    def _on_theme_change(self, event=None):
        """主题切换"""
        idx = self.sidebar.combos['theme'].current()
        is_dark = idx == 1

        if is_dark:
            ctk.set_appearance_mode("Dark")
            self._dark_mode = True
        else:
            ctk.set_appearance_mode("Light")
            self._dark_mode = False

        self._apply_theme()

    def _apply_theme(self):
        """应用主题"""
        bg_color = '#000000' if self._dark_mode else '#ffffff'
        text_color = '#ffffff' if self._dark_mode else '#000000'

        self.fig.set_facecolor(bg_color)

        for ax in [self.ax_motion, self.ax_geom, self.ax_anim]:
            ax.set_facecolor(bg_color)
            ax.tick_params(colors=text_color)
            for spine in ax.spines.values():
                spine.set_edgecolor('gray')
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)

        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self.canvas.draw_idle()
        else:
            self.canvas.draw_idle()

    def _on_quick_preset_select(self, event=None):
        """快速预设选择"""
        idx = self.sidebar.combos['quick_preset'].current()
        if idx < 0:
            return

        built_in_presets = [
            {'delta_0': 120, 'delta_01': 60, 'delta_ret': 90, 'delta_02': 90,
             'h': 30, 'r_0': 40, 'e': 5, 'omega': 10,
             'tc_law': 4, 'hc_law': 4, 'sn': 1, 'pz': 1,
             'r_r': 0, 'n_points': 360, 'alpha_threshold': 30},
            {'delta_0': 90, 'delta_01': 45, 'delta_ret': 90, 'delta_02': 135,
             'h': 15, 'r_0': 25, 'e': 3, 'omega': 15,
             'tc_law': 5, 'hc_law': 5, 'sn': 1, 'pz': 1,
             'r_r': 0, 'n_points': 360, 'alpha_threshold': 35},
            {'delta_0': 150, 'delta_01': 30, 'delta_ret': 120, 'delta_02': 60,
             'h': 50, 'r_0': 80, 'e': 10, 'omega': 5,
             'tc_law': 4, 'hc_law': 4, 'sn': 1, 'pz': 1,
             'r_r': 0, 'n_points': 360, 'alpha_threshold': 25},
            {'delta_0': 120, 'delta_01': 60, 'delta_ret': 120, 'delta_02': 60,
             'h': 25, 'r_0': 50, 'e': 8, 'omega': 50,
             'tc_law': 6, 'hc_law': 6, 'sn': 1, 'pz': 1,
             'r_r': 0, 'n_points': 720, 'alpha_threshold': 25},
            {'delta_0': 135, 'delta_01': 45, 'delta_ret': 90, 'delta_02': 90,
             'h': 35, 'r_0': 45, 'e': 6, 'omega': 12,
             'tc_law': 4, 'hc_law': 4, 'sn': 1, 'pz': 1,
             'r_r': 10, 'n_points': 360, 'alpha_threshold': 30},
        ]

        if idx < len(built_in_presets):
            self.sidebar.load_preset_data(built_in_presets[idx])
            preset_name = self.sidebar.combos['quick_preset'].get()
            self.status_bar.set_status(t("status.preset_loaded", self.lang, file=preset_name))

    def _on_arc_toggle(self):
        """压力角弧线切换"""
        if self.sidebar.switches['show_arc'].get():
            self.sidebar.switches['show_normal'].set(True)
        else:
            self.sidebar.switches['show_normal'].set(False)
            if self._anim_artists:
                self._anim_artists['arc'].set_data([], [])
                self._anim_artists['normal'].set_data([], [])
                self._anim_artists['center'].set_data([], [])
                self.canvas.draw_idle()

    def _on_grid_toggle(self):
        """网格线切换"""
        self.ax_anim.grid(self.sidebar.switches['show_grid'].get())
        self.canvas.draw_idle()

    def _on_frame_seek(self, value):
        """帧跳转"""
        if not self.animating and self.sim_data is not None:
            self.current_frame = int(value)
            self._draw_single_frame(self.current_frame)

    # ===================================================================
    # 按钮回调
    # ===================================================================

    def _on_start(self):
        """开始仿真"""
        self._stop_animation()

        result = self.sidebar.read_params(self.lang)
        if result is None:
            return

        model, detail = result
        if model is None:
            self.status_bar.set_status(detail, 'danger')
            return

        if detail:
            self.status_bar.set_status(" | ".join(detail), 'warning')
        else:
            self.status_bar.set_status("")

        n_points = model.n_points
        if n_points < 36:
            n_points = 36
        elif n_points > 3600:
            n_points = 3600

        alpha_threshold = model.alpha_threshold
        if alpha_threshold <= 0:
            alpha_threshold = MAX_PRESSURE_ANGLE

        r_r = model.r_r
        if r_r < 0:
            self.status_bar.set_status(t("status.warning_r_r_negative", self.lang, val=r_r), 'warning')
            return

        try:
            delta_deg, s, v, a, ds_ddelta, phase_bounds = compute_full_motion(
                model.delta_0, model.delta_01,
                model.delta_ret, model.delta_02,
                model.h, model.r_0, model.e,
                model.omega, model.tc_law, model.hc_law,
                n_points=n_points
            )
            x, y, s_0 = compute_cam_profile(s, model.r_0, model.e, model.sn, model.pz)
            rho = compute_curvature_radius(x, y)
        except ValueError as exc:
            self.status_bar.set_status(str(exc), 'danger')
            return

        if r_r > 0:
            rho_finite = rho[np.isfinite(rho)]
            if len(rho_finite) > 0:
                min_abs_rho = np.min(np.abs(rho_finite))
                if r_r >= min_abs_rho:
                    self.status_bar.set_status(t("status.warning_r_r_exceed", self.lang, r_r=r_r, min_rho=min_abs_rho), 'danger')
                    return

        try:
            x_actual, y_actual = compute_roller_profile(x, y, r_r, model.sn)
        except ValueError as exc:
            self.status_bar.set_status(str(exc), 'danger')
            return

        delta_full = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        x_base = model.r_0 * np.cos(delta_full)
        y_base = model.r_0 * np.sin(delta_full)
        x_offset = x_base / model.r_0 * model.e
        y_offset = y_base / model.r_0 * model.e

        R = np.hypot(x, y)
        Rmax = np.max(R)

        alpha_all = compute_pressure_angle(s, ds_ddelta, s_0, model.e, model.pz)
        max_alpha = np.max(np.abs(alpha_all))

        warnings = []
        if max_alpha > alpha_threshold:
            warnings.append(t("status.warning_max_alpha", self.lang, val=max_alpha, threshold=alpha_threshold))
        if model.h > model.r_0:
            warnings.append(t("status.warning_h_gt_r0", self.lang, h=model.h, r0=model.r_0))
        rho_finite = rho[np.isfinite(rho)]
        if len(rho_finite) > 0 and r_r > 0:
            min_rho_abs = np.min(np.abs(rho_finite))
            if min_rho_abs < r_r:
                warnings.append(t("status.warning_min_curvature", self.lang, val=min_rho_abs, r_r=r_r))
        if warnings:
            self.status_bar.set_status(" | ".join(warnings), 'warning')

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
            rho_finite = rho[np.isfinite(rho)]
            if len(rho_finite) > 0:
                self.sim_data['min_rho_idx'] = int(np.argmin(np.abs(rho_finite)))
            else:
                self.sim_data['min_rho_idx'] = 0

        self._plot_static()
        self._start_animation()

    def _on_pause(self):
        """暂停/继续"""
        if self.animating:
            self.paused = not self.paused
            if self.paused:
                self.toolbar.update_pause_button(t("toolbar.btn.resume", self.lang))
                self._pause_state = "paused_running"
            else:
                self.toolbar.update_pause_button(t("toolbar.btn.pause", self.lang))
                self._pause_state = "paused"
                self._animate_frame()
        elif self.sim_data is not None and self._pause_state == "replay":
            self._start_animation()

    def _on_clear(self):
        """清除参数和图像"""
        self.sidebar.clear_params()
        self._stop_animation()
        self._clear_twinx_axes()
        for ax in [self.ax_motion, self.ax_geom, self.ax_anim]:
            ax.clear()
        self.canvas.draw()
        self.status_bar.clear()

    def _on_random(self):
        """随机参数"""
        self.sidebar.set_random_params()

    def _on_load_preset(self):
        """加载预设"""
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
            self.status_bar.set_status(t("status.preset_loaded", self.lang, file=os.path.basename(filepath)), 'success')
        except Exception as exc:
            self.status_bar.set_status(t("status.preset_load_failed", self.lang, error=str(exc)), 'danger')

    def _on_save_preset(self):
        """保存预设"""
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
            self.status_bar.set_status(t("status.preset_saved", self.lang, file=os.path.basename(filepath)), 'success')
        except Exception as exc:
            self.status_bar.set_status(t("status.preset_save_failed", self.lang, error=str(exc)), 'danger')

    def _on_export_all(self):
        """全部导出"""
        if self.sim_data is None:
            self.status_bar.set_status(t("status.run_first", self.lang), 'warning')
            return

        folder = filedialog.askdirectory(title=t("export.folder_dialog.title", self.lang))
        if not folder:
            return

        # 临时设置所有选项为 True
        original_values = {name: var.get() for name, var in self.sidebar.download_checkboxes.items()}
        for var in self.sidebar.download_checkboxes.values():
            var.set(True)

        self._do_export(folder)

        # 恢复原始选项
        for name, var in self.sidebar.download_checkboxes.items():
            var.set(original_values.get(name, True))

    def _on_download(self):
        """下载"""
        if not any(var.get() for var in self.sidebar.download_checkboxes.values()):
            self.status_bar.set_status(t("status.no_download_selection", self.lang), 'warning')
            return

        if self.sim_data is None:
            self.status_bar.set_status(t("status.run_first", self.lang), 'warning')
            return

        folder = filedialog.askdirectory(title=t("export.folder_dialog.title", self.lang))
        if not folder:
            return

        self._do_export(folder)

    def _do_export(self, folder):
        """执行导出"""
        data = self.sim_data
        saved = []
        errors = []

        export_mgr = ExportManager(self, self._sim_data_lock)
        toggles = {
            'motion': self.sidebar.download_checkboxes['dl_motion'].get(),
            'geom': self.sidebar.download_checkboxes['dl_geom'].get(),
            'profile': self.sidebar.download_checkboxes['dl_profile'].get(),
            'svg': self.sidebar.download_checkboxes['dl_svg'].get(),
            'csv': self.sidebar.download_checkboxes['dl_csv'].get(),
            'anim': False,
            'excel': False,
        }
        draw_funcs = {
            'motion_curves': self._draw_motion_curves,
            'geometry_constraints': self._draw_geometry_constraints,
            'profile': self._draw_profile_plot,
        }

        if any(toggles.values()):
            result = export_mgr.download(
                data, toggles, draw_funcs, self.lang,
                self._tk_font_family, {'ax_anim': self.ax_anim},
                None, folder,
            )
            if result is not None:
                saved, errors, folder = result

        if self.sidebar.download_checkboxes['dl_excel'].get():
            export_mgr._export_excel(folder, saved, data, self.lang, errors)

        if self.sidebar.download_checkboxes['dl_dxf'].get():
            self._export_dxf(folder, saved, errors)

        # 非 GIF 导出成功后立即显示提示
        if saved:
            self.status_bar.set_status(t("status.saved", self.lang, files=', '.join(saved), folder=folder), 'success')

        # GIF 导出是异步的，完成后会追加到状态栏
        if self.sidebar.download_checkboxes['dl_anim'].get():
            filename_anim = t("export.filename.animation", self.lang) + ".gif"
            filepath = os.path.join(folder, filename_anim)
            self._export_gif(filepath, folder, saved)

    def _export_dxf(self, folder, saved_list, errors):
        """导出 DXF"""
        try:
            data = self.sim_data
            if data is None:
                return

            filename = t("export.filename.dxf", self.lang) + ".dxf"
            filepath = os.path.join(folder, filename)

            x = data['x']
            y = data['y']
            x_actual = data.get('x_actual')
            y_actual = data.get('y_actual')
            r_r = data.get('r_r', 0)

            if r_r > 0 and x_actual is not None and y_actual is not None:
                export_both_profiles_to_dxf(x, y, x_actual, y_actual, filepath)
            else:
                export_cam_profile_to_dxf(x, y, filepath)

            saved_list.append(filename)
        except Exception as exc:
            errors.append(f"dxf: {exc}")

    def _export_gif(self, filepath, folder, saved_list):
        """在后台线程中导出GIF动画"""
        if PILImage is None:
            self.status_bar.set_status(t("status.gif_failed", self.lang, error="Pillow not installed"), 'danger')
            return

        lang = self.lang
        show_base = self.sidebar.switches['show_base_circle'].get()
        show_offset = self.sidebar.switches['show_offset_circle'].get()
        show_limits = self.sidebar.switches['show_limits'].get()
        show_tangent_gif = self.sidebar.switches['show_tangent'].get()
        show_normal_gif = self.sidebar.switches['show_normal'].get()
        show_arc_gif = self.sidebar.switches['show_arc'].get()
        show_boundaries_gif = self.sidebar.switches['show_boundaries'].get()

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
                'r_r': data['r_r'],
                'x_actual': data['x_actual'].copy() if data['x_actual'] is not None else None,
                'y_actual': data['y_actual'].copy() if data['y_actual'] is not None else None,
            }

        xlim = self.ax_anim.get_xlim()
        ylim = self.ax_anim.get_ylim()

        # CustomTkinter 进度弹窗
        progress_win = ctk.CTkToplevel(self)
        progress_win.title(t("export.gif_dialog.title", lang))
        progress_win.geometry("320x120")
        progress_win.resizable(False, False)
        progress_win.transient(self)
        progress_win.grab_set()

        from ui.ctk_constants import create_ctk_font, FONT_SIZE_LABEL

        msg_label = ctk.CTkLabel(
            progress_win,
            text=t("export.gif_dialog.message", lang),
            font=create_ctk_font(size=FONT_SIZE_LABEL),
        )
        msg_label.pack(pady=(15, 8))

        N = len(thread_data['s'])
        progress_bar = ctk.CTkProgressBar(progress_win, width=280)
        progress_bar.set(0)
        progress_bar.pack(pady=4)

        progress_label = ctk.CTkLabel(
            progress_win,
            text="0 / 360",
            font=create_ctk_font(size=FONT_SIZE_LABEL - 2),
        )
        progress_label.pack()

        gif_result = {'error': None}

        def progress_callback(idx, total, phase_text):
            if phase_text is None:
                progress_val = (idx + 1) / total
                self.after(0, lambda v=progress_val, i=idx, t=total: (
                    progress_bar.set(v),
                    progress_label.configure(text=f"{i + 1} / {t}")
                ))
            else:
                self.after(0, lambda: progress_label.configure(
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
                        self.status_bar.set_status(t("status.gif_failed", lang, error=gif_result['error']), 'danger')
                    elif saved_list:
                        # 追加 GIF 到已保存列表
                        all_saved = saved_list
                        self.status_bar.set_status(t("status.saved", lang, files=', '.join(all_saved), folder=folder), 'success')
                self.after(0, _on_done)

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    # ===================================================================
    # 静态图表
    # ===================================================================

    def _draw_motion_curves(self, ax, data, show_law_names=False):
        draw_motion_curves(ax, data, self.lang, show_law_names)

    def _draw_geometry_constraints(self, ax, data):
        draw_geometry_constraints(ax, data, self.lang)

    def _draw_profile_plot(self, ax, data):
        draw_profile_plot(ax, data, self.lang)

    def _clear_twinx_axes(self):
        """清除 twinx 次轴"""
        main_axes = {self.ax_motion, self.ax_geom, self.ax_anim, self.ax_info}
        to_remove = [ax for ax in self.fig.axes if ax not in main_axes]
        for ax in to_remove:
            self.fig.delaxes(ax)

    def _plot_static(self):
        """绘制静态图表"""
        data = self.sim_data

        self._clear_twinx_axes()

        for ax in [self.ax_motion, self.ax_geom]:
            ax.clear()

        self._draw_motion_curves(self.ax_motion, data, show_law_names=True)
        self._draw_geometry_constraints(self.ax_geom, data)

        self.canvas.draw()

    # ===================================================================
    # 动画
    # ===================================================================

    def _init_anim_artists(self):
        """初始化动画图形对象"""
        ax = self.ax_anim
        ax.clear()

        data = self.sim_data
        r_0 = data['r_0']
        h = data['h']
        Rmax = data['Rmax']
        r_r = data.get('r_r', 0)

        line_cam, = ax.plot([], [], 'r-', linewidth=2)
        line_theory, = ax.plot([], [], 'b:', linewidth=1.5)
        line_base, = ax.plot([], [], 'm-', linewidth=1)
        line_offset, = ax.plot([], [], 'c-', linewidth=1)
        line_tangent, = ax.plot([], [], 'm-', linewidth=1)
        line_normal, = ax.plot([], [], 'm-', linewidth=1)
        line_rod, = ax.plot([], [], 'k-', linewidth=1.5, solid_capstyle='butt')
        line_tip, = ax.plot([], [], 'k-', linewidth=2)
        line_roller, = ax.plot([], [], 'k-', linewidth=2)
        line_roller_center, = ax.plot([], [], 'ko', markersize=2)
        line_center, = ax.plot([], [], 'k--', linewidth=0.8)
        line_lower, = ax.plot([], [], 'c-.', linewidth=1)
        line_upper, = ax.plot([], [], 'm--', linewidth=1)
        lines_boundary = []
        for _ in range(4):
            lb, = ax.plot([], [], 'k-', linewidth=0.8)
            lines_boundary.append(lb)
        line_arc, = ax.plot([], [], 'k-', linewidth=1)

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
        ax.grid(self.sidebar.switches['show_grid'].get())

        ax.set_title(t("plot.title.animation", self.lang), fontsize=12)
        ax.set_xlabel(r'$x$ (mm)')
        ax.set_ylabel(r'$y$ (mm)')

        draw_fixed_support(ax, r_0)

        self.ax_info = ax.inset_axes([0.01, 0.78, 0.28, 0.20])
        self._init_info_panel()

        self._anim_artists = {
            'cam': line_cam, 'theory': line_theory, 'base': line_base, 'offset': line_offset,
            'tangent': line_tangent, 'normal': line_normal,
            'rod': line_rod, 'tip': line_tip, 'roller': line_roller, 'roller_center': line_roller_center,
            'center': line_center, 'lower': line_lower, 'upper': line_upper,
            'boundaries': lines_boundary, 'arc': line_arc,
        }

    def _init_info_panel(self):
        """初始化信息面板"""
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor((1.0, 1.0, 1.0, 0.8))
        for spine in ax.spines.values():
            spine.set_visible(False)  # 无边框

        items = [
            ('delta', t("info.label.delta", self.lang)),
            ('alpha', t("info.label.alpha", self.lang)),
            ('s', t("info.label.s", self.lang)),
        ]
        self._info_labels = {}

        for idx, (key, name) in enumerate(items):
            y_pos = 0.78 - idx * 0.22
            lbl = ax.text(0.10, y_pos, f'{name}: --', transform=ax.transAxes,
                          fontsize=8, ha='left', va='top', color='black')
            self._info_labels[key] = lbl

    def _start_animation(self):
        """开始动画"""
        self.animating = True
        self.paused = False
        self.current_frame = 0
        self.toolbar.update_pause_button(t("toolbar.btn.pause", self.lang))
        self._pause_state = "paused"
        self._init_anim_artists()
        if self.sim_data is not None:
            n = len(self.sim_data['s'])
            self.toolbar.set_frame_range(n - 1)
        self._animate_frame()

    def _stop_animation(self):
        """停止动画"""
        self.animating = False
        self.paused = False
        if self.anim_id is not None:
            self.after_cancel(self.anim_id)
            self.anim_id = None
        self._anim_artists = None

    def _animate_frame(self):
        """绘制一帧"""
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
            self.toolbar.update_pause_button(t("toolbar.btn.replay", self.lang))
            self._pause_state = "replay"
            label_alpha = t("status.label.max_alpha", self.lang)
            self.status_bar.set_alpha(f'{label_alpha}: {data["max_alpha"]:.2f}°')
            h, s_0 = update_info_panel(self._info_labels, 360, data['max_alpha'], 0.0,
                              data['h'], data['s_0'], self.lang)
            label_h = t("status.label.h", self.lang)
            label_s0 = t("status.label.s0", self.lang)
            self.status_bar.set_stroke(f'{label_h}: {h:.1f} mm')
            self.status_bar.set_s0(f'{label_s0}: {s_0:.2f} mm')
            self.canvas.draw_idle()
            return

        render_frame_artists(
            artists, data, i,
            show_base=self.sidebar.switches['show_base_circle'].get(),
            show_offset=self.sidebar.switches['show_offset_circle'].get(),
            show_tangent=self.sidebar.switches['show_tangent'].get(),
            show_normal=self.sidebar.switches['show_normal'].get(),
            show_limits=self.sidebar.switches['show_limits'].get(),
            show_boundaries=self.sidebar.switches['show_boundaries'].get(),
            show_arc=self.sidebar.switches['show_arc'].get(),
        )

        n_points = data.get('n_points', N)
        angle_deg = int(i * 360.0 / n_points)
        h, s_0 = update_info_panel(self._info_labels, angle_deg, data['alpha_all'][i] if i < N else 0,
                          data['s'][i] if i < N else 0, data['h'], data['s_0'], self.lang)

        label_h = t("status.label.h", self.lang)
        label_s0 = t("status.label.s0", self.lang)
        self.status_bar.set_stroke(f'{label_h}: {h:.1f} mm')
        self.status_bar.set_s0(f'{label_s0}: {s_0:.2f} mm')

        if i % ANIM_FRAME_SKIP == 0:
            self.canvas.draw_idle()

        self.toolbar.set_frame(i)

        self.current_frame += 1
        delay = max(ANIM_MIN_DELAY_MS, int(ANIM_BASE_DELAY_MS / (self.toolbar.get_speed() ** 1.5)))
        self.anim_id = self.after(delay, self._animate_frame)

    def _draw_single_frame(self, i):
        """绘制指定帧"""
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
            show_base=self.sidebar.switches['show_base_circle'].get(),
            show_offset=self.sidebar.switches['show_offset_circle'].get(),
            show_tangent=self.sidebar.switches['show_tangent'].get(),
            show_normal=self.sidebar.switches['show_normal'].get(),
            show_limits=self.sidebar.switches['show_limits'].get(),
            show_boundaries=self.sidebar.switches['show_boundaries'].get(),
            show_arc=self.sidebar.switches['show_arc'].get(),
        )
        n_points = data.get('n_points', N)
        angle_deg = int(i * 360.0 / n_points)
        h, s_0 = update_info_panel(self._info_labels, angle_deg, result['alpha_i'],
                          result['s_i'], data['h'], data['s_0'], self.lang)
        label_h = t("status.label.h", self.lang)
        label_s0 = t("status.label.s0", self.lang)
        self.status_bar.set_stroke(f'{label_h}: {h:.1f} mm')
        self.status_bar.set_s0(f'{label_s0}: {s_0:.2f} mm')
        self.canvas.draw_idle()

    def _on_prev_frame(self):
        """上一帧"""
        if self.sim_data is not None and not self.animating:
            n = len(self.sim_data['s'])
            self.current_frame = max(0, self.current_frame - 1)
            self.toolbar.set_frame(self.current_frame)
            self._draw_single_frame(self.current_frame)

    def _on_next_frame(self):
        """下一帧"""
        if self.sim_data is not None and not self.animating:
            n = len(self.sim_data['s'])
            self.current_frame = min(n - 1, self.current_frame + 1)
            self.toolbar.set_frame(self.current_frame)
            self._draw_single_frame(self.current_frame)

    def _on_first_frame(self):
        """第一帧"""
        if self.sim_data is not None and not self.animating:
            self.current_frame = 0
            self.toolbar.set_frame(0)
            self._draw_single_frame(0)

    def _on_last_frame(self):
        """最后一帧"""
        if self.sim_data is not None and not self.animating:
            n = len(self.sim_data['s'])
            self.current_frame = n - 1
            self.toolbar.set_frame(n - 1)
            self._draw_single_frame(n - 1)

    def _on_close(self):
        """窗口关闭"""
        self._stop_animation()
        self._save_current_config()
        self.destroy()

    def run(self):
        """运行"""
        self.mainloop()


def main():
    """Entry point"""
    app = CamSimulator()
    app.run()


if __name__ == '__main__':
    main()
