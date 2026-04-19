"""CamForge 侧边栏构建器

构建参数面板 UI 和参数读取/设置逻辑。
采用扁平布局 + 分组分隔线风格，与 CamSimulator 的侧边栏一致。
"""

import tkinter as tk
from tkinter import ttk

from i18n import (
    t, get_motion_law_list, get_rotation_list,
    get_offset_dir_list, get_lang_display_list,
    SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP,
)
from ui.constants import (
    DEFAULT_PARAMS, THEME,
)
from ui.params import ParameterModel, generate_random_params


class ToolTip:
    """悬浮提示工具类"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0",
                         relief="solid", borderwidth=1, font=("Microsoft YaHei", 9))
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class SidebarBuilder:
    """构建和管理侧边栏参数面板。

    采用扁平布局（非 LabelFrame），使用分组标题 + 分隔线风格，
    与 CamSimulator 的侧边栏视觉一致。

    Attributes
    ----------
    entries : dict[str, tk.Entry]
        参数名 → 输入框控件。
    combos : dict[str, ttk.Combobox]
        参数名 → 下拉框控件。
    checks : dict[str, tk.BooleanVar]
        复选框名 → BooleanVar。
    """

    def __init__(self, parent_frame, i18n_mgr, theme_mgr, on_validate_entry=None):
        """
        Parameters
        ----------
        parent_frame : tk.Frame
            侧边栏父容器。
        i18n_mgr : I18nManager
            国际化管理器。
        theme_mgr : ThemeManager
            主题管理器。
        on_validate_entry : callable or None
            输入框校验回调 (entry, conv_type) -> None。
        """
        self.frame = parent_frame
        self.i18n_mgr = i18n_mgr
        self.theme_mgr = theme_mgr
        self._on_validate_entry = on_validate_entry

        self.entries = {}       # param_name -> Entry widget
        self.combos = {}        # param_name -> Combobox widget
        self.checks = {}        # param_name -> BooleanVar
        self._combo_callbacks = {}  # param_name -> callback

    def build(self, lang, arc_command=None, grid_command=None):
        """构建侧边栏 UI。

        Parameters
        ----------
        lang : str
            当前语言代码。
        arc_command : callable or None
            压力角弧线复选框命令回调。
        grid_command : callable or None
            网格复选框命令回调。
        """
        tk_font_family = self.i18n_mgr.tk_font_family
        sidebar_bg = THEME['sidebar_bg']
        lbl_font = (tk_font_family, 10)
        ent_font = (tk_font_family, 10)
        lbl_kw = {'font': lbl_font, 'bg': sidebar_bg, 'anchor': 'w'}
        ent_kw = {'font': ent_font, 'width': 14}

        # Logo
        tk.Label(self.frame, text="CamForge", font=(tk_font_family, 16, 'bold'),
                 fg=THEME['logo_fg'], bg=sidebar_bg, anchor='w').pack(fill=tk.X, padx=16, pady=(16, 20))

        # ---- 语言选择组 ----
        self._sidebar_group(self.frame, t("sidebar.group.language", lang), i18n_key="sidebar.group.language")
        self.combos['lang'] = ttk.Combobox(self.frame, values=get_lang_display_list(), state='readonly', width=14)
        self.combos['lang'].current(SUPPORTED_LANGS.index(DEFAULT_LANG))
        self.combos['lang'].pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 主题选择组 ----
        self._sidebar_group(self.frame, t("sidebar.group.theme", lang), i18n_key="sidebar.group.theme")
        theme_values = [t("theme.light", lang), t("theme.dark", lang)]
        self.combos['theme'] = ttk.Combobox(self.frame, values=theme_values, state='readonly', width=14)
        self.combos['theme'].current(0)
        self.combos['theme'].pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 快速预设组 ----
        self._sidebar_group(self.frame, t("sidebar.group.quick_preset", lang), i18n_key="sidebar.group.quick_preset")
        quick_preset_values = [
            t("toolbar.quick_preset.default", lang),
            t("toolbar.quick_preset.small_cam", lang),
            t("toolbar.quick_preset.large_cam", lang),
            t("toolbar.quick_preset.high_speed", lang),
            t("toolbar.quick_preset.roller", lang),
        ]
        self.combos['quick_preset'] = ttk.Combobox(self.frame, values=quick_preset_values, state='readonly', width=14)
        self.combos['quick_preset'].current(0)
        self.combos['quick_preset'].pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 运动参数组 ----
        self._sidebar_group(self.frame, t("sidebar.group.motion", lang), i18n_key="sidebar.group.motion")

        self._add_entry(self.frame, 'delta_0', t("sidebar.label.delta_0", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.delta_0",
                        default=str(DEFAULT_PARAMS['delta_0']), conv_type=float,
                        tooltip=t("tooltip.delta_0", lang))
        self._add_entry(self.frame, 'delta_01', t("sidebar.label.delta_01", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.delta_01",
                        default=str(DEFAULT_PARAMS['delta_01']), conv_type=float,
                        tooltip=t("tooltip.delta_01", lang))
        self._add_entry(self.frame, 'delta_ret', t("sidebar.label.delta_ret", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.delta_ret",
                        default=str(DEFAULT_PARAMS['delta_ret']), conv_type=float,
                        tooltip=t("tooltip.delta_ret", lang))
        self._add_entry(self.frame, 'delta_02', t("sidebar.label.delta_02", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.delta_02",
                        default=str(DEFAULT_PARAMS['delta_02']), conv_type=float,
                        tooltip=t("tooltip.delta_02", lang))
        self._add_entry(self.frame, 'h', t("sidebar.label.h", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.h",
                        default=str(DEFAULT_PARAMS['h']), conv_type=float,
                        tooltip=t("tooltip.h", lang))
        self._add_entry(self.frame, 'omega', t("sidebar.label.omega", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.omega",
                        default=str(DEFAULT_PARAMS['omega']), conv_type=float,
                        tooltip=t("tooltip.omega", lang))

        # ---- 几何参数组 ----
        self._sidebar_group(self.frame, t("sidebar.group.geometry", lang), i18n_key="sidebar.group.geometry")

        self._add_entry(self.frame, 'r_0', t("sidebar.label.r_0", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.r_0",
                        default=str(DEFAULT_PARAMS['r_0']), conv_type=float,
                        tooltip=t("tooltip.r_0", lang))
        self._add_entry(self.frame, 'e', t("sidebar.label.e", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.e",
                        default=str(DEFAULT_PARAMS['e']), conv_type=float,
                        tooltip=t("tooltip.e", lang))
        self._add_entry(self.frame, 'r_r', t("sidebar.label.r_r", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.r_r",
                        default=str(DEFAULT_PARAMS['r_r']), conv_type=float,
                        tooltip=t("tooltip.r_r", lang))
        self._add_entry(self.frame, 'alpha_threshold', t("sidebar.label.alpha_threshold", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.alpha_threshold",
                        default=str(DEFAULT_PARAMS['alpha_threshold']), conv_type=float,
                        tooltip=t("tooltip.alpha_threshold", lang))
        self._add_entry(self.frame, 'n_points', t("sidebar.label.n_points", lang),
                        lbl_kw, ent_kw, i18n_key="sidebar.label.n_points",
                        default=str(DEFAULT_PARAMS['n_points']), conv_type=int,
                        tooltip=t("tooltip.n_points", lang))

        # ---- 运动规律组 ----
        self._sidebar_group(self.frame, t("sidebar.group.law", lang), i18n_key="sidebar.group.law")

        motion_laws = get_motion_law_list(lang)
        combo_kw = {'state': 'readonly', 'width': 14}

        self._add_combo(self.frame, 'tc_law', t("sidebar.label.tc_law", lang),
                        motion_laws, combo_kw, i18n_key="sidebar.label.tc_law", default_idx=0)
        self._add_combo(self.frame, 'hc_law', t("sidebar.label.hc_law", lang),
                        motion_laws, combo_kw, i18n_key="sidebar.label.hc_law", default_idx=0)
        self._add_combo(self.frame, 'sn', t("sidebar.label.rotation", lang),
                        get_rotation_list(lang), combo_kw, i18n_key="sidebar.label.rotation", default_idx=0)
        self._add_combo(self.frame, 'pz', t("sidebar.label.offset_dir", lang),
                        get_offset_dir_list(lang), combo_kw, i18n_key="sidebar.label.offset_dir", default_idx=0)

        # ---- 动态显示组（两列布局） ----
        self._sidebar_group(self.frame, t("sidebar.group.display", lang), i18n_key="sidebar.group.display")

        cb_kw = {'font': (tk_font_family, 10), 'anchor': 'w', 'bg': sidebar_bg}

        display_grid = tk.Frame(self.frame, bg=sidebar_bg)
        display_grid.pack(fill=tk.X, padx=16, pady=2)
        display_grid.columnconfigure(0, weight=1)
        display_grid.columnconfigure(1, weight=1)

        self._add_check(display_grid, 'show_tangent', t("sidebar.cb.tangent", lang),
                        cb_kw, row=0, col=0, default=False, i18n_key="sidebar.cb.tangent")
        self._add_check(display_grid, 'show_normal', t("sidebar.cb.normal", lang),
                        cb_kw, row=0, col=1, default=False, i18n_key="sidebar.cb.normal")
        self._add_check(display_grid, 'show_arc', t("sidebar.cb.arc", lang),
                        cb_kw, row=1, col=0, default=False, i18n_key="sidebar.cb.arc",
                        command=arc_command)
        self._add_check(display_grid, 'show_boundaries', t("sidebar.cb.boundaries", lang),
                        cb_kw, row=1, col=1, default=False, i18n_key="sidebar.cb.boundaries")
        self._add_check(display_grid, 'show_base_circle', t("sidebar.cb.base_circle", lang),
                        cb_kw, row=2, col=0, default=False, i18n_key="sidebar.cb.base_circle")
        self._add_check(display_grid, 'show_offset_circle', t("sidebar.cb.offset_circle", lang),
                        cb_kw, row=2, col=1, default=False, i18n_key="sidebar.cb.offset_circle")
        self._add_check(display_grid, 'show_limits', t("sidebar.cb.limits", lang),
                        cb_kw, row=3, col=0, default=False, i18n_key="sidebar.cb.limits")
        self._add_check(display_grid, 'show_grid', t("sidebar.cb.grid", lang),
                        cb_kw, row=3, col=1, default=False, i18n_key="sidebar.cb.grid",
                        command=grid_command)

    # ===================================================================
    # 内部构建辅助
    # ===================================================================

    def _sidebar_group(self, parent, title, i18n_key=None):
        """侧边栏分组标题（扁平风格：标题 + 分隔线）"""
        frame = tk.Frame(parent, bg=THEME['sidebar_bg'])
        frame.pack(fill=tk.X, padx=16, pady=(12, 4))
        lbl = tk.Label(frame, text=title, font=(self.i18n_mgr.tk_font_family, 9),
                 fg=THEME['group_fg'], bg=THEME['sidebar_bg'], anchor='w')
        lbl.pack(fill=tk.X)
        tk.Frame(frame, height=1, bg=THEME['separator']).pack(fill=tk.X, pady=(2, 0))
        self.theme_mgr.register_widget(lbl)
        self.theme_mgr.register_widget(frame)
        if i18n_key:
            self.i18n_mgr.register(i18n_key, lbl, font_size=9)

    def _sidebar_item(self, parent, text, lbl_kw, i18n_key=None):
        """侧边栏参数标签"""
        lbl = tk.Label(parent, text=text, **lbl_kw)
        lbl.pack(fill=tk.X, padx=16, pady=(4, 0))
        self.theme_mgr.register_widget(lbl)
        if i18n_key:
            self.i18n_mgr.register(i18n_key, lbl, font_size=10)

    def _add_entry(self, parent, name, label_text, lbl_kw, ent_kw,
                   i18n_key=None, default='', conv_type=float, tooltip=None):
        """添加一个参数输入框。"""
        self._sidebar_item(parent, label_text, lbl_kw, i18n_key=i18n_key)
        entry = tk.Entry(parent, **ent_kw)
        entry.insert(0, default)
        entry.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.entries[name] = entry
        self.theme_mgr.register_widget(entry)
        if self._on_validate_entry and conv_type:
            entry.bind('<FocusOut>', lambda e, ent=entry, ct=conv_type: self._on_validate_entry(ent, ct))
        # 添加 tooltip
        if tooltip:
            ToolTip(entry, tooltip)

    def _add_combo(self, parent, name, label_text, values, combo_kw,
                   i18n_key=None, default_idx=0):
        """添加一个参数下拉框。"""
        self._sidebar_item(parent, label_text,
                           {'font': (self.i18n_mgr.tk_font_family, 10),
                            'bg': THEME['sidebar_bg'], 'anchor': 'w'},
                           i18n_key=i18n_key)
        combo = ttk.Combobox(parent, values=values, **combo_kw)
        combo.current(default_idx)
        combo.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.combos[name] = combo
        self.theme_mgr.register_widget(combo, 'TCombobox')

    def _add_check(self, parent, name, label_text, cb_kw,
                   row=0, col=0, default=False, i18n_key=None,
                   command=None):
        """添加一个复选框。"""
        var = tk.BooleanVar(value=default)
        cb = tk.Checkbutton(parent, text=label_text, variable=var,
                            command=command, **cb_kw)
        cb.grid(row=row, column=col, sticky='w', pady=1)
        self.checks[name] = var
        self.theme_mgr.register_widget(cb)
        if i18n_key:
            self.i18n_mgr.register(i18n_key, cb, font_size=10)

    # ===================================================================
    # 参数读取与设置
    # ===================================================================

    def read_params(self, lang):
        """从 UI 读取参数值，返回 ParameterModel。

        Parameters
        ----------
        lang : str
            当前语言代码（用于错误消息和角度名称）。

        Returns
        -------
        ParameterModel or None
            参数模型，如果参数无效返回 None。
            无效时通过 status_var 设置错误状态。
        """
        try:
            raw_angles = {
                'delta_0': float(self.entries['delta_0'].get()),
                'delta_01': float(self.entries['delta_01'].get()),
                'delta_ret': float(self.entries['delta_ret'].get()),
                'delta_02': float(self.entries['delta_02'].get()),
            }
            vals = {
                'delta_0': int(raw_angles['delta_0']),
                'delta_01': int(raw_angles['delta_01']),
                'delta_ret': int(raw_angles['delta_ret']),
                'delta_02': int(raw_angles['delta_02']),
                'h': float(self.entries['h'].get()),
                'r_0': float(self.entries['r_0'].get()),
                'e': float(self.entries['e'].get()),
                'omega': float(self.entries['omega'].get()),
                'r_r': float(self.entries['r_r'].get()),
                'n_points': int(float(self.entries['n_points'].get())),
                'alpha_threshold': float(self.entries['alpha_threshold'].get()),
            }
        except ValueError:
            return None, t("status.incomplete_params", lang)

        # 检查角度浮点截断
        truncation_warnings = []
        angle_names = {
            'delta_0': t("sidebar.label.delta_0", lang),
            'delta_01': t("sidebar.label.delta_01", lang),
            'delta_ret': t("sidebar.label.delta_ret", lang),
            'delta_02': t("sidebar.label.delta_02", lang),
        }
        for key, raw_val in raw_angles.items():
            int_val = int(raw_val)
            if abs(raw_val - int_val) > 1e-9:
                truncation_warnings.append(
                    t("status.angle_truncated", lang, name=angle_names[key], raw=raw_val, rounded=int_val)
                )

        # 读取下拉菜单
        vals['tc_law'] = self.combos['tc_law'].current() + 1
        vals['hc_law'] = self.combos['hc_law'].current() + 1
        vals['sn'] = 1 if self.combos['sn'].current() == 0 else -1
        vals['pz'] = 1 if self.combos['pz'].current() == 0 else -1
        vals['e'] = abs(vals['e'])  # 偏距取正值，方向由 pz 控制

        # 构建 ParameterModel 并校验
        model = ParameterModel(**vals)
        ok, err = model.validate()
        if not ok:
            if isinstance(err, tuple):
                key, name_key = err
                name = t(name_key, lang)
                return None, t(key, lang, name=name)
            else:
                return None, t(err, lang)

        return model, truncation_warnings

    def clear_params(self):
        """将所有参数重置为默认值。"""
        for name, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(DEFAULT_PARAMS.get(name, '')))
        self.combos['tc_law'].current(0)
        self.combos['hc_law'].current(0)
        self.combos['sn'].current(0)
        self.combos['pz'].current(0)

    def set_params(self, params_dict):
        """从字典设置参数值。"""
        for name, entry in self.entries.items():
            if name in params_dict:
                entry.delete(0, tk.END)
                entry.insert(0, str(params_dict[name]))
        for name in ['tc_law', 'hc_law', 'sn', 'pz']:
            if name in params_dict and name in self.combos:
                self.combos[name].current(params_dict[name])

    def set_random_params(self):
        """设置随机凸轮参数。"""
        params = generate_random_params()
        for name in ['delta_0', 'delta_01', 'delta_ret', 'delta_02',
                      'h', 'r_0', 'e', 'omega']:
            if name in self.entries:
                self.entries[name].delete(0, tk.END)
                self.entries[name].insert(0, str(params[name]))

        self.combos['tc_law'].current(params['tc_law'] - 1)
        self.combos['hc_law'].current(params['hc_law'] - 1)
        self.combos['sn'].current(0 if params['sn'] == 1 else 1)
        self.combos['pz'].current(0 if params['pz'] == 1 else 1)

        # 新参数保持默认值
        for name in ['r_r', 'n_points', 'alpha_threshold']:
            if name in self.entries:
                self.entries[name].delete(0, tk.END)
                self.entries[name].insert(0, str(DEFAULT_PARAMS.get(name, '')))

    def get_check(self, name):
        """获取复选框变量的值。"""
        return self.checks[name].get()

    def get_preset_data(self):
        """获取当前参数值用于预设保存。"""
        preset = {}
        for name, entry in self.entries.items():
            preset[name] = entry.get()
        for name in ['tc_law', 'hc_law', 'sn', 'pz']:
            if name in self.combos:
                preset[name] = self.combos[name].current()
        return preset

    def load_preset_data(self, preset):
        """从预设字典加载参数值。"""
        for name, entry in self.entries.items():
            if name in preset:
                entry.delete(0, tk.END)
                entry.insert(0, str(preset[name]))
        for name in ['tc_law', 'hc_law', 'sn', 'pz']:
            if name in preset and name in self.combos:
                idx = int(preset[name])
                self.combos[name].current(idx)

    def update_combo_values(self, lang):
        """更新所有下拉列表的值（语言切换后）。"""
        if 'tc_law' in self.combos:
            idx = self.combos['tc_law'].current()
            self.combos['tc_law'].config(values=get_motion_law_list(lang))
            self.combos['tc_law'].current(idx)
        if 'hc_law' in self.combos:
            idx = self.combos['hc_law'].current()
            self.combos['hc_law'].config(values=get_motion_law_list(lang))
            self.combos['hc_law'].current(idx)
        if 'sn' in self.combos:
            idx = self.combos['sn'].current()
            self.combos['sn'].config(values=get_rotation_list(lang))
            self.combos['sn'].current(idx)
        if 'pz' in self.combos:
            idx = self.combos['pz'].current()
            self.combos['pz'].config(values=get_offset_dir_list(lang))
            self.combos['pz'].current(idx)
        if 'lang' in self.combos:
            # 语言列表不变，只更新显示
            pass
        if 'theme' in self.combos:
            # 主题列表更新
            idx = self.combos['theme'].current()
            self.combos['theme'].config(values=[t("theme.light", lang), t("theme.dark", lang)])
            self.combos['theme'].current(idx)
