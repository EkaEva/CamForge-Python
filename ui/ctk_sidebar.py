"""CamForge CustomTkinter 侧边栏模块

使用 CustomTkinter 实现现代化的侧边栏：
- 卡片式分组布局
- 拨动开关替代复选框
- iOS/Apple 设计风格
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional, Dict, Any

from ui.ctk_constants import (
    UI_PADDING, SIDEBAR_WIDTH, COLORS_LIGHT, COLORS_DARK,
    FONT_SIZE_TITLE, FONT_SIZE_SECTION, FONT_SIZE_LABEL,
    create_ctk_font, get_colors,
)
from ui.ctk_components import (
    CardGroup, EntryRow, SwitchRow, ComboRow,
)
from ui.constants import DEFAULT_PARAMS
from i18n import (
    t, get_motion_law_list, get_rotation_list,
    get_offset_dir_list, get_lang_display_list,
    SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP,
)


class CTkSidebar:
    """CustomTkinter 侧边栏构建器

    使用卡片式布局组织参数输入控件。

    Attributes
    ----------
    frame : CTkScrollableFrame
        侧边栏容器（可滚动）
    entries : dict
        参数名 -> EntryRow 映射
    switches : dict
        开关名 -> SwitchRow 映射
    combos : dict
        下拉框名 -> ComboRow 映射
    """

    def __init__(self, parent_frame, i18n_mgr, on_validate_entry: Optional[Callable] = None):
        """
        Parameters
        ----------
        parent_frame : widget
            父容器
        i18n_mgr : I18nManager
            国际化管理器
        on_validate_entry : callable, optional
            输入框校验回调
        """
        # 直接使用父容器（父容器已经是 CTkScrollableFrame）
        self.frame = parent_frame

        self.i18n_mgr = i18n_mgr
        self._on_validate_entry = on_validate_entry

        self.entries: Dict[str, EntryRow] = {}
        self.switches: Dict[str, SwitchRow] = {}
        self.combos: Dict[str, ComboRow] = {}
        self._cards: list = []

    def build(self, lang: str, arc_command: Optional[Callable] = None,
              grid_command: Optional[Callable] = None,
              lang_command: Optional[Callable] = None,
              theme_command: Optional[Callable] = None,
              preset_command: Optional[Callable] = None):
        """构建侧边栏 UI

        Parameters
        ----------
        lang : str
            当前语言代码
        arc_command : callable, optional
            压力角弧线开关回调
        grid_command : callable, optional
            网格线开关回调
        lang_command : callable, optional
            语言切换回调
        theme_command : callable, optional
            主题切换回调
        preset_command : callable, optional
            快速预设切换回调
        """
        # 清除现有内容
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.entries.clear()
        self.switches.clear()
        self.combos.clear()
        self._cards.clear()

        # Logo 标题
        self._create_logo()

        # 卡片 1：常用设置
        self._build_general_card(lang, lang_command, theme_command, preset_command)

        # 卡片 2：下载选项
        self._build_download_card(lang)

        # 卡片 3：运动参数
        self._build_motion_card(lang)

        # 卡片 4：几何参数
        self._build_geometry_card(lang)

        # 卡片 5：运动规律
        self._build_law_card(lang)

        # 卡片 6：显示选项
        self._build_display_card(lang, arc_command, grid_command)

    def _create_logo(self):
        """创建 Logo 标题"""
        logo_label = ctk.CTkLabel(
            self.frame,
            text="CamForge",
            font=create_ctk_font(size=FONT_SIZE_TITLE, weight="bold"),
            text_color=COLORS_LIGHT['accent'],
            anchor='w',
        )
        logo_label.pack(fill='x', padx=UI_PADDING, pady=(20, 20), anchor='w')

    def _build_general_card(self, lang: str, lang_command=None, theme_command=None, preset_command=None):
        """构建通用设置卡片"""
        card = CardGroup(self.frame, title=t("sidebar.group.common", lang))

        # 语言选择
        lang_values = get_lang_display_list()
        lang_row = ComboRow(
            card, t("sidebar.group.language", lang),
            values=lang_values,
            default_index=SUPPORTED_LANGS.index(DEFAULT_LANG),
            command=lang_command,
        )
        lang_row.pack_in_card()
        self.combos['lang'] = lang_row

        # 主题选择
        theme_values = [
            t("theme.light", lang),
            t("theme.dark", lang),
        ]
        theme_row = ComboRow(
            card, t("sidebar.group.theme", lang),
            values=theme_values,
            default_index=0,
            command=theme_command,
        )
        theme_row.pack_in_card()
        self.combos['theme'] = theme_row

        # 快速预设
        preset_values = [
            t("toolbar.quick_preset.default", lang),
            t("toolbar.quick_preset.small_cam", lang),
            t("toolbar.quick_preset.large_cam", lang),
            t("toolbar.quick_preset.high_speed", lang),
            t("toolbar.quick_preset.roller", lang),
        ]
        preset_row = ComboRow(
            card, t("sidebar.group.quick_preset", lang),
            values=preset_values,
            default_index=0,
            command=preset_command,
        )
        preset_row.pack_in_card()
        self.combos['quick_preset'] = preset_row

        card.pack_with_title()
        self._cards.append(card)

    def _build_download_card(self, lang: str):
        """构建下载选项卡片 - 四行两列布局"""
        import tkinter as tk
        card = CardGroup(self.frame, title=t("sidebar.group.download", lang))

        self.download_checkboxes = {}

        import customtkinter as ctk
        from ui.ctk_constants import create_ctk_font, FONT_SIZE_LABEL

        # 四行两列布局（按用户要求的顺序）
        items = [
            ('dl_motion', 'toolbar.cb.dl_motion', True),
            ('dl_geom', 'toolbar.cb.dl_geom', True),
            ('dl_anim', 'toolbar.cb.dl_anim', True),
            ('dl_profile', 'toolbar.cb.dl_profile', True),
            ('dl_csv', 'toolbar.cb.dl_csv', True),
            ('dl_svg', 'toolbar.cb.dl_svg', True),
            ('dl_dxf', 'toolbar.cb.dl_dxf', True),
            ('dl_excel', 'toolbar.cb.dl_excel', True),
        ]

        for i, (name, key, default) in enumerate(items):
            row = i // 2  # 0, 1, 2, 3
            col = i % 2   # 0, 1

            if col == 0:
                # 创建新行
                row_frame = tk.Frame(card, bg='white')
                row_frame.pack(fill='x', padx=10, pady=(6 if row == 0 else 2, 2))

            self.download_checkboxes[name] = tk.BooleanVar(value=default)
            cb = ctk.CTkCheckBox(
                row_frame,
                text=t(key, lang),
                variable=self.download_checkboxes[name],
                font=create_ctk_font(size=FONT_SIZE_LABEL - 2),
                checkbox_width=16,
                checkbox_height=16,
            )
            cb.pack(side='left', padx=(0, 10))

        card.pack_with_title()
        self._cards.append(card)

    def _build_motion_card(self, lang: str):
        """构建运动参数卡片"""
        card = CardGroup(self.frame, title=t("sidebar.group.motion", lang))

        # 推程运动角
        self._add_entry_to_card(
            card, 'delta_0',
            t("sidebar.label.delta_0", lang),
            str(DEFAULT_PARAMS['delta_0']),
            tooltip=t("tooltip.delta_0", lang),
        )

        # 远休止角
        self._add_entry_to_card(
            card, 'delta_01',
            t("sidebar.label.delta_01", lang),
            str(DEFAULT_PARAMS['delta_01']),
            tooltip=t("tooltip.delta_01", lang),
        )

        # 回程运动角
        self._add_entry_to_card(
            card, 'delta_ret',
            t("sidebar.label.delta_ret", lang),
            str(DEFAULT_PARAMS['delta_ret']),
            tooltip=t("tooltip.delta_ret", lang),
        )

        # 近休止角
        self._add_entry_to_card(
            card, 'delta_02',
            t("sidebar.label.delta_02", lang),
            str(DEFAULT_PARAMS['delta_02']),
            tooltip=t("tooltip.delta_02", lang),
        )

        # 推杆最大位移
        self._add_entry_to_card(
            card, 'h',
            t("sidebar.label.h", lang),
            str(DEFAULT_PARAMS['h']),
            tooltip=t("tooltip.h", lang),
        )

        # 凸轮角速度
        self._add_entry_to_card(
            card, 'omega',
            t("sidebar.label.omega", lang),
            str(DEFAULT_PARAMS['omega']),
            tooltip=t("tooltip.omega", lang),
        )

        card.pack_with_title()
        self._cards.append(card)

    def _build_geometry_card(self, lang: str):
        """构建几何参数卡片"""
        card = CardGroup(self.frame, title=t("sidebar.group.geometry", lang))

        # 基圆半径
        self._add_entry_to_card(
            card, 'r_0',
            t("sidebar.label.r_0", lang),
            str(DEFAULT_PARAMS['r_0']),
            tooltip=t("tooltip.r_0", lang),
        )

        # 偏距
        self._add_entry_to_card(
            card, 'e',
            t("sidebar.label.e", lang),
            str(DEFAULT_PARAMS['e']),
            tooltip=t("tooltip.e", lang),
        )

        # 滚子半径
        self._add_entry_to_card(
            card, 'r_r',
            t("sidebar.label.r_r", lang),
            str(DEFAULT_PARAMS['r_r']),
            tooltip=t("tooltip.r_r", lang),
        )

        # 压力角阈值
        self._add_entry_to_card(
            card, 'alpha_threshold',
            t("sidebar.label.alpha_threshold", lang),
            str(DEFAULT_PARAMS['alpha_threshold']),
            tooltip=t("tooltip.alpha_threshold", lang),
        )

        # 离散点数
        self._add_entry_to_card(
            card, 'n_points',
            t("sidebar.label.n_points", lang),
            str(DEFAULT_PARAMS['n_points']),
            tooltip=t("tooltip.n_points", lang),
        )

        card.pack_with_title()
        self._cards.append(card)

    def _build_law_card(self, lang: str):
        """构建运动规律卡片"""
        card = CardGroup(self.frame, title=t("sidebar.group.law", lang))

        motion_laws = get_motion_law_list(lang)

        # 推程规律
        tc_row = ComboRow(
            card, t("sidebar.label.tc_law", lang),
            values=motion_laws,
            default_index=0,
        )
        tc_row.pack_in_card()
        self.combos['tc_law'] = tc_row

        # 回程规律
        hc_row = ComboRow(
            card, t("sidebar.label.hc_law", lang),
            values=motion_laws,
            default_index=0,
        )
        hc_row.pack_in_card()
        self.combos['hc_law'] = hc_row

        # 旋向
        sn_row = ComboRow(
            card, t("sidebar.label.rotation", lang),
            values=get_rotation_list(lang),
            default_index=0,
        )
        sn_row.pack_in_card()
        self.combos['sn'] = sn_row

        # 偏距方向
        pz_row = ComboRow(
            card, t("sidebar.label.offset_dir", lang),
            values=get_offset_dir_list(lang),
            default_index=0,
        )
        pz_row.pack_in_card()
        self.combos['pz'] = pz_row

        card.pack_with_title()
        self._cards.append(card)

    def _build_display_card(self, lang: str, arc_command: Optional[Callable],
                            grid_command: Optional[Callable]):
        """构建显示选项卡片"""
        card = CardGroup(self.frame, title=t("sidebar.group.display", lang))

        # 切线
        tangent_row = SwitchRow(
            card, t("sidebar.cb.tangent", lang),
            default=False,
        )
        tangent_row.pack_in_card()
        self.switches['show_tangent'] = tangent_row

        # 法线
        normal_row = SwitchRow(
            card, t("sidebar.cb.normal", lang),
            default=False,
        )
        normal_row.pack_in_card()
        self.switches['show_normal'] = normal_row

        # 压力角弧线
        arc_row = SwitchRow(
            card, t("sidebar.cb.arc", lang),
            default=False,
            command=arc_command,
        )
        arc_row.pack_in_card()
        self.switches['show_arc'] = arc_row

        # 角度分界线
        boundaries_row = SwitchRow(
            card, t("sidebar.cb.boundaries", lang),
            default=False,
        )
        boundaries_row.pack_in_card()
        self.switches['show_boundaries'] = boundaries_row

        # 基圆
        base_row = SwitchRow(
            card, t("sidebar.cb.base_circle", lang),
            default=False,
        )
        base_row.pack_in_card()
        self.switches['show_base_circle'] = base_row

        # 偏距圆
        offset_row = SwitchRow(
            card, t("sidebar.cb.offset_circle", lang),
            default=False,
        )
        offset_row.pack_in_card()
        self.switches['show_offset_circle'] = offset_row

        # 推杆上下限
        limits_row = SwitchRow(
            card, t("sidebar.cb.limits", lang),
            default=False,
        )
        limits_row.pack_in_card()
        self.switches['show_limits'] = limits_row

        # 网格线
        grid_row = SwitchRow(
            card, t("sidebar.cb.grid", lang),
            default=False,
            command=grid_command,
        )
        grid_row.pack_in_card()
        self.switches['show_grid'] = grid_row

        card.pack_with_title()
        self._cards.append(card)

    def _add_entry_to_card(self, card: CardGroup, name: str, label: str,
                           default: str, tooltip: Optional[str] = None):
        """向卡片添加输入行"""
        entry_row = EntryRow(
            card,
            label_text=label,
            default_value=default,
            tooltip=tooltip,
        )
        entry_row.pack_in_card()
        self.entries[name] = entry_row

    # ===================================================================
    # 参数读取与设置
    # ===================================================================

    def read_params(self, lang: str):
        """从 UI 读取参数值，返回 ParameterModel"""
        from ui.params import ParameterModel

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
        vals['e'] = abs(vals['e'])

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
        """将所有参数重置为默认值"""
        for name, entry_row in self.entries.items():
            entry_row.set(str(DEFAULT_PARAMS.get(name, '')))
        self.combos['tc_law'].set_index(0)
        self.combos['hc_law'].set_index(0)
        self.combos['sn'].set_index(0)
        self.combos['pz'].set_index(0)

    def set_params(self, params_dict: dict):
        """从字典设置参数值"""
        for name, entry_row in self.entries.items():
            if name in params_dict:
                entry_row.set(str(params_dict[name]))
        for name in ['tc_law', 'hc_law', 'sn', 'pz']:
            if name in params_dict and name in self.combos:
                self.combos[name].set_index(params_dict[name])

    def set_random_params(self):
        """设置随机凸轮参数"""
        from ui.params import generate_random_params
        params = generate_random_params()

        for name in ['delta_0', 'delta_01', 'delta_ret', 'delta_02',
                     'h', 'r_0', 'e', 'omega']:
            if name in self.entries:
                self.entries[name].set(str(params[name]))

        self.combos['tc_law'].set_index(params['tc_law'] - 1)
        self.combos['hc_law'].set_index(params['hc_law'] - 1)
        self.combos['sn'].set_index(0 if params['sn'] == 1 else 1)
        self.combos['pz'].set_index(0 if params['pz'] == 1 else 1)

        for name in ['r_r', 'n_points', 'alpha_threshold']:
            if name in self.entries:
                self.entries[name].set(str(DEFAULT_PARAMS.get(name, '')))

    def get_check(self, name: str) -> bool:
        """获取开关状态"""
        return self.switches[name].get()

    def get_preset_data(self) -> dict:
        """获取当前参数值用于预设保存"""
        preset = {}
        for name, entry_row in self.entries.items():
            preset[name] = entry_row.get()
        for name in ['tc_law', 'hc_law', 'sn', 'pz']:
            if name in self.combos:
                preset[name] = self.combos[name].current()
        return preset

    def load_preset_data(self, preset: dict):
        """从预设字典加载参数值"""
        for name, entry_row in self.entries.items():
            if name in preset:
                entry_row.set(str(preset[name]))
        for name in ['tc_law', 'hc_law', 'sn', 'pz']:
            if name in preset and name in self.combos:
                self.combos[name].set_index(int(preset[name]))

    def update_combo_values(self, lang: str):
        """更新所有下拉列表的值（语言切换后）"""
        if 'tc_law' in self.combos:
            idx = self.combos['tc_law'].current()
            self.combos['tc_law'].combo.configure(values=get_motion_law_list(lang))
            self.combos['tc_law'].set_index(idx)
        if 'hc_law' in self.combos:
            idx = self.combos['hc_law'].current()
            self.combos['hc_law'].combo.configure(values=get_motion_law_list(lang))
            self.combos['hc_law'].set_index(idx)
        if 'sn' in self.combos:
            idx = self.combos['sn'].current()
            self.combos['sn'].combo.configure(values=get_rotation_list(lang))
            self.combos['sn'].set_index(idx)
        if 'pz' in self.combos:
            idx = self.combos['pz'].current()
            self.combos['pz'].combo.configure(values=get_offset_dir_list(lang))
            self.combos['pz'].set_index(idx)
        if 'theme' in self.combos:
            idx = self.combos['theme'].current()
            self.combos['theme'].combo.configure(values=[t("theme.light", lang), t("theme.dark", lang)])
            self.combos['theme'].set_index(idx)
