"""CamForge 国际化管理器

管理可翻译控件的注册和语言切换。
"""

from i18n import (
    t, SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP,
    LANG_DISPLAY_NAMES, get_motion_law_list, get_rotation_list,
    get_offset_dir_list, get_lang_display_list, detect_mpl_fonts,
)
import tkinter as tk
from tkinter import ttk


class I18nManager:
    """管理语言切换和可翻译控件注册。"""

    def __init__(self, default_lang=None):
        self.lang = default_lang or DEFAULT_LANG
        self._tk_font_family = FONT_MAP[self.lang]["tk"]
        self._translatable = {}  # key -> (widget, font_size)

    @property
    def tk_font_family(self):
        return self._tk_font_family

    def register(self, key, widget, font_size=None):
        """注册一个控件用于语言切换更新。

        Parameters
        ----------
        key : str
            i18n 翻译键。
        widget : tk.Widget
            需要更新文本的控件。
        font_size : int or None
            如果提供，语言切换时同时更新字体。
        """
        self._translatable[key] = (widget, font_size)

    def law_name(self, law_id):
        """获取运动规律名称（当前语言）。"""
        return t(f"law.{law_id}", self.lang)

    def apply_language(self, lang, combo_widgets=None):
        """更新所有已注册控件为指定语言。

        Parameters
        ----------
        lang : str
            目标语言代码。
        combo_widgets : dict or None
            需要更新下拉列表值的控件，键: 'tc', 'hc', 'sn', 'pz'，
            值为 ttk.Combobox 实例。
        """
        self.lang = lang
        self._tk_font_family = FONT_MAP[lang]["tk"]

        for key, (widget, font_size) in self._translatable.items():
            text = t(key, lang)
            try:
                widget.config(text=text)
            except tk.TclError:
                pass
            if font_size is not None:
                try:
                    widget.config(font=(self._tk_font_family, font_size))
                except tk.TclError:
                    pass

        # 更新下拉列表值（保留当前索引）
        if combo_widgets:
            if 'tc' in combo_widgets:
                tc_idx = combo_widgets['tc'].current()
                combo_widgets['tc'].config(values=get_motion_law_list(lang))
                combo_widgets['tc'].current(tc_idx)
            if 'hc' in combo_widgets:
                hc_idx = combo_widgets['hc'].current()
                combo_widgets['hc'].config(values=get_motion_law_list(lang))
                combo_widgets['hc'].current(hc_idx)
            if 'sn' in combo_widgets:
                sn_idx = combo_widgets['sn'].current()
                combo_widgets['sn'].config(values=get_rotation_list(lang))
                combo_widgets['sn'].current(sn_idx)
            if 'pz' in combo_widgets:
                pz_idx = combo_widgets['pz'].current()
                combo_widgets['pz'].config(values=get_offset_dir_list(lang))
                combo_widgets['pz'].current(pz_idx)

    @staticmethod
    def update_mpl_fonts(lang):
        """更新 matplotlib 字体配置。"""
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = detect_mpl_fonts(lang)
        plt.rcParams['axes.unicode_minus'] = False
